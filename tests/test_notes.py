"""Regression tests for structured ticket notes."""
from copy import deepcopy
import unittest

from campusflow.notes import add_note, get_notes, next_note_id
from campusflow.tickets import create_ticket, ValidationError, TicketNotFoundError
from campusflow.workflow import change_status, reopen_ticket


class NotesTests(unittest.TestCase):
    def setUp(self):
        self.tickets = []
        create_ticket(self.tickets, "Wi-Fi outage", "Network", "high", 3)

    def test_add_note_trims_fields_and_returns_note(self):
        note = add_note(self.tickets, "T001", " Ada ", "  Router rebooted  ")
        self.assertEqual(note, {"note_id": "N001", "author": "Ada", "message": "Router rebooted"})
        self.assertEqual(self.tickets[0]["notes"], [note])

    def test_note_ids_are_per_ticket(self):
        create_ticket(self.tickets, "Laptop", "Hardware", "low", 1)
        self.assertEqual(add_note(self.tickets, "T001", "A", "First note")["note_id"], "N001")
        self.assertEqual(add_note(self.tickets, "T002", "B", "First note")["note_id"], "N001")

    def test_next_id_uses_highest_existing_not_count(self):
        self.tickets[0]["notes"] = [
            {"note_id": "N001", "author": "A", "message": "First note"},
            {"note_id": "N003", "author": "B", "message": "Third note"},
        ]
        self.assertEqual(next_note_id(self.tickets[0]), "N004")

    def test_get_notes_numeric_order_without_mutating_storage(self):
        self.tickets[0]["notes"] = [
            {"note_id": "N010", "author": "A", "message": "Tenth note"},
            {"note_id": "N002", "author": "B", "message": "Second note"},
        ]
        before = deepcopy(self.tickets[0]["notes"])
        self.assertEqual([n["note_id"] for n in get_notes(self.tickets, "T001")], ["N002", "N010"])
        self.assertEqual(self.tickets[0]["notes"], before)

    def test_message_length_boundaries(self):
        for message in ("abcd", "x" * 301):
            before = deepcopy(self.tickets)
            with self.subTest(length=len(message)), self.assertRaises(ValueError):
                add_note(self.tickets, "T001", "Ada", message)
            self.assertEqual(self.tickets, before)
        self.assertEqual(add_note(self.tickets, "T001", "Ada", "12345")["note_id"], "N001")
        self.assertEqual(add_note(self.tickets, "T001", "Ada", "x" * 300)["note_id"], "N002")

    def test_blank_author_and_unknown_ticket_rejected_without_changes(self):
        before = deepcopy(self.tickets)
        with self.assertRaises(ValueError):
            add_note(self.tickets, "T001", "  ", "A valid message")
        self.assertEqual(self.tickets, before)
        with self.assertRaises(TicketNotFoundError):
            add_note(self.tickets, "T404", "Ada", "A valid message")
        self.assertEqual(self.tickets, before)

    def test_resolved_note_rejected_then_reopen_preserves_notes_and_id(self):
        add_note(self.tickets, "T001", "Ada", "First note")
        # Assign first because the workflow correctly blocks unassigned tickets.
        from campusflow.tickets import assign_ticket
        assign_ticket(self.tickets, "T001", "Ada")
        change_status(self.tickets, "T001", "in_progress")
        change_status(self.tickets, "T001", "resolved")
        before = deepcopy(self.tickets)
        with self.assertRaises(ValueError):
            add_note(self.tickets, "T001", "Ada", "Rejected note")
        self.assertEqual(self.tickets, before)
        reopen_ticket(self.tickets, "T001")
        self.assertEqual(add_note(self.tickets, "T001", "Ada", "After reopen")["note_id"], "N002")

    def test_duplicate_existing_note_ids_rejected_without_mutation(self):
        note = {"note_id": "N001", "author": "Ada", "message": "First note"}
        self.tickets[0]["notes"] = [note.copy(), note.copy()]
        before = deepcopy(self.tickets)
        with self.assertRaises(ValueError):
            add_note(self.tickets, "T001", "Ada", "Another note")
        self.assertEqual(self.tickets, before)


if __name__ == "__main__":
    unittest.main()
