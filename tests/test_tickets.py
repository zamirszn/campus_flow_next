"""Engineer A: creation, validation, priority engine."""
import unittest

from campusflow.tickets import (
    ValidationError, calculate_priority, create_ticket, next_ticket_id,
    parse_affected_users, assign_ticket, TicketNotFoundError, WorkflowError,
)


class PriorityTests(unittest.TestCase):
    def test_high_urgency_12_users_is_critical(self):
        self.assertEqual(calculate_priority("high", 12), "critical")

    def test_high_urgency_2_users_is_high(self):
        self.assertEqual(calculate_priority("high", 2), "high")

    def test_low_urgency_4_users_is_medium(self):
        self.assertEqual(calculate_priority("low", 4), "medium")

    def test_low_urgency_1_user_is_low(self):
        self.assertEqual(calculate_priority("low", 1), "low")

    def test_boundaries(self):
        self.assertEqual(calculate_priority("high", 10), "critical")   # exactly 10
        self.assertEqual(calculate_priority("medium", 10), "high")     # users alone
        self.assertEqual(calculate_priority("low", 3), "medium")       # exactly 3
        self.assertEqual(calculate_priority("low", 2), "low")
        self.assertEqual(calculate_priority("medium", 1), "medium")

    def test_case_variations_are_normalised(self):
        self.assertEqual(calculate_priority(" HIGH ", "12"), "critical")


class ValidationTests(unittest.TestCase):
    def test_zero_affected_users_rejected(self):
        tickets = []
        with self.assertRaises(ValidationError):
            create_ticket(tickets, "Wi-Fi", "Network", "high", 0)
        self.assertEqual(tickets, [])

    def test_bad_affected_users_values_rejected(self):
        for bad in (-1, "-1", "2.5", 2.5, "abc", "", None, True):
            with self.subTest(bad=bad):
                with self.assertRaises(ValidationError):
                    parse_affected_users(bad)

    def test_blank_title_rejected(self):
        with self.assertRaises(ValidationError):
            create_ticket([], "   ", "Network", "low", 1)

    def test_invalid_category_and_urgency_rejected(self):
        with self.assertRaises(ValidationError):
            create_ticket([], "x", "Plumbing", "low", 1)
        with self.assertRaises(ValidationError):
            create_ticket([], "x", "Network", "urgent", 1)


class CreateTests(unittest.TestCase):
    def test_create_valid_ticket(self):
        tickets = []
        t = create_ticket(tickets, "  Campus Wi-Fi is down ", "network", "HIGH", "15")
        self.assertEqual(t, {
            "id": "T001", "title": "Campus Wi-Fi is down", "category": "Network",
            "urgency": "high", "affected_users": 15, "priority": "critical",
            "status": "open", "assigned_to": None, "notes": [],
        })
        self.assertEqual(tickets, [t])

    def test_ids_are_sequential_and_unique(self):
        tickets = []
        ids = [create_ticket(tickets, "t", "Other", "low", 1)["id"] for _ in range(3)]
        self.assertEqual(ids, ["T001", "T002", "T003"])

    def test_next_id_uses_highest_number_not_count(self):
        existing = [{"id": "T001"}, {"id": "T007"}]
        self.assertEqual(next_ticket_id(existing), "T008")


class AssignTests(unittest.TestCase):
    def setUp(self):
        self.tickets = []
        create_ticket(self.tickets, "Laptop", "Hardware", "low", 1)

    def test_assign(self):
        assign_ticket(self.tickets, "t001", "  Ada ")
        self.assertEqual(self.tickets[0]["assigned_to"], "Ada")

    def test_unknown_id_and_blank_name_rejected(self):
        with self.assertRaises(TicketNotFoundError):
            assign_ticket(self.tickets, "T999", "Ada")
        with self.assertRaises(ValidationError):
            assign_ticket(self.tickets, "T001", "  ")
        self.assertIsNone(self.tickets[0]["assigned_to"])

    def test_resolved_ticket_cannot_be_assigned(self):
        self.tickets[0]["status"] = "resolved"
        with self.assertRaises(WorkflowError):
            assign_ticket(self.tickets, "T001", "Ada")


if __name__ == "__main__":
    unittest.main()
