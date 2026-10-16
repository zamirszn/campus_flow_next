# Bug-hunter report

Results below were produced by running `tests/test_bug_hunter.py` against the code BEFORE and
AFTER the fixes. Before: 4 failures. After: all pass.

## 1. For storage / ticket IDs (to be credited to the engineer who writes the review)
- **Initial state:** JSON file with one ticket whose `id` is `"T001\n"`.
- **Input:** `load_tickets(path)`.
- **Expected:** `StorageError` (IDs must be `T` followed only by digits).
- **Actual (before):** the file loaded. The pattern `^T\d+$` with `re.match` lets `$` match before a trailing newline.
- **Test:** `test_id_with_trailing_newline_is_rejected_on_load`
- **Change:** use `re.fullmatch` and `[0-9]+` in `storage.py` and `tickets.py`.
- **Invariant made visible:** every stored ID has exactly one canonical form.

## 2. Related invariant gap found while reading the load code
- **Initial state:** JSON ticket with status `in_progress` and `assigned_to: null`.
- **Expected:** load rejected, because the workflow can never create this.
- **Actual (before):** it loaded, so the app held a state it forbids elsewhere.
- **Test:** `test_in_progress_ticket_without_assignee_is_rejected_on_load`
- **Change:** `validate_tickets` rejects in_progress/resolved tickets with no assignee.

## 3. For search
- **Initial state:** tickets "Wifi" and "Printer broken".
- **Input:** `search_tickets(tickets, "   ")` (and `"  wi-fi "` against "Campus Wi-Fi is down").
- **Expected:** blank-like query means no filter; surrounding spaces are ignored.
- **Actual (before):** `"   "` was used as a substring (only titles containing spaces matched); `"  wi-fi "` found nothing.
- **Tests:** `test_whitespace_only_query_means_no_title_filter`, `test_query_with_surrounding_spaces_still_matches`
- **Change:** `search_tickets` strips the query before casefolding.
