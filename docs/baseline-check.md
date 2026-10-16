# Baseline check

> Fill every field from what you actually ran at the AUDITED commit. Do not label a
> peer-reported bug "confirmed" until you reproduced it.

- **Audited commit SHA:** `26a0c9b` ("Merge pull request #9 from zamirszn/feat/5-search-cli").
  This is the commit immediately before my audit-and-fix commit `e3fa1bd`, so every number below
  is the behaviour **before** my corrections.
- **Run command:** `python main.py`
- **Test command:** `python -m unittest discover -s tests -v`
- **Test result at that commit:** 71 tests, 70 passed, **1 failed**.
  `test_storage.CliTests.test_invalid_menu_choice` failed: it still asserted
  `"Please choose a valid menu option (1-11)."` while `cli.py` printed `(1-12)`, because PR #9
  added menu option 12. `cli.py` was right and the assertion was stale, but until it was updated
  the suite could not be green. The other 70 tests passed.

## Three inputs I tested by hand
| # | Input | Expected | Actual |
|---|-------|----------|--------|
| 1 | `data/tickets.json` holding one ticket with `"id": "T001\n"`, then `python main.py` and menu 2 (List) | The app refuses to start with a clear error, because `"T001\n"` is not `T` followed only by digits | The app started, printed the menu and listed the ticket. The embedded newline even tore the row apart: the title printed on one line and the priority (`critical`) shifted to the next |
| 2 | Menu 10 (Add follow-up note) on a **resolved** ticket assigned to `Sam`, author `Mubarak`, message `Printer replaced today` | Rejected, because a resolved ticket must be reopened before it can be modified | `Error: Cannot add a note to T001 while status is 'resolved'. Reopen it first.` and no note stored. The same input on an **open** ticket printed `Added note N001.` — the notes layer behaved correctly at this commit |
| 3 | `search_tickets(tickets, "   ")` and `search_tickets(tickets, "  wi-fi ")` against titles `"Campus Wi-Fi is down"` and `"Printer broken"` | Blank-like query means "no title filter" (both tickets); the padded query is the same as `"wi-fi"` (1 ticket) | `[]` and `[]` — both queries filtered everything out. Note that the **same** whitespace input through menu 12 looked correct, because `cli.py` calls `.strip()` before calling the function, so the menu hid the defect |

## What my audit said needed improvement
1. **The ticket-ID format was not enforced on load** (`tickets.py`, `storage.py`). `^T(\d+)$` with
   `.match()` accepts `"T001\n"`, so a hand-edited file could introduce an ID the rest of the app
   would then treat as canonical. `\d` is also Unicode-aware, so `"T١"` passed as well.
2. **The load accepted a state the workflow can never produce** (`storage.py`). A ticket with
   status `in_progress`/`resolved` and `assigned_to: null` loaded fine, even though
   `change_status` refuses to create that combination. Load validation was checking fields but not
   this invariant.
3. **`search_tickets` did not honour its own contract** (`search.py`). The docstring promised
   `Empty string means "do not filter by title."`, but any caller passing whitespace instead of an
   empty string got a literal substring filter. The CLI's `.strip()` covered the one caller that
   existed, which is why the bug survived.
4. **A stale assertion blocked a green suite** (`tests/test_storage.py`). PR #9 changed the
   invalid-option message range without updating the test that asserts it.

## Reproduced vs not reproduced
- **Peer report — ID with a trailing newline loads** (recorded in `tests/test_bug_hunter.py` as
  Engineer B's review of my storage/ticket-ID module): **reproduced**. Hand test 1 above, and the
  case fails at `26a0c9b` with `AssertionError: StorageError not raised`.
- **Peer report — `in_progress` ticket without an assignee loads**: **reproduced**. Fails at
  `26a0c9b` with `AssertionError: StorageError not raised`.
- **My report against search — whitespace-only query filters instead of being ignored**:
  **reproduced at API level** (`AssertionError: 0 != 2`) and **deliberately recorded as not
  reproducible through menu 12**, since the CLI strips first. It is an API-contract defect, not a
  user-visible one, and I have written it up that way rather than overstating it.
- **Nothing in the peer reports failed to reproduce.** Running all five bug-hunter cases against
  `26a0c9b` gives exactly 4 failures (the two above, plus the two search cases); the fifth
  (`test_valid_in_progress_ticket_with_assignee_still_loads`) passes both before and after, which
  is the check that my fix did not reject valid data. Full suite at `e3fa1bd`: 90 tests, 0 failures.
