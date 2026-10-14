"""JSON persistence. Never silently discards data it cannot understand."""
import json
import os
import re

from .tickets import (
    CATEGORIES, PRIORITIES, STATUSES, TICKET_FIELDS, URGENCIES, CampusFlowError, calculate_priority,
)
from .notes import next_note_id

DEFAULT_PATH = os.path.join("data", "tickets.json")
_ID = re.compile(r"^T\d+$")


class StorageError(CampusFlowError):
    """The data file cannot be read or is not valid CampusFlow data."""


def validate_tickets(data):
    if not isinstance(data, list):
        raise StorageError("Ticket file must contain a JSON list of tickets.")
    seen = set()
    for index, ticket in enumerate(data, start=1):
        where = f"Ticket #{index} in file"
        if not isinstance(ticket, dict):
            raise StorageError(f"{where} is not an object.")
        legacy_fields = tuple(f for f in TICKET_FIELDS if f != "notes")
        missing = [f for f in legacy_fields if f not in ticket]
        if missing:
            raise StorageError(f"{where} is missing fields: {', '.join(missing)}.")
        if not isinstance(ticket["id"], str) or not _ID.match(ticket["id"]):
            raise StorageError(f"{where} has an invalid id.")
        if ticket["id"] in seen:
            raise StorageError(f"Duplicate ticket id {ticket['id']} in file.")
        seen.add(ticket["id"])
        # Upgrade old records in memory; their original fields are preserved.
        if "notes" not in ticket:
            ticket["notes"] = []
        users = ticket["affected_users"]
        checks = [
            (isinstance(ticket["title"], str) and ticket["title"].strip(), "title"),
            (ticket["category"] in CATEGORIES, "category"),
            (ticket["urgency"] in URGENCIES, "urgency"),
            (isinstance(users, int) and not isinstance(users, bool) and users >= 1,
             "affected_users"),
            (ticket["priority"] in PRIORITIES, "priority"),
            (ticket["status"] in STATUSES, "status"),
            (ticket["assigned_to"] is None
             or (isinstance(ticket["assigned_to"], str) and ticket["assigned_to"].strip()),
             "assigned_to"),
        ]
        for ok, field in checks:
            if not ok:
                raise StorageError(f"{where} ({ticket['id']}) has an invalid {field}.")
        if ticket["priority"] != calculate_priority(ticket["urgency"], users):
            raise StorageError(f"{where} ({ticket['id']}) has a priority inconsistent with urgency/users.")
        try:
            next_note_id(ticket)
        except ValueError as exc:
            raise StorageError(f"{where} ({ticket['id']}) has invalid notes: {exc}") from exc


def load_tickets(path=DEFAULT_PATH):
    """Missing file -> fresh start ([]). Bad file -> StorageError."""
    if not os.path.exists(path):
        return []
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise StorageError(
            f"{path} is not valid JSON (line {exc.lineno}, column {exc.colno}). "
            "Fix or move the file; it has NOT been overwritten."
        ) from exc
    except OSError as exc:
        raise StorageError(f"Could not read {path}: {exc}") from exc
    validate_tickets(data)
    return data


def save_tickets(tickets, path=DEFAULT_PATH):
    """Write atomically so a crash cannot leave a half-written file."""
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    temp_path = path + ".tmp"
    try:
        with open(temp_path, "w", encoding="utf-8") as handle:
            json.dump(tickets, handle, indent=2)
        os.replace(temp_path, path)
    except OSError as exc:
        raise StorageError(f"Could not save to {path}: {exc}") from exc
