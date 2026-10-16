"""Engineering Understanding Check: question bank, scoring, retry, explanations."""
import os
import tempfile
import unittest

from campusflow.question_bank import QUESTIONS
from campusflow.understanding_check import ask_choice, run_check, score_answers
from tests.helpers import CliTestCase

CORRECT = {q["id"]: q["answer"] for q in QUESTIONS}


def scripted(inputs):
    feed = iter(inputs)
    lines = []
    return (lambda prompt="": next(feed)), lines.append, lines


class QuestionBankTests(unittest.TestCase):
    def test_bank_has_six_well_formed_questions(self):
        self.assertEqual(len(QUESTIONS), 6)
        for q in QUESTIONS:
            self.assertEqual(list(q["options"]), ["A", "B", "C", "D"])
            self.assertIn(q["answer"], q["options"])

    def test_scoring_is_independent_of_the_menu(self):
        self.assertEqual(score_answers(QUESTIONS, CORRECT), 6)
        self.assertEqual(score_answers(QUESTIONS, {}), 0)
        partial = dict(CORRECT, Q1="A", Q2="A")
        self.assertEqual(score_answers(QUESTIONS, partial), 4)


class RunCheckTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.addCleanup(self._dir.cleanup)
        self.note = os.path.join(self._dir.name, "note.md")

    def run_quiz(self, answers, extra):
        ask, out, lines = scripted(list(answers) + list(extra))
        score = run_check(ask, out, note_path=self.note)
        return score, "\n".join(lines)

    def test_invalid_answer_retries_then_scores(self):
        ask, out, lines = scripted(["Z", "", "1", "b"])
        self.assertEqual(ask_choice(ask, out), "B")
        self.assertEqual(sum("Invalid choice" in l for l in lines), 3)

    def test_perfect_score_and_saved_explanations(self):
        answers = [CORRECT[q["id"]] for q in QUESTIONS]
        score, text = self.run_quiz(
            answers, ["q3", "Q5", "Filters combine with AND in search_tickets.",
                      "validate_tickets rejects duplicate IDs before replacing memory."])
        self.assertEqual(score, 6)
        self.assertIn("Final score: 6/6", text)
        with open(self.note) as handle:
            saved = handle.read()
        self.assertIn("Q3", saved)
        self.assertIn("Q5", saved)
        self.assertIn("Filters combine with AND", saved)

    def test_wrong_first_answers_are_scored_even_with_feedback(self):
        answers = ["A", "A"] + [CORRECT[q["id"]] for q in QUESTIONS[2:]]
        score, text = self.run_quiz(answers, ["Q1", "Q2", "I picked A by mistake here.",
                                              "I thought 100 percent was right."])
        self.assertEqual(score, 4)
        self.assertIn("Not quite. The best answer is B.", text)

    def test_explanation_must_be_real_text_and_questions_distinct(self):
        answers = [CORRECT[q["id"]] for q in QUESTIONS]
        _, text = self.run_quiz(answers, ["Q1", "Q1", "Q9", "Q2", "ok",
                                          "Rejecting keeps the ticket unchanged.",
                                          "Zero tickets must not divide by zero."])
        self.assertIn("You already explained that one", text)
        self.assertIn("Invalid question", text)
        self.assertIn("at least 10 characters", text)


class CliUnderstandingCheckTests(CliTestCase):
    def test_menu_14_runs_check_and_saves_note_beside_data_file(self):
        answers = [CORRECT[q["id"]] for q in QUESTIONS]
        code, text = self.drive(["14"] + answers + [
            "Q1", "Q2", "Unassigned tickets cannot start work.",
            "Empty report is guarded to 0 percent.", "9"])
        self.assertEqual(code, 0)
        self.assertIn("Final score: 6/6", text)
        note = os.path.join(os.path.dirname(self.path), "learning_note.md")
        self.assertTrue(os.path.exists(note))
