"""Ticket creation, validation and the priority engine (Engineer A).

Design: the ticket collection is a plain ``list`` of ``dict`` records that is
passed into every function. Functions validate FIRST and mutate LAST, so an
invalid request can never leave a half-updated ticket behind. Invalid input is
signalled with exceptions that all derive from ``CampusFlowError``.
"""
import re

CATEGORIES = ("Network", "Hardware", "Software", "Other")
URGENCIES = ("low", "medium", "high")
PRIORITIES = ("critical", "high", "medium", "low")  # queue order
STATUSES = ("open", "in_progress", "resolved")
TICKET_FIELDS = (
    "id", "title", "category", "urgency",
    "affected_users", "priority", "status", "assigned_to", "notes",
)
ID_PATTERN = re.compile(r"^T(\d+)$")


class CampusFlowError(ValueError):
    """Base class for every expected, user-facing error."""


class ValidationError(CampusFlowError):
    """Input that does not satisfy the ticket rules."""


class TicketNotFoundError(CampusFlowError):
    """No ticket exists with the requested ID."""


class WorkflowError(CampusFlowError):
    """A status change or modification that the workflow forbids."""


# ---------------------------------------------------------------- validation
def normalize_title(title):
    if not isinstance(title, str) or not title.strip():
        raise ValidationError("Title must not be blank.")
    return title.strip()


def normalize_category(category):
    if isinstance(category, str):
        lookup = {c.lower(): c for c in CATEGORIES}
        found = lookup.get(category.strip().lower())
        if found:
            return found
    raise ValidationError(
        f"Invalid category {category!r}. Allowed: {', '.join(CATEGORIES)}."
    )


def normalize_urgency(urgency):
    if isinstance(urgency, str) and urgency.strip().lower() in URGENCIES:
        return urgency.strip().lower()
    raise ValidationError(
        f"Invalid urgency {urgency!r}. Allowed: {', '.join(URGENCIES)}."
    )


def parse_affected_users(value):
    """Return a positive int. Rejects 0, negatives, decimals, text, bools."""
    message = "affected_users must be a positive whole number (1 or more)."
    if isinstance(value, bool):
        raise ValidationError(message)
    if isinstance(value, int):
        number = value
    elif isinstance(value, str):
        text = value.strip()
        if not (text.isascii() and text.isdigit()):
            raise ValidationError(message)
        number = int(text)
    else:
        raise ValidationError(message)
    if number < 1:
        raise ValidationError(message)
    return number


# ------------------------------------------------------------ priority engine
def calculate_priority(urgency, affected_users):
    """Apply the four rules in order; the first match wins."""
    urgency = normalize_urgency(urgency)
    affected_users = parse_affected_users(affected_users)
    if urgency == "high" and affected_users >= 10:
        return "critical"
    if urgency == "high" or affected_users >= 10:
        return "high"
    if urgency == "medium" or affected_users >= 3:
        return "medium"
    return "low"


# ------------------------------------------------------------------- tickets
def ticket_number(ticket_id):
    match = ID_PATTERN.match(ticket_id)
    return int(match.group(1)) if match else 0


def next_ticket_id(tickets):
    """Highest existing number + 1, so IDs stay unique after reload."""
    highest = max((ticket_number(t["id"]) for t in tickets), default=0)
    return f"T{highest + 1:03d}"


def create_ticket(tickets, title, category, urgency, affected_users):
    """Validate, compute priority, assign ID, append and return the ticket."""
    title = normalize_title(title)
    category = normalize_category(category)
    urgency = normalize_urgency(urgency)
    affected_users = parse_affected_users(affected_users)
    ticket = {
        "id": next_ticket_id(tickets),
        "title": title,
        "category": category,
        "urgency": urgency,
        "affected_users": affected_users,
        "priority": calculate_priority(urgency, affected_users),
        "status": "open",
        "assigned_to": None,
        "notes": [],
    }
    tickets.append(ticket)
    return ticket


def get_ticket(tickets, ticket_id):
    key = ticket_id.strip().upper() if isinstance(ticket_id, str) else ""
    for ticket in tickets:
        if ticket["id"] == key:
            return ticket
    raise TicketNotFoundError(f"No ticket with ID {ticket_id!r}.")


def assign_ticket(tickets, ticket_id, staff_name):
    ticket = get_ticket(tickets, ticket_id)
    if not isinstance(staff_name, str) or not staff_name.strip():
        raise ValidationError("Staff member name must not be blank.")
    if ticket["status"] == "resolved":
        raise WorkflowError(
            f"{ticket['id']} is resolved. Reopen it before modifying it."
        )
    ticket["assigned_to"] = staff_name.strip()
    return ticket
