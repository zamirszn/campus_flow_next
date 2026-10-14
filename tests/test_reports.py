import unittest
from campusflow.reports import build_report, format_report


def make_ticket(tid, status, priority, category):
    """Build a minimal ticket for report tests."""
    return {
        "id": tid,
        "title": "x",
        "category": category,
        "urgency": "low",
        "affected_users": 1,
        "priority": priority,
        "status": status,
        "assigned_to": None,
        "notes": [],
    }


class TestBuildReport(unittest.TestCase):

    def test_empty_report(self):
        r = build_report([])
        self.assertEqual(r["total"], 0)
        self.assertEqual(r["unresolved"], 0)
        self.assertEqual(r["resolved"], 0)
        self.assertEqual(r["resolution_rate"], 0.0)

    def test_counts_by_status(self):
        tickets = [
            make_ticket("T001", "open", "high", "Network"),
            make_ticket("T002", "open", "low", "Network"),
            make_ticket("T003", "resolved", "medium", "Hardware"),
        ]
        r = build_report(tickets)
        self.assertEqual(r["by_status"]["open"], 2)
        self.assertEqual(r["by_status"]["resolved"], 1)
        self.assertEqual(r["by_status"]["in_progress"], 0)

    def test_counts_by_priority(self):
        tickets = [
            make_ticket("T001", "open", "critical", "Network"),
            make_ticket("T002", "open", "high", "Network"),
            make_ticket("T003", "open", "high", "Hardware"),
        ]
        r = build_report(tickets)
        self.assertEqual(r["by_priority"]["critical"], 1)
        self.assertEqual(r["by_priority"]["high"], 2)
        self.assertEqual(r["by_priority"]["low"], 0)

    def test_counts_by_category(self):
        tickets = [
            make_ticket("T001", "open", "high", "Network"),
            make_ticket("T002", "open", "high", "Network"),
            make_ticket("T003", "open", "high", "Hardware"),
        ]
        r = build_report(tickets)
        self.assertEqual(r["by_category"]["Network"], 2)
        self.assertEqual(r["by_category"]["Hardware"], 1)
        self.assertEqual(r["by_category"]["Software"], 0)

    def test_unresolved_is_open_plus_in_progress(self):
        tickets = [
            make_ticket("T001", "open", "high", "Network"),
            make_ticket("T002", "in_progress", "high", "Network"),
            make_ticket("T003", "resolved", "high", "Network"),
        ]
        r = build_report(tickets)
        self.assertEqual(r["unresolved"], 2)
        self.assertEqual(r["resolved"], 1)

    def test_resolution_rate(self):
        tickets = [
            make_ticket("T001", "resolved", "high", "Network"),
            make_ticket("T002", "resolved", "high", "Network"),
            make_ticket("T003", "open", "high", "Network"),
            make_ticket("T004", "open", "high", "Network"),
        ]
        r = build_report(tickets)
        self.assertEqual(r["resolution_rate"], 50.0)

    def test_reopened_counts_as_current_status(self):
        tickets = [
            make_ticket("T001", "open", "high", "Network"),
        ]
        r = build_report(tickets)
        self.assertEqual(r["by_status"]["open"], 1)
        self.assertEqual(r["by_status"]["resolved"], 0)


class TestFormatReport(unittest.TestCase):

    def test_empty_report_formats_without_crash(self):
        text = format_report(build_report([]))
        self.assertIn("Total tickets: 0", text)
        self.assertIn("0.0%", text)

    def test_report_shows_categories(self):
        tickets = [make_ticket("T001", "open", "high", "Network")]
        text = format_report(build_report(tickets))
        self.assertIn("By category:", text)
        self.assertIn("Network", text)

    def test_report_shows_resolution_rate(self):
        tickets = [
            make_ticket("T001", "resolved", "high", "Network"),
            make_ticket("T002", "open", "high", "Network"),
        ]
        text = format_report(build_report(tickets))
        self.assertIn("50.0%", text)


if __name__ == "__main__":
    unittest.main()