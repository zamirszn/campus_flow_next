# Design decisions

| Question | Decision |
|---|---|
| Where are tickets stored? | A `list` of `dict`s, passed as the first argument to every function. |
| How is invalid input signalled? | Exceptions deriving from `CampusFlowError` (`ValidationError`, `TicketNotFoundError`, `WorkflowError`, `StorageError`). The CLI catches them and prints `Error: <message>`. |
| What do functions return? | `create_ticket`, `assign_ticket`, `change_status`, `reopen_ticket` return the updated ticket. |
| Who owns JSON? | `storage.py` (`load_tickets`, `save_tickets`); only `cli.py` calls it. |
| How do we test without input()? | Business logic never prompts. `cli.run` takes `input_func` / `output_func` so tests script it. |
| Corruption safety | Validate first, mutate last; saves are atomic (temp file + `os.replace`). |
| Queue meaning | "Open, unresolved" = status `open` (work waiting to be picked up). |
| ID generation | Highest existing number + 1, so IDs stay unique after reload. |
| Notes | Stored in `ticket["notes"]`; IDs N001, N002 per ticket from highest existing number + 1; all validation happens before the single `append`, so a rejected note consumes no ID. Same exception convention as tickets. |
| Search | `search_tickets` is read-only and returns a new list; filters combine with AND; blank means no filter; title match uses `casefold`. The CLI only prompts and prints. |
| Sorted search view | Separate menu option (13). The original Work Queue stays open-only; nothing silently changes its filter. |
| Ticket IDs | Sorted by the numeric part, never as text, so T2 comes before T10. IDs must match `T[0-9]+` exactly. |
| Load invariants | In addition to field checks, in_progress/resolved tickets must have an assignee, since the workflow can never produce otherwise. |
| Understanding check | Question bank (data) is separate from scoring and prompting. The first submitted answer is scored; feedback is shown afterwards. Explanations are saved, never auto-graded. |
| Learning note location | Beside the data file (`learning_note.md`), so tests use temp folders. |

## Ownership
- **Engineer A:** `tickets.py` (creation, validation, priority) + `tests/test_tickets.py`
- **Engineer B:** `workflow.py`, `reports.py` + `tests/test_workflow.py`
- **Both:** `storage.py`, `cli.py`, `tests/test_storage.py`, docs
