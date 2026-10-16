# Individual reflections

Each engineer: one verified mistake, one learning gain, one improvement from code review.

## Engineer A: Mubarak Lawal
- **Verified mistake:** In the ticket-ID check I wrote in PR #3 I used
  `ID_PATTERN = re.compile(r"^T(\d+)$")` with `re.match` in `campusflow/tickets.py`, and the mirror
  of it in `campusflow/storage.py` (`_ID = re.compile(r"^T\d+$")` with `.match`). Because `$` also
  matches just before a trailing newline, `load_tickets` accepted a ticket whose ID was `"T001\n"`.
  I reproduced it by hand at the audited commit `26a0c9b`: I wrote that ID into `data/tickets.json`,
  ran `python main.py`, and instead of refusing to start the app listed the ticket (the embedded
  newline even split the printed row). Run against that same commit, `tests/test_bug_hunter.py`
  fails 4 cases — `StorageError not raised` twice and `0 != 2` twice; after `e3fa1bd` all pass and
  the suite is 90 tests green. Fixed with `re.compile(r"T([0-9]+)")` and `.fullmatch()`, which also
  closed the Unicode hole: `\d` accepts `"١"`, `[0-9]` does not.
  (Second verified mistake, same fix commit: `search_tickets` treated a whitespace-only query as a
  literal substring, so `"   "` filtered everything out and `"  wi-fi "` matched nothing.)
- **Learning gain:** A pattern is not a contract. "IDs are `T` followed by digits" was true in my
  head and false in three places in the code, because `^...$` with `re.match` does not mean "the
  whole string" and `\d` is not `[0-9]`. Two habits I am keeping: validate the entire string with
  `re.fullmatch` (or anchor with `\Z`), and normalise input at the boundary of the function that
  owns the rule instead of only in the caller that happens to exist today — the menu's `.strip()`
  was hiding a defect in the function's own documented contract.
- **Improvement from review:** The review recorded in `tests/test_bug_hunter.py` (Engineer B's
  review of my storage/ticket-ID module) pushed me past the newline case to the load-time
  invariant behind it: the file could hold a state the workflow can never produce. I added the
  check to `validate_tickets` so an `in_progress`/`resolved` ticket with no assignee is rejected on
  load, guarded by `test_in_progress_ticket_without_assignee_is_rejected_on_load`, and the
  canonical ID form is now enforced at load as well as at creation. Reviewing Engineer B's PRs #6,
  #7 and #9 is what made me apply the same question to her contract: `search_tickets` documented
  "empty string means no filter" and her CLI satisfied that by stripping, so I called the function
  directly, found the API-level gap, and fixed it with two tests of my own.

## Engineer B: <full name>
- **Verified mistake:** <TODO>
- **Learning gain:** <TODO>
- **Improvement from review:** <TODO>
