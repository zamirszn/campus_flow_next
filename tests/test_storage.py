"""Persistence and CLI end-to-end."""
import json
import os
import tempfile
import unittest

from campusflow.cli import run
from campusflow.storage import StorageError, load_tickets, save_tickets
from campusflow.tickets import create_ticket


class StorageTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.path = os.path.join(self._dir.name, "data", "tickets.json")

    def test_missing_file_gives_fresh_start(self):
        self.assertEqual(load_tickets(self.path), [])

    def test_round_trip_preserves_tickets(self):
        tickets = []
        create_ticket(tickets, "Wi-Fi", "Network", "high", 15)
        create_ticket(tickets, "Laptop", "Hardware", "low", 1)
        save_tickets(tickets, self.path)
        self.assertEqual(load_tickets(self.path), tickets)


    def test_round_trip_preserves_notes_and_next_note_id(self):
        from campusflow.notes import add_note
        tickets = []
        create_ticket(tickets, "Wi-Fi", "Network", "high", 15)
        add_note(tickets, "T001", "Ada", "Router rebooted")
        save_tickets(tickets, self.path)
        reloaded = load_tickets(self.path)
        self.assertEqual(reloaded[0]["notes"][0]["note_id"], "N001")
        self.assertEqual(add_note(reloaded, "T001", "Grace", "Checking switch" )["note_id"], "N002")

    def test_new_ticket_after_reload_has_unique_id(self):
        tickets = []
        create_ticket(tickets, "a", "Other", "low", 1)
        create_ticket(tickets, "b", "Other", "low", 1)
        save_tickets(tickets, self.path)
        reloaded = load_tickets(self.path)
        new = create_ticket(reloaded, "c", "Other", "low", 1)
        self.assertEqual(new["id"], "T003")
        ids = [t["id"] for t in reloaded]
        self.assertEqual(len(ids), len(set(ids)))

    def test_malformed_json_raises_and_file_is_untouched(self):
        os.makedirs(os.path.dirname(self.path))
        with open(self.path, "w") as f:
            f.write("{not json")
        with self.assertRaises(StorageError):
            load_tickets(self.path)
        with open(self.path) as f:
            self.assertEqual(f.read(), "{not json")

    def test_wrong_shape_or_invalid_records_rejected(self):
        os.makedirs(os.path.dirname(self.path))
        for payload in ({"a": 1}, [1], [{"id": "T001"}]):
            with self.subTest(payload=payload):
                with open(self.path, "w") as f:
                    json.dump(payload, f)
                with self.assertRaises(StorageError):
                    load_tickets(self.path)

    def test_duplicate_ids_in_file_rejected(self):
        tickets = []
        create_ticket(tickets, "a", "Other", "low", 1)
        save_tickets(tickets + tickets, self.path)
        with self.assertRaises(StorageError):
            load_tickets(self.path)


class CliTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.path = os.path.join(self._dir.name, "tickets.json")

    def drive(self, answers):
        feed, out = iter(answers), []
        code = run(self.path, input_func=lambda prompt="": next(feed), output_func=out.append)
        return code, "\n".join(out)

    def test_full_session_with_restart(self):
        code, text = self.drive([
            "1", "Wi-Fi down", "network", "high", "15",        # create -> critical
            "1", "Bad", "network", "high", "0",                # invalid, rejected
            "5", "T001", "in_progress",                        # unassigned -> rejected
            "4", "T001", "Ada",
            "5", "T001", "in_progress",
            "7", "8", "9",
        ])
        self.assertEqual(code, 0)
        self.assertIn("Created T001 with priority critical", text)
        self.assertIn("affected_users must be a positive whole number", text)
        self.assertIn("unassigned", text)
        self.assertIn("T001 is now in_progress", text)
        self.assertIn("The work queue is empty.", text)   # in_progress leaves queue
        # restart: data persisted, next ID continues
        code, text = self.drive(["2", "1", "Printer", "hardware", "low", "1", "9"])
        self.assertIn("Wi-Fi down", text)
        self.assertIn("Created T002", text)

    def test_corrupted_file_stops_app_without_overwriting(self):
        with open(self.path, "w") as f:
            f.write("oops")
        code, text = self.drive(["9"])
        self.assertEqual(code, 1)
        self.assertIn("not valid JSON", text)
        with open(self.path) as f:
            self.assertEqual(f.read(), "oops")

    def test_invalid_menu_choice(self):
        code, text = self.drive(["x", "9"])
        self.assertIn("Please choose a valid menu option (1-11).", text)


if __name__ == "__main__":
    unittest.main()
