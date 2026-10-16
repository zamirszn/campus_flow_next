"""Shared test helpers: scripted CLI sessions and ticket fixtures."""
import os
import tempfile
import unittest

from campusflow.cli import run


def make_ticket(tid, title, category="Network", urgency="low", users=1,
                priority="low", status="open", assigned_to=None):
    return {"id": tid, "title": title, "category": category, "urgency": urgency,
            "affected_users": users, "priority": priority, "status": status,
            "assigned_to": assigned_to, "notes": []}


class CliTestCase(unittest.TestCase):
    """Runs the menu with scripted input against a temporary data file."""

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.path = os.path.join(self._dir.name, "tickets.json")

    def drive(self, inputs):
        feed = iter(inputs)
        lines = []
        code = run(self.path, input_func=lambda prompt="": next(feed),
                   output_func=lines.append)
        return code, "\n".join(lines)
