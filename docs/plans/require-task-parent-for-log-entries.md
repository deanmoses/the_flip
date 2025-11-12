# Require Task Parent for All Log Entries

## Overview

Eliminate standalone log entries from the system. All log entries must have a parent Task. This simplifies the data model and maintainer workflow - maintainers only need to look at one list (Tasks) rather than managing both tasks and standalone log entries.

## Motivation

- **Simpler data model**: No more optional task relationship on LogEntry
- **Simpler UI/UX**: Maintainers work with a single list of Tasks
- **Clearer semantics**: Every piece of maintenance work is tracked as a Task

## Database Changes

### LogEntry Model

Change `LogEntry.task` from nullable to required:

**Before:**
```python
task = models.ForeignKey(
    Task,
    on_delete=models.CASCADE,
    related_name="log_entries",
    null=True,  # ← Remove this
    blank=True,  # ← Remove this
)
```

**After:**
```python
task = models.ForeignKey(
    Task,
    on_delete=models.CASCADE,
    related_name="log_entries",
    null=False,  # ← Required
    blank=False,  # ← Required
)
```

Also update this help text on the `machine` field (no longer accurate):
```python
help_text="Machine this log entry is associated with (required for standalone logs)"
```

### No Migration Needed

Since we're deleting the database and starting fresh, no migration is required. Simply update the model code and recreate the database from scratch using `python manage.py migrate`.

## Import Script Changes

File: `the_flip/tickets/management/commands/import_legacy_maintenance_records.py`

### Change `import_log_entries()` Method

Currently creates standalone log entries. Change to create Tasks instead:

#### For Single Maintainer CSV Entries

Model behavior: User does work, then creates and closes task in one action.

1. Create Task:
   - `type='todo'`
   - `status='closed'`
   - `problem_text` = CSV "Notes" field (full text)
   - `reported_by_user` = matched maintainer User object (if found, else None)
   - `machine` = matched machine

2. Save and override timestamps:
   - `created_at` = parsed CSV Date
   - `closed_at` = parsed CSV Date (same as created_at)

3. **Do NOT create a child LogEntry**

#### For Multiple Maintainer CSV Entries

Model behavior: User creates task first, then later logs work with all maintainers.

1. Create Task:
   - `type='todo'`
   - `status='open'`
   - `problem_text` = CSV "Notes" field (full text)
   - `reported_by_user` = first maintainer from list (if found, else None)
   - `machine` = matched machine

2. Save and override `created_at`:
   - `created_at` = parsed CSV Date minus random offset (5-60 minutes)

3. Close the task via `task.set_status()`:
   ```python
   log_entry = task.set_status(
       Task.STATUS_CLOSED,
       maintainers=all_matched_maintainers,
       text=""
   )
   ```

4. Override log entry timestamp:
   - `log_entry.created_at` = parsed CSV Date (original timestamp)

### Random Time Offset

For multiple maintainer entries, generate a random offset between 5-60 minutes:

```python
import random

def random_task_creation_offset():
    """Generate random offset for when task was created before work was logged"""
    minutes = random.randint(5, 60)
    return timedelta(minutes=minutes)
```

Use this when setting `created_at` for tasks with multiple maintainers:
```python
task.created_at = parsed_csv_date - random_task_creation_offset()
```

## UI Changes

### Only Update Global Task Creation

**ONLY update** `/tasks/new/` (global todo creation); **do NOT update:**
- `/machines/{SLUG}/tasks/new/` (machine-specific task creation)
- Problem report creation
- Any other task creation flows

### Add "Create Closed" Checkbox

Add a checkbox next to the submit button:

**Desktop layout:**
```
[Submit Button] ☑ Create closed
```

**Mobile layout:**
```
☑ Create closed
[Submit Button]
```

The checkbox should:
- Label: "Create closed"
- Default: Unchecked
- Position: Immediately to the right of submit button on desktop
- Position: Flow above submit button on mobile

### Form Handling

When "Create closed" is checked:
1. Create Task with `status='closed'`
2. Set `closed_at = created_at` (same timestamp)
3. Do NOT create a child LogEntry

When unchecked (default):
- Create Task with `status='open'` as normal
- No `closed_at` set

### Implementation Details

**View changes** (`the_flip/tickets/views.py`):
- Add `create_closed` boolean field to form
- In form processing, check if `create_closed` is True
- If True, set `status='closed'` and `closed_at=timezone.now()` after saving

**Template changes** (`the_flip/tickets/templates/tickets/task_create.html`):
- Add checkbox input after submit button
- Add CSS to handle desktop/mobile layout differences

## Files to Change

1. **Models**: `the_flip/tickets/models.py`
   - Update `LogEntry.task` to required field
   - Remove obsolete help_text from `LogEntry.machine`

2. **Import script**: `the_flip/tickets/management/commands/import_legacy_maintenance_records.py`
   - Replace `import_log_entries()` implementation
   - Add `random_task_creation_offset()` helper

3. **Views**: `the_flip/tickets/views.py`
   - Update global task creation view
   - Add `create_closed` form field handling

4. **Template**: `the_flip/tickets/templates/tickets/task_create.html`
   - Add "Create closed" checkbox
   - Add responsive CSS for checkbox positioning

5. **Forms**: `the_flip/tickets/forms.py` (if using ModelForm)
   - Add `create_closed` field to form class

## Testing Plan

1. **Database integrity**: Verify LogEntry.task is required at DB level
2. **Import script**:
   - Test single maintainer CSV entries create closed tasks
   - Test multiple maintainer CSV entries create open tasks then close via LogEntry
   - Verify timestamps are correctly offset for multiple maintainer entries
3. **UI**:
   - Test creating task with "Create closed" checked
   - Test creating task with "Create closed" unchecked (default)
   - Verify checkbox layout on desktop and mobile
   - Verify `closed_at` is set correctly when creating closed

## Out of Scope

- Machine-specific task creation pages (keep existing behavior)
- Problem report creation (keep existing behavior)
- `create_sample_maintenance_data.py` (already doesn't create standalone log entries)
