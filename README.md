# CampusFlow

A command-line helpdesk for Learn2Earn campus staff. It records support problems
(Wi-Fi outages, faulty laptops, ...), calculates priority, assigns work, tracks
status, shows a work queue and reports, and saves everything to JSON.

**Team:** Engineer A: <name> (creation, validation, priority engine) | Engineer B: <name> (assignment, lifecycle, queue, reports)
**Reviewed PRs:** <link to A's PR> | <link to B's PR>

## Setup
Python 3.9+ and the standard library only. No installs needed.

```bash
python main.py                              # run the CLI
python -m unittest discover -s tests -v     # run the tests
```

## Menu
1 Create | 2 List | 3 View | 4 Assign | 5 Change status | 6 Reopen | 7 Work queue | 8 Report | 9 Exit | 10 Add follow-up note | 11 View ticket notes

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
Tickets are saved to `data/tickets.json` after every change (git-ignored). Delete the file
to start fresh. A missing file means a fresh start; a malformed or invalid file stops the app
with a clear error and is never overwritten.

## Tests
`tests/test_tickets.py` priority rules and boundaries, validation, ID generation, assignment.
`tests/test_workflow.py` lifecycle, reopen, queue ordering, reports (incl. zero tickets).
`tests/test_storage.py` JSON round-trip, unique IDs after reload, corrupted files, CLI session. `tests/test_notes.py` note validation, lifecycle, ordering, and state integrity.

## Known limitations
- Single user, no locking: two instances writing the same file can overwrite each other.
- The queue shows `open` tickets only; `in_progress` tickets are not listed in it.
- No editing of title/category/urgency after creation; no deleting tickets.
- Text interface only.
