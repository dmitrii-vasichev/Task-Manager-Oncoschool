# Test Plan

## Task Labels

### Automated

- `cd backend && pytest tests/test_task_label_repository.py tests/test_task_label_api.py tests/test_task_label_task_api.py tests/test_task_permission_service.py tests/test_task_update_permissions.py -q`
- `cd backend && pytest -q`
- `cd frontend && npx tsc --noEmit`

### Manual

1. Open the Tasks page.
2. Create a label named `Conference` while creating a task.
3. Add `Conference` and `Partners` to one task.
4. Create another task with no labels.
5. Filter the task board by `Conference`.
6. Confirm the unlabeled task is hidden only while the filter is active.
7. Log in as a user with narrower department access.
8. Confirm the user does not see hidden tasks even when those tasks have matching labels.

