"""Search and filter logic for CampusFlow tickets."""
from .tickets import CATEGORIES, PRIORITIES, STATUSES

PRIORITY_RANK = {name: index for index, name in enumerate(PRIORITIES)}


def search_tickets(tickets, title_query="", category="", status="", priority=""):
    """Return tickets matching all supplied filters.

    Args:
        tickets: list of ticket dicts.
        title_query: case-insensitive substring to search in titles.
            Empty string means "do not filter by title."
        category: canonical category name, or empty for no filter.
        status: canonical status name, or empty for no filter.
        priority: canonical priority name, or empty for no filter.

    Returns:
        A new list of ticket dicts matching every supplied filter.
        The input list and its tickets are never modified.

    Side effects:
        None. This function is read-only.
    """
    results = []
    for ticket in tickets:
        if title_query and title_query.casefold() not in ticket["title"].casefold():
            continue
        if category and ticket["category"] != category:
            continue
        if status and ticket["status"] != status:
            continue
        if priority and ticket["priority"] != priority:
            continue
        results.append(ticket)
    return results


def sort_by_priority_then_id(tickets):
    """Return a new list sorted by priority rank, then numeric ticket ID.

    Args:
        tickets: list of ticket dicts.

    Returns:
        A new sorted list. The input list is not modified.

    Side effects:
        None.
    """
    return sorted(
        tickets,
        key=lambda t: (PRIORITY_RANK[t["priority"]], int(t["id"][1:])),
    )