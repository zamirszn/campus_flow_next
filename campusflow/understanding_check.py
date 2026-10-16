"""Engineering Understanding Check: scoring and interaction.

The questions live in ``question_bank.py``. This module only asks, records,
scores and saves explanations. ``input_func`` / ``output_func`` are injectable
so everything can be tested without typing.
"""
import os
from datetime import datetime

from .question_bank import QUESTIONS

LETTERS = ("A", "B", "C", "D")
EXPLANATIONS_REQUIRED = 2
MIN_EXPLANATION_LENGTH = 10
DEFAULT_NOTE_PATH = os.path.join("data", "learning_note.md")


def score_answers(questions, answers):
    """Return the number of correct answers (one point each).

    Args: question list and a dict {question_id: submitted letter}.
    Returns: int, 0..len(questions). Missing or wrong answers score 0.
    Side effects: None.
    """
    return sum(1 for q in questions if answers.get(q["id"]) == q["answer"])


def ask_choice(ask, out, valid=LETTERS, prompt="Your answer (A/B/C/D): "):
    """Prompt until the user enters one of the valid letters (any case)."""
    while True:
        raw = ask(prompt).strip().upper()
        if raw in valid:
            return raw
        out(f"Invalid choice. Please enter one of: {', '.join(valid)}.")


def ask_explanation(ask, out, label):
    """Prompt until a non-trivial explanation is given. Never auto-graded."""
    while True:
        text = ask(f"Explain your answer to {label} in a sentence or two: ").strip()
        if len(text) >= MIN_EXPLANATION_LENGTH:
            return text
        out(f"Please write at least {MIN_EXPLANATION_LENGTH} characters.")


def save_explanations(path, explanations, score, total):
    """Append explanations to a local learning note for mentor discussion."""
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(f"## Understanding check {stamp} - score {score}/{total}\n")
        for item in explanations:
            handle.write(f"- {item['id']} (chose {item['choice']}): {item['text']}\n")
        handle.write("\n")


def run_check(ask=input, out=print, questions=None, note_path=DEFAULT_NOTE_PATH):
    """Run the quiz. Returns the final score.

    The first submitted answer to each question is the one scored; feedback is
    shown only after it is recorded. The user then explains
    EXPLANATIONS_REQUIRED of their answers (their choice of which), which are
    saved and shown for mentor discussion rather than graded.
    """
    questions = QUESTIONS if questions is None else questions
    out("\n=== Engineering Understanding Check ===")
    answers = {}
    for number, q in enumerate(questions, start=1):
        out(f"\nQuestion {number}/{len(questions)}: {q['prompt']}")
        for letter, text in q["options"].items():
            out(f"  {letter}. {text}")
        answers[q["id"]] = ask_choice(ask, out, tuple(q["options"]))
        if answers[q["id"]] == q["answer"]:
            out("Correct. " + q.get("feedback", ""))
        else:
            out(f"Not quite. The best answer is {q['answer']}. " + q.get("feedback", ""))

    score = score_answers(questions, answers)
    total = len(questions)
    out(f"\nFinal score: {score}/{total}")

    ids = [q["id"] for q in questions]
    wanted = min(EXPLANATIONS_REQUIRED, len(ids))
    chosen = []
    out(f"\nChoose {wanted} questions to explain ({', '.join(ids)}).")
    while len(chosen) < wanted:
        pick = ask(f"Question to explain ({len(chosen) + 1}/{wanted}): ").strip().upper()
        if pick not in ids:
            out(f"Invalid question. Choose from: {', '.join(ids)}.")
        elif pick in chosen:
            out("You already explained that one. Pick a different question.")
        else:
            chosen.append(pick)
    explanations = [
        {"id": qid, "choice": answers[qid], "text": ask_explanation(ask, out, qid)}
        for qid in chosen
    ]
    save_explanations(note_path, explanations, score, total)
    out(f"\nExplanations saved to {note_path} for mentor discussion:")
    for item in explanations:
        out(f"  {item['id']} (chose {item['choice']}): {item['text']}")
    return score
