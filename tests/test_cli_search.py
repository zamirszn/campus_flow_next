"""Search Tickets CLI views (menu 12 and 13), driven by scripted input."""
import json

from tests.helpers import CliTestCase, make_ticket

SAMPLE = [
    make_ticket("T001", "Campus Wi-Fi is down", "Network", "high", 15, "critical"),
    make_ticket("T002", "Wi-Fi drops in Block B", "Network", "low", 1, "low",
                status="resolved", assigned_to="Sam"),
    make_ticket("T003", "Printer broken", "Hardware", "medium", 1, "medium"),
    make_ticket("T010", "Slow network", "Network", "high", 1, "high"),
]


class CliSearchTests(CliTestCase):
    def setUp(self):
        super().setUp()
        with open(self.path, "w") as handle:
            json.dump(SAMPLE, handle)

    def test_combined_filters_use_and(self):
        _, text = self.drive(["12", "wifi", "network", "open", "", "9"])
        self.assertIn("No tickets match your search.", text)  # 'wifi' != 'wi-fi'
        _, text = self.drive(["12", "wi-fi", "network", "open", "", "9"])
        self.assertIn("Found 1 matching ticket(s):", text)
        self.assertIn("T001", text)
        self.assertNotIn("T002  ", text)   # resolved, filtered out by status

    def test_title_search_ignores_case(self):
        _, text = self.drive(["12", "WI-FI", "", "", "", "9"])
        self.assertIn("Found 2 matching ticket(s):", text)

    def test_invalid_filter_reprompts_then_accepts(self):
        _, text = self.drive(["12", "", "bogus", "Network", "", "", "9"])
        self.assertIn("Invalid category. Allowed: Network, Hardware, Software, Other.", text)
        self.assertIn("Found 3 matching ticket(s):", text)

    def test_blank_filters_return_every_ticket(self):
        _, text = self.drive(["12", "", "", "", "", "9"])
        self.assertIn("Found 4 matching ticket(s):", text)

    def test_search_does_not_modify_data_or_file(self):
        with open(self.path) as handle:
            before = handle.read()
        self.drive(["12", "wi-fi", "", "", "", "13", "", "", "", "", "9"])
        with open(self.path) as handle:
            self.assertEqual(handle.read(), before)

    def test_sorted_view_orders_by_priority_then_numeric_id(self):
        _, text = self.drive(["13", "", "network", "", "", "9"])
        order = [line.split()[0] for line in text.splitlines()
                 if line[:1] == "T" and line[1:4].isdigit()]
        self.assertEqual(order, ["T001", "T010", "T002"])  # critical, high, low

    def test_work_queue_unchanged_by_search_menu(self):
        _, text = self.drive(["7", "9"])
        rows = [line.split()[0] for line in text.splitlines()
                if line[:1] == "T" and line[1:4].isdigit()]
        self.assertEqual(rows, ["T001", "T010", "T003"])   # open only
        self.assertNotIn("T002", rows)
