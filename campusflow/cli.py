"""Text menu. input/output are injectable so the CLI can be tested."""
from .reports import build_report, format_report
from .notes import add_note, get_notes
from .storage import DEFAULT_PATH, StorageError, load_tickets, save_tickets
from .tickets import (
    CATEGORIES, PRIORITIES, STATUSES, URGENCIES,
    CampusFlowError, assign_ticket, create_ticket, get_ticket,
)
from .search import search_tickets, sort_by_priority_then_id
from .workflow import change_status, reopen_ticket, work_queue

MENU = """
===== CampusFlow =====
1. Create ticket
2. List tickets
3. View ticket
4. Assign ticket
5. Change status
6. Reopen ticket
7. Work queue
8. Report
9. Exit
10. Add follow-up note
11. View ticket notes
12. Search tickets"""


def format_row(t):
    return (f"{t['id']:<6}{t['priority']:<10}{t['status']:<13}"
            f"{t['category']:<10}{(t['assigned_to'] or '-'):<14}{t['title']}")


def format_ticket(t):
    return "\n".join(f"  {key:<15}{value}" for key, value in t.items())


def print_rows(tickets, out, empty="No tickets."):
    if not tickets:
        out(empty)
        return
    out(f"{'ID':<6}{'PRIORITY':<10}{'STATUS':<13}{'CATEGORY':<10}{'ASSIGNED':<14}TITLE")
    for t in tickets:
        out(format_row(t))


def _create(tickets, ask, out):
    ticket = create_ticket(
        tickets,
        ask("Title: "),
        ask(f"Category ({'/'.join(CATEGORIES)}): "),
        ask(f"Urgency ({'/'.join(URGENCIES)}): "),
        ask("Affected users: "),
    )
    out(f"Created {ticket['id']} with priority {ticket['priority']}.")
    return True


def _list(tickets, ask, out):
    print_rows(tickets, out)
    return False


def _view(tickets, ask, out):
    out(format_ticket(get_ticket(tickets, ask("Ticket ID: "))))
    return False


def _assign(tickets, ask, out):
    ticket = assign_ticket(tickets, ask("Ticket ID: "), ask("Staff member: "))
    out(f"{ticket['id']} assigned to {ticket['assigned_to']}.")
    return True


def _status(tickets, ask, out):
    ticket = change_status(tickets, ask("Ticket ID: "),
                           ask("New status (open/in_progress/resolved): "))
    out(f"{ticket['id']} is now {ticket['status']}.")
    return True


def _reopen(tickets, ask, out):
    ticket = reopen_ticket(tickets, ask("Ticket ID: "))
    out(f"{ticket['id']} reopened.")
    return True


def _queue(tickets, ask, out):
    print_rows(work_queue(tickets), out, empty="The work queue is empty.")
    return False


def _report(tickets, ask, out):
    out(format_report(build_report(tickets)))
    return False


def _add_note(tickets, ask, out):
    note = add_note(tickets, ask("Ticket ID: "), ask("Author: "), ask("Message: "))
    out(f"Added note {note['note_id']}.")
    return True


def _view_notes(tickets, ask, out):
    ticket_id = ask("Ticket ID: ")
    notes = get_notes(tickets, ticket_id)
    if not notes:
        out(f"No notes for {ticket_id.strip().upper()}.")
    else:
        for note in notes:
            out(f"{note['note_id']} | {note['author']} | {note['message']}")
    return False


def _ask_filter(ask, out, label, allowed):
    """Prompt until the user gives a valid value or blank."""
    while True:
        raw = ask(f"{label} [{', '.join(allowed)}] (or blank): ").strip()
        if raw == "":
            return ""
        for value in allowed:
            if value.casefold() == raw.casefold():
                return value
        out(f"Invalid {label.lower()}. Allowed: {', '.join(allowed)}.")


def _search(tickets, ask, out):
    """Read-only search with optional combined filters."""
    title_query = ask("Title contains (or blank): ").strip()
    category = _ask_filter(ask, out, "Category", CATEGORIES)
    status = _ask_filter(ask, out, "Status", STATUSES)
    priority = _ask_filter(ask, out, "Priority", PRIORITIES)

    results = search_tickets(tickets, title_query, category, status, priority)

    if not results:
        out("No tickets match your search.")
        return False

    out(f"Found {len(results)} matching ticket(s):")
    print_rows(results, out)
    return False


HANDLERS = {"1": _create, "2": _list, "3": _view, "4": _assign,
            "5": _status, "6": _reopen, "7": _queue, "8": _report,
            "10": _add_note, "11": _view_notes, "12": _search}


def run(path=DEFAULT_PATH, input_func=input, output_func=print):
    """Run the menu loop. Returns a process exit code."""
    try:
        tickets = load_tickets(path)
    except StorageError as exc:
        output_func(f"Error: {exc}")
        return 1
    while True:
        output_func(MENU)
        try:
            choice = input_func("Choose an option: ").strip()
        except EOFError:
            return 0
        if choice == "9":
            output_func("Goodbye.")
            return 0
        handler = HANDLERS.get(choice)
        if handler is None:
            output_func("Please choose a valid menu option (1-12).")
            continue
        try:
            if handler(tickets, input_func, output_func):
                save_tickets(tickets, path)
        except CampusFlowError as exc:
            output_func(f"Error: {exc}")