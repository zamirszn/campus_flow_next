"""Bug-hunter tests: edge cases not in the guide's 14 acceptance cases.

Each records: initial state, input, expected result, name, fix made.
"""
import json
import os
import tempfile
import unittest

from campusflow.search import search_tickets
from campusflow.storage import StorageError, load_tickets
from campusflow.tickets import next_ticket_id
from tests.helpers import make_ticket


class BugHunterForStorage(unittest.TestCase):
    """Written by Engineer B against Engineer A's storage/ticket-ID module."""

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.path = os.path.join(self._dir.name, "tickets.json")

    def _write(self, tickets):
        with open(self.path, "w") as handle:
            json.dump(tickets, handle)

    def test_id_with_trailing_newline_is_rejected_on_load(self):
        # Initial: file holds one ticket whose id is "T001\n".
        # Expected: load rejected (IDs must be exactly T + digits).
        # Before fix: regex "^T\d+$" let "$" match before the newline.
        self._write([make_ticket("T001\n", "Wi-Fi down")])
        with self.assertRaises(StorageError):
            load_tickets(self.path)

    def test_in_progress_ticket_without_assignee_is_rejected_on_load(self):
        # Invariant: in_progress/resolved tickets always have an assignee, so a
        # hand-edited file breaking it must not load.
        self._write([make_ticket("T001", "Wi-Fi down", status="in_progress")])
        with self.assertRaises(StorageError):
            load_tickets(self.path)

    def test_valid_in_progress_ticket_with_assignee_still_loads(self):
        self._write([make_ticket("T004", "Wi-Fi down", status="in_progress",
                                 assigned_to="Sam")])
        loaded = load_tickets(self.path)
        self.assertEqual(next_ticket_id(loaded), "T005")


class BugHunterForSearch(unittest.TestCase):
    """Written by Engineer A against Engineer B's search module."""

    def test_whitespace_only_query_means_no_title_filter(self):
        # Initial: two tickets. Input: title_query "   ".
        # Expected: both returned (same as blank). Before fix: "   " was
        # treated as a substring and matched only titles containing spaces.
        tickets = [make_ticket("T001", "Wifi"), make_ticket("T002", "Printer broken")]
        self.assertEqual(len(search_tickets(tickets, "   ")), 2)

    def test_query_with_surrounding_spaces_still_matches(self):
        tickets = [make_ticket("T001", "Campus Wi-Fi is down")]
        self.assertEqual(len(search_tickets(tickets, "  wi-fi ")), 1)
