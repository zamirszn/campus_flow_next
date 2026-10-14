"""Structured follow-up notes for CampusFlow tickets."""
import re

from .tickets import ValidationError, WorkflowError, get_ticket

_NOTE_ID = re.compile(r"^N([0-9]+)$")
_ALLOWED_STATUSES = {"open", "in_progress"}
_NOTE_FIELDS = {"note_id", "author", "message"}


def _validated_notes(ticket):
    """Return the notes list after checking its structure and ID uniqueness."""
    notes = ticket.get("notes", [])
    if not isinstance(notes, list):
        raise ValidationError("Ticket notes must be a list.")
    seen = set()
    for note in notes:
        if not isinstance(note, dict) or set(note) != _NOTE_FIELDS:
            raise ValidationError("Each note must contain note_id, author, and message only.")
        note_id = note.get("note_id")
        match = _NOTE_ID.fullmatch(note_id) if isinstance(note_id, str) else None
        if not match:
            raise ValidationError(f"Invalid note ID: {note_id!r}.")
        number = int(match.group(1))
        if number < 1 or note_id != f"N{number:03d}" or note_id in seen:
            raise ValidationError(f"Duplicate or invalid note ID: {note_id!r}.")
        seen.add(note_id)
        if not isinstance(note.get("author"), str) or not note["author"].strip():
            raise ValidationError(f"Note {note_id} has an invalid author.")
        message = note.get("message")
        if not isinstance(message, str) or not 5 <= len(message.strip()) <= 300:
            raise ValidationError(f"Note {note_id} must have a message of 5-300 characters.")
    return notes


def next_note_id(ticket):
    """Return the next per-ticket ID (N001, N002, ...), without mutation.

    Args: A ticket dictionary containing a list of valid notes (missing notes
        is treated as an empty list for compatibility with legacy records).
    Returns: The next note ID string.
    Raises: ValueError for malformed or duplicate existing note data.
    Side effects: None.
    """
    notes = _validated_notes(ticket)
    highest = max((int(_NOTE_ID.fullmatch(n["note_id"]).group(1)) for n in notes), default=0)
    return f"N{highest + 1:03d}"


def add_note(tickets, ticket_id, author, message):
    """Add a note to an open/in-progress ticket after validating all inputs.

    Args: tickets collection, ticket ID, author label, and message text.
        Author must be nonblank; trimmed message length must be 5-300.
    Returns: The new {note_id, author, message} dictionary.
    Raises: ValueError (including CampusFlowError subclasses) for unknown
        tickets, invalid text, malformed notes, or resolved/invalid status.
    Side effects: Appends exactly one note only on success; failures leave the
        collection unchanged. The author and message are stored trimmed.
    """
    ticket = get_ticket(tickets, ticket_id)
    if ticket.get("status") not in _ALLOWED_STATUSES:
        raise WorkflowError(
            f"Cannot add a note to {ticket.get('id', ticket_id)} while status is "
            f"{ticket.get('status')!r}. Reopen it first."
        )
    if not isinstance(author, str) or not author.strip():
        raise ValidationError("Note author must not be blank.")
    if not isinstance(message, str):
        raise ValidationError("Note message must be a string of 5-300 characters.")
    author = author.strip()
    message = message.strip()
    if not 5 <= len(message) <= 300:
        raise ValidationError("Note message must be between 5 and 300 characters after trimming.")
    note_id = next_note_id(ticket)
    note = {"note_id": note_id, "author": author, "message": message}
    # No validation or ID generation remains after this mutation.
    ticket.setdefault("notes", []).append(note)
    return note


def get_notes(tickets, ticket_id):
    """Return notes in numeric note-ID order without changing stored order.

    Args: ticket collection and an existing ticket ID.
    Returns: A new list of note dictionaries in ascending ID order.
    Raises: ValueError for unknown tickets or malformed notes.
    Side effects: None (the returned list contains references to note dicts).
    """
    ticket = get_ticket(tickets, ticket_id)
    notes = _validated_notes(ticket)
    return sorted(notes, key=lambda note: int(_NOTE_ID.fullmatch(note["note_id"]).group(1)))
