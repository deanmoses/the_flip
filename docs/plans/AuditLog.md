# Audit Log Requirements

This document describes the requirements for audit logging and compares implementation options.

## Background

The museum director wants to track what volunteer maintainers are doing in the system. From [GitHub Issue #33](https://github.com/deanmoses/the_flip/issues/33):

> The museum director, William, tries to turn volunteers loose to do things, but he'd like to know what they did.

The audit trail should show:
 - who created/modified records
 - when
 - what was changed

---

## Requirements

### Works on Dev DB

The auditing package must work not only on Postgres but also on localhost dev SQLite databases.

### Revert / Restore

It would be nice to have the ability to click and restore a record to a previous point in time, all things being equal (they never are).

### Storage Impact

Audit logging must not meaningfully affect hosting  costs (the concern is that it might, due to increased database growth).

See database growth projections before this feature in [Hosting Requirements](./Hosting.md).

### Integration & Maintenance Costs

We want the integration and maintenance costs to be as low as possible.  Weight will be given to:
 - Least amount of custom code we must own (such as boilerplate code, custom diff viewers, etc)
 - Least number of migrations
 - Least amount of effort to audit each subsequent model

### Performance

We don't want this to affect the performance of writing data.  At least, weight will be given to packages that affect performance the least.

### Models to Audit

Audit models that can be created or modified by maintainers through the application:

| Model | Create | Update | Why Audit |
|-------|--------|--------|-----------|
| **ProblemReport** | Yes | Yes (status, description) | Track who reported problems and who closed them |
| **LogEntry** | Yes | Yes (text, work_date, maintainers) | Track who logged work and any corrections |
| **LogEntryMedia** | Yes | Yes (delete) | Track who uploaded/deleted photos and videos |
| **MachineInstance** | Yes | Yes (status, location, details) | Track status changes and location moves |
| **MachineModel** | Yes | Yes (name, manufacturer, etc.) | Track edits to machine catalog information |

### Models NOT to Audit

Do not audit models that are admin-only or cannot be changed by maintainers.  This includes:

| Model | Reason |
|-------|--------|
| Location | Admin-only; maintainers can only select existing locations |
| WebhookEndpoint | Admin-only; webhook configuration |
| WebhookSettings | Admin-only; singleton settings |
| Maintainer | Admin-only; user profile management |
| User | Admin-only; Django auth |
| Invitation | Admin-only; invitation management |

### Non-Requirements

- **SQL queries against historical data**: Not needed. We don't need to run aggregate queries like "how many status changes happened last month" against the audit tables.

---

## Package Comparison

Both packages are maintained by [Jazzband](https://jazzband.co/), a collaborative community for Django packages.

### Philosophy

**django-auditlog**: "What changed?" — Lightweight audit trail. Stores only the diff (changed fields as JSON) in a single table. Created explicitly as a lightweight alternative when full version control was "excessive and expensive."

**django-simple-history**: "What was the state?" — Full version control. Stores complete snapshots of each record in per-model history tables. Enables rollback and time-travel queries.

### Comparison

|  | **django-auditlog** | **django-simple-history** |
|---|---|---|
| [Supports PostgreSQL & SQLite](#storage-impact) | ✅ | ✅ |
| [No Increase in Hosting Cost](#storage-impact) | ✅ (~7MB over 3 years) | ✅ (~20MB over 3 years) |
| Write Performance | ✅ 1 INSERT + diff calculation | ✅ 1 INSERT (row copy) |
| Supports Rollback | ❌ | ✅ Built-in revert to any previous version |
| [Built-in Admin Diff View](#display) | ✅ Field/From/To table | ✅ Select two versions to compare |
| Model Changes Required | ❌ None (settings-based) | ✅ Add `history = HistoricalRecords()` to each model |
| Number of Migrations | 1 (single `auditlog_logentry` table) | 1 per tracked model (5 migrations for 5 models) |
| Settings Configuration | List models in `AUDITLOG_INCLUDE_TRACKING_MODELS` | Add to `INSTALLED_APPS` only |
| Admin Changes | Add `AuditlogHistoryAdminMixin` | Change base class to `SimpleHistoryAdmin` |
| [Template Code for Display](#display) | ~10 lines (iterate `changes_dict`) | ~12 lines (use `diff_against()`) |
| Ongoing Maintenance | Add model name to settings when adding new audited models | Add `history` field to new audited models |

### Storage Model

| Aspect | django-auditlog | django-simple-history |
|--------|-----------------|----------------------|
| **Table structure** | Single `auditlog_logentry` table for ALL models | Separate `_history` table per model |
| **What's stored** | JSON diff of changed fields only | Full snapshot of entire record |
| **Per-change size** | ~100-500 bytes | Full row size (varies by model) |
| **Query efficiency** | Generic foreign key (content_type + object_pk) | Direct foreign key to original model |

### Example: What Gets Stored

When a ProblemReport status changes from "open" to "closed":

**django-auditlog stores:**
```json
{"status": ["open", "closed"]}
```
Plus: actor, timestamp, action type

**django-simple-history stores:**
Full copy of the ProblemReport row (all fields), plus: `history_user`, `history_date`, `history_type`

---

## Recommendation

**TBD** — Pending decision on whether rollback capability is worth the per-model setup.

**If rollback is important:** django-simple-history
- Built-in revert functionality
- Time-travel queries (`as_of(datetime)`)
- Slightly more setup (one line per model)

**If rollback is not needed:** django-auditlog
- Zero model changes (settings-only configuration)
- Smaller storage footprint
- Simpler mental model (just diffs)
