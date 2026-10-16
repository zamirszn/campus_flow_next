# AI learning log

Only write what actually happened. Each engineer needs at least TWO cycles; the team needs at
least ONE cycle where an AI suggestion was changed or rejected after evidence review.

## Cycle template
- **Concept gap:**
- **Exact question I asked AI:**
- **Summary of AI guidance:**
- **Tiny unrelated experiment I ran:**
- **Independent verification (test / docs):**
- **Final engineering decision:**
- **Reflection:** What did I believe before? What did AI explain? Which claim did I test? What did the test show? What did I change in MY code? Which test guards it? Could I explain it without AI?

## Engineer A

### Cycle 1 — a ticket ID of `"T001\n"` loaded as valid (`$` vs `re.fullmatch`)

- **Concept gap:** `ID_PATTERN` in `campusflow/tickets.py` and `_ID` in `campusflow/storage.py`
  were both `re.compile(r"^T(\d+)$")`, used with `.match()`. I could not explain why a
  hand-edited `data/tickets.json` containing `"id": "T001\n"` was accepted as valid — I read `$`
  as "the string must end here, with nothing after the last digit".
- **Exact question I asked AI:** _<pending — to be recorded from the AI session>_
- **Summary of AI guidance:** _<pending — to be recorded from the AI session>_
- **Tiny unrelated experiment I ran:** _<pending — to be recorded from the AI session>_
- **Independent verification (test / docs):** The `re` documentation defines `$` as matching "at
  the end of the string or just before the newline at the end of the string", which is exactly the
  hole; `re.fullmatch` and `\Z` carry no such exception. `tests/test_bug_hunter.py::BugHunterForStorage::test_id_with_trailing_newline_is_rejected_on_load`
  fails at `26a0c9b` (`AssertionError: StorageError not raised`) and passes at `e3fa1bd`. Running
  the five bug-hunter cases against `26a0c9b` gives 4 failures; the full suite is 71 tests / 1
  failure before and 90 tests / 0 failures after.
- **Final engineering decision:** `campusflow/tickets.py`: `ID_PATTERN = re.compile(r"T([0-9]+)")`
  with `ID_PATTERN.fullmatch(ticket_id)` in `ticket_number`. `campusflow/storage.py`:
  `_ID = re.compile(r"T[0-9]+")` validated with `_ID.fullmatch(ticket["id"])`. I changed `\d` to
  `[0-9]` in both, because `\d` is Unicode-aware and would otherwise have accepted `"T١"`
  (Arabic-Indic one) as a ticket ID. Both checks now enforce one canonical form: `T` + ASCII digits,
  whole string, at creation **and** at load.
- **Reflection:** Before this I believed `^T\d+$` fully described the ID format, so the format was
  guaranteed by the pattern itself and could not be bypassed. What I did not know is that `$` also
  matches immediately before a trailing newline, so a value carrying hidden trailing whitespace
  satisfies the same pattern, and that `\d` matches far more than `0-9`. I tested that instead of
  taking it on faith: writing `"T001\n"` into the file and starting the app listed the ticket
  instead of refusing to load, and then the bug-hunter case failed with `StorageError not raised`.
  I changed both of MY checks to `fullmatch` with `[0-9]+`, and
  `test_id_with_trailing_newline_is_rejected_on_load` is the test that fails if anyone reverts to
  `$`. The same review made me look at the rest of `validate_tickets`, where I had accepted
  `in_progress`/`resolved` tickets with no assignee — a state the workflow can never produce — so
  I added that invariant and `test_in_progress_ticket_without_assignee_is_rejected_on_load`. I can
  now explain `$` vs `\Z` vs `fullmatch` without AI.

### Cycle 2 — a whitespace-only search query filtered instead of being ignored

- **Concept gap:** `search_tickets` in `campusflow/search.py` documented
  `title_query: ... Empty string means "do not filter by title."` but its body used the raw value:
  `if title_query and title_query.casefold() not in ticket["title"].casefold()`. I could not
  explain where "blank means no filter" was supposed to be enforced — the menu strips with
  `.strip()` before calling, so blank looked handled, yet the function's own contract only held for
  the exact empty string.
- **Exact question I asked AI:** _<pending — to be recorded from the AI session>_
- **Summary of AI guidance:** _<pending — to be recorded from the AI session>_
- **Tiny unrelated experiment I ran:** _<pending — to be recorded from the AI session>_
- **Independent verification (test / docs):** `tests/test_search.py` already contained
  `test_whitespace_query_is_treated_as_no_filter`, but it passes `""` — it covers the input I had
  in mind, not whitespace, which is why it stayed green while the function was wrong. The two new
  cases fail at `26a0c9b` and pass at `e3fa1bd`:
  `test_whitespace_only_query_means_no_title_filter` (`AssertionError: 0 != 2`) and
  `test_query_with_surrounding_spaces_still_matches`. Hand test at the audited commit:
  `search_tickets(tickets, "   ")` returned `[]` and `search_tickets(tickets, "  wi-fi ")`
  returned `[]`, while the same whitespace input through menu 12 returned the ticket, because
  `cli.py` strips before calling.
- **Final engineering decision:** Normalise at the boundary of the function that owns the rule,
  not only in the caller that currently exists:
  `title_query = title_query.strip() if isinstance(title_query, str) else ""`, then
  `needle = title_query.casefold()` used for the comparison, and the docstring updated to
  "Empty or whitespace-only means 'do not filter by title.'" I kept the CLI's `.strip()` as a
  second line of defence and left the other three filters comparing canonical values.
- **Reflection:** Before this I believed trimming in the menu was sufficient, because the menu is
  the only way a user reaches the function — I had confused "no user can hit this" with "this
  cannot happen". Two things were wrong with that: the function is a public API that other callers
  use directly, and the padded query was a real usability defect, since `"  wi-fi "` matched
  nothing at all even though `"Campus Wi-Fi is down"` existed. I tested the claim rather than
  reasoning about it — calling the function directly with `"   "` and `"  wi-fi "` returned `[]`
  for both while the menu returned results — and then I changed MY code so the contract holds for
  every caller, leaving the CLI strip in place. Two tests guard it
  (`test_whitespace_only_query_means_no_title_filter`,
  `test_query_with_surrounding_spaces_still_matches`). The durable lesson is boundary vs caller
  normalisation: normalise where the rule lives, and make the test use the input a real keyboard
  produces (`" "`) rather than the input that is convenient to type in a test. I can explain this
  without AI.

## Engineer B
### Cycle 1
<TODO>
### Cycle 2
<TODO>
