# CampusFlow

A command-line helpdesk for Learn2Earn campus staff. It records support problems
(Wi-Fi outages, faulty laptops, ...), calculates priority, assigns work, tracks
status, shows a work queue and reports, and saves everything to JSON.

**Team:** Engineer A: Mubarak Lawal (creation, validation, priority engine) | Engineer B: John Serah (assignment, lifecycle, queue, reports)
**Reviewed PRs:** [A: notes data layer #3](https://github.com/zamirszn/campus_flow_next/pull/3) | [B: search_tickets #6](https://github.com/zamirszn/campus_flow_next/pull/6), [reports #7](https://github.com/zamirszn/campus_flow_next/pull/7), [search CLI #9](https://github.com/zamirszn/campus_flow_next/pull/9)

## Setup
Python 3.9+ and the standard library only. No installs needed.

```bash
python main.py                              # run the CLI
python -m unittest discover -s tests -v     # run the tests
```

## Menu
1 Create | 2 List | 3 View | 4 Assign | 5 Change status | 6 Reopen | 7 Work queue | 8 Report | 9 Exit | 10 Add follow-up note | 11 View ticket notes | 12 Search tickets | 13 Search tickets (sorted by priority, then ID) | 14 Engineering understanding check

## Search (menu 12 and 13)
Read-only. Prompts for: title text, category, status, priority. A blank answer means "do not
filter by that field"; an invalid category/status/priority re-prompts. Title matching is a
case-insensitive substring match (`casefold`), and a whitespace-only title counts as blank.
Every supplied filter must match (AND). Results show ID, priority, status, category, assignee
and title. Option 13 shows the same results sorted by priority, then numeric ticket ID. The
original Work Queue (menu 7) is unchanged and still shows only `open` tickets.

## Engineering Understanding Check (menu 14)
Six A/B/C/D scenario questions about this app's behaviour (invalid answers re-prompt). One point
per correct first answer, final score 0-6. You then choose two questions and explain your
answers in your own words; explanations are not auto-graded. They are appended to
`data/learning_note.md` (next to the data file, git-ignored) for mentor discussion.
Questions live in `campusflow/question_bank.py`; scoring is in `campusflow/understanding_check.py`.

## Rules
**Ticket:** id (T001, T002, ...), title (not blank), category (Network/Hardware/Software/Other),
urgency (low/medium/high), affected_users (positive whole number), priority, status, assigned_to, notes (a list of note dictionaries). Each note has note_id (N001, N002, ... per ticket), author and message. Notes require an open or in_progress ticket; author is trimmed and nonblank; message is trimmed to 5-300 characters. Notes remain through resolve/reopen.
Case variations such as `network` or `HIGH` are accepted and normalised.

**Priority (first match wins):**
1. high urgency AND 10+ users -> critical
2. high urgency OR 10+ users -> high
3. medium urgency OR 3+ users -> medium
4. otherwise -> low

**Status:** open -> in_progress -> resolved. An unassigned ticket cannot go to in_progress.
A resolved ticket can only be changed after an explicit Reopen (resolved -> open).

**Work queue:** tickets with status `open`, ordered critical -> high -> medium -> low,
ties broken by the lower numeric ID.

## Storage
**File format:** a plain JSON list of ticket objects (no envelope or version field), each with
`id, title, category, urgency, affected_users, priority, status, assigned_to, notes`. `notes` is a
list of `{note_id, author, message}`. Files from the original version (no `notes` key) still load;
their tickets get `notes: []` in memory and are upgraded on the next save, so no migration is needed.
On load the whole file is validated before anything is used: list structure, required keys, unique
and well-formed IDs (`T` + digits only), category/urgency/status values, `affected_users` (positive
int, not bool), priority consistent with urgency and users, in_progress/resolved tickets having an
assignee, and note shape/ID uniqueness. One bad record rejects the whole load; the app does not
start with partial data and the file is never overwritten.

Tickets are saved to `data/tickets.json` after every change (git-ignored). Delete the file
to start fresh. A missing file means a fresh start; a malformed or invalid file stops the app
with a clear error and is never overwritten.

## Tests
`tests/test_tickets.py` priority rules and boundaries, validation, ID generation, assignment.
`tests/test_workflow.py` lifecycle, reopen, queue ordering, reports (incl. zero tickets).
`tests/test_storage.py` JSON round-trip, unique IDs after reload, corrupted files, CLI session. `tests/test_notes.py` note validation, lifecycle, ordering, and state integrity. `tests/test_search.py` search logic. `tests/test_cli_search.py` search menus via scripted input. `tests/test_understanding.py` question bank, scoring, retry, explanations. `tests/test_bug_hunter.py` extra edge cases (see `docs/bug-hunter-report.md`). `tests/helpers.py` shared fixtures.

## Known limitations
- Single user, no locking: two instances writing the same file can overwrite each other.
- The Work Queue (menu 7) shows `open` tickets only; use search (menu 12/13) with status `in_progress` to find work in progress.
- No editing of title/category/urgency after creation; no deleting tickets.
- Text interface only.
