import copy
import unittest
from campusflow.search import search_tickets, sort_by_priority_then_id


def make_ticket(tid, title, category, priority, status):
    return {
        "id": tid,
        "title": title,
        "category": category,
        "urgency": "low",
        "affected_users": 1,
        "priority": priority,
        "status": status,
        "assigned_to": None,
        "notes": [],
    }


class TestSearchTickets(unittest.TestCase):

    def setUp(self):
        self.tickets = [
            make_ticket("T001", "Campus Wi-Fi is down", "Network", "critical", "open"),
            make_ticket("T002", "Wi-Fi drops in Block B", "Network", "high", "resolved"),
            make_ticket("T003", "Printer broken", "Hardware", "medium", "open"),
            make_ticket("T010", "Slow network", "Network", "high", "open"),
        ]

    def test_empty_query_returns_all(self):
        self.assertEqual(len(search_tickets(self.tickets)), 4)

    def test_title_substring_hyphen(self):
        results = search_tickets(self.tickets, title_query="wi-fi")
        self.assertEqual({t["id"] for t in results}, {"T001", "T002"})

    def test_title_case_insensitive(self):
        results = search_tickets(self.tickets, title_query="WI-FI")
        self.assertEqual({t["id"] for t in results}, {"T001", "T002"})

    def test_no_match_returns_empty(self):
        results = search_tickets(self.tickets, title_query="banana")
        self.assertEqual(results, [])

    def test_title_without_hyphen_does_not_match(self):
        results = search_tickets(self.tickets, title_query="wifi")
        self.assertEqual(results, [])

    def test_category_filter(self):
        results = search_tickets(self.tickets, category="Network")
        self.assertEqual({t["id"] for t in results}, {"T001", "T002", "T010"})

    def test_status_filter(self):
        results = search_tickets(self.tickets, status="open")
        self.assertEqual({t["id"] for t in results}, {"T001", "T003", "T010"})

    def test_priority_filter(self):
        results = search_tickets(self.tickets, priority="high")
        self.assertEqual({t["id"] for t in results}, {"T002", "T010"})

    def test_combined_filters_and(self):
        results = search_tickets(
            self.tickets, title_query="wi-fi", category="Network", status="open"
        )
        self.assertEqual([t["id"] for t in results], ["T001"])

    def test_whitespace_query_is_treated_as_no_filter(self):
        # Empty string returned by strip() should behave like no filter.
        # The CLI strips before passing to search_tickets. At the search level,
        # an empty string means "no filter", so it returns all.
        results = search_tickets(self.tickets, title_query="")
        self.assertEqual(len(results), 4)

    def test_search_does_not_modify_tickets(self):
        before = copy.deepcopy(self.tickets)
        search_tickets(self.tickets, title_query="wi-fi", status="open")
        self.assertEqual(self.tickets, before)

    def test_search_returns_references_not_copies(self):
        # Read-only means we don't copy. The results contain the same dicts.
        results = search_tickets(self.tickets, title_query="wi-fi")
        self.assertIs(results[0], self.tickets[0])


class TestSortByPriorityThenId(unittest.TestCase):

    def test_priority_order(self):
        tickets = [
            make_ticket("T003", "x", "Other", "low", "open"),
            make_ticket("T001", "x", "Other", "critical", "open"),
            make_ticket("T002", "x", "Other", "high", "open"),
            make_ticket("T004", "x", "Other", "medium", "open"),
        ]
        ids = [t["id"] for t in sort_by_priority_then_id(tickets)]
        self.assertEqual(ids, ["T001", "T002", "T004", "T003"])

    def test_tie_broken_by_numeric_id(self):
        tickets = [
            make_ticket("T010", "x", "Other", "high", "open"),
            make_ticket("T002", "x", "Other", "high", "open"),
            make_ticket("T001", "x", "Other", "high", "open"),
        ]
        ids = [t["id"] for t in sort_by_priority_then_id(tickets)]
        self.assertEqual(ids, ["T001", "T002", "T010"])

    def test_sort_does_not_modify_input(self):
        tickets = [
            make_ticket("T002", "x", "Other", "high", "open"),
            make_ticket("T001", "x", "Other", "critical", "open"),
        ]
        before = list(tickets)
        sort_by_priority_then_id(tickets)
        self.assertEqual(tickets, before)


if __name__ == "__main__":
    unittest.main()