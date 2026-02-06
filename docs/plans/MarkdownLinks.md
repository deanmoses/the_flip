# Markdown: Linking to Other Records

Status: IMPLEMENTED.

## Overview

All of Flipfix's various types of records -- Problem Reports, Log Entries, Parts Requests and soon the new [wiki docs](Wiki.md) -- support markdown. In that markdown, we'd like to be able to support linking from any type of record to any other type of record.

Examples:

- [Wiki docs](Wiki.md) should be able to contain links to other wiki docs.
- The repair guide wiki doc for the Blackout machine should link directly to the Blackout machine's detail page in Flipfix.
- A troubleshooting wiki doc should reference the specific problem reports that inspired it.
- A log entry should be able to reference the troubleshooting wiki doc that helped solve it.
- A log entry should be able to reference a part request that's holding up completion of the work.

The only markdown field this does NOT apply to is the public problem report submission form.

To make these easy to use, we want to type `[[` in any markdown field and get autocomplete for linking to any record in the system.

## The Link Syntax

Wiki-style double-bracket links provide a natural, readable syntax:

```markdown
See the [[machine:blackout]] repair history for context.

This was first reported in [[problem:142]].

Refer to [[page:guides/troubleshooting]] for the full procedure.
```

The format is `[[type:identifier]]` where:

- **type** indicates what kind of record you're linking to
- **identifier** is either a slug/path (for page, machine, model) or a numeric ID (for problem, log, etc.)

### Supported Link Types

| Type                | Example                               | Identifier Type   |
| ------------------- | ------------------------------------- | ----------------- |
| `page`              | `[[page:machines/blackout/system-6]]` | Path (tag + slug) |
| `machine`           | `[[machine:blackout]]`                | Slug              |
| `model`             | `[[model:black-knight]]`              | Slug              |
| `problem`           | `[[problem:142]]`                     | ID                |
| `log`               | `[[log:567]]`                         | ID                |
| `partrequest`       | `[[partrequest:89]]`                  | ID                |
| `partrequestupdate` | `[[partrequestupdate:234]]`           | ID                |

## Autocomplete

When a user types `[[` in any markdown textarea, a dropdown appears with a two-stage flow:

### Stage 1: Choose Link Type

```
┌────────────────────────────────────┐
│ Page                Link to a doc  │
│ Machine             Link to a...   │
│ Model               Link to a...   │
│ Problem Report      Link to a...   │
│ Log Entry           Link to a...   │
│ Part Request        Link to a...   │
│ Part Request Update Link to a...   │
└────────────────────────────────────┘
```

### Stage 2: Search and Select

After choosing a type, a search box appears. Results update as you type:

```
┌─────────────────────────────┐
│ Search machines...          │
├─────────────────────────────┤
│ Blackout                    │
│ Black Knight                │
│ Black Hole                  │
└─────────────────────────────┘
```

Selecting an item inserts the complete link syntax and closes the dropdown.

## Where Links Can Appear

Links can be authored in any markdown text field across Flipfix:

| Record Type         | Field(s)    |
| ------------------- | ----------- |
| Wiki Page           | Content     |
| Problem Report      | Description |
| Log Entry           | Notes       |
| Part Request        | Description |
| Part Request Update | Notes       |

This means a maintainer can write a problem report that references a wiki doc, or a log entry that links to the part request that resolved the issue.

## Toolbar

In v2 (_not_ v1), we will add simple toolbar above the textarea with a link button (can be expanded later for other actions).

When clicked, it inserts `[[` at the cursor position and the picker dialog appears, identical to manually typing `[[`. This:

- Makes the feature discoverable for new users
- Reuses the same component
- Teaches users the `[[` keyboard shortcut

## Reference Tracking

Beyond just rendering links, we track them in a database table. This enables several features:

### Preventing Broken Links

When deleting a wiki page, we can see which other pages still reference it, and warn the user.

### "What Links Here"

On any record's detail page, show all records that link to it:

> **What links here:**
>
> - [Blackout Repair Guide](page:machines/blackout/repairs) (wiki page)
> - [Problem #142: Flipper weak](problem:142) (problem report)

### "Related Records"

For records like part requests, show context about where they're referenced:

> **Related records:**
>
> - Log Entry #567 mentions this part request
> - Problem #142 links to this part request

## Data Model: The `RecordReference` Table

A single generic table tracks all references using Django's [contenttypes framework](https://docs.djangoproject.com/en/5.2/ref/contrib/contenttypes/). This provides automatic model discovery - adding a new model type requires no schema changes.

```python
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class RecordReference(models.Model):
    """Tracks links between records for 'what links here' queries."""

    # Source (the record containing the link)
    source_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="+"
    )
    source_id = models.PositiveBigIntegerField()
    source = GenericForeignKey("source_type", "source_id")

    # Target (the record being linked to)
    target_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, related_name="+"
    )
    target_id = models.PositiveBigIntegerField()
    target = GenericForeignKey("target_type", "target_id")

    class Meta:
        unique_together = [["source_type", "source_id", "target_type", "target_id"]]
        indexes = [
            models.Index(fields=["target_type", "target_id"]),  # "What links here"
            models.Index(fields=["source_type", "source_id"]),  # Cleanup on delete
        ]
```

Usage:

```python
from django.contrib.contenttypes.models import ContentType

# Creating a reference (using the GenericForeignKey accessor)
ref = RecordReference(source=page, target=machine)
ref.save()

# Or explicitly with ContentType
RecordReference.objects.create(
    source_type=ContentType.objects.get_for_model(page),
    source_id=page.id,
    target_type=ContentType.objects.get_for_model(machine),
    target_id=machine.id,
)

# "What links here" query
ct = ContentType.objects.get_for_model(MachineInstance)
refs = RecordReference.objects.filter(target_type=ct, target_id=machine.id)

# Access the actual objects (for display)
for ref in refs:
    print(ref.source)  # Returns the WikiPage, ProblemReport, etc.
```

**Note:** You cannot filter directly on `GenericForeignKey` fields (e.g., `filter(source=page)` won't work). Always filter on the underlying `source_type` + `source_id` fields. This is fine for our use case since we always query from a known object.

### Source Types vs Target Types

**Source types** are records that have markdown text fields where links can be authored:

- `page` (wiki pages)
- `problem` (problem reports)
- `log` (log entries)
- `partrequest` (part requests)
- `partrequestupdate` (part request updates)

**Target types** are records that can be linked to:

- All source types (you can link to a wiki page, problem report, etc.)
- Plus: `machine`, `model` (can be linked to but don't have link-containing text fields)

### Reference Syncing

When a record with markdown content is saved:

1. Parse all `[[type:identifier]]` links from the content
2. Extract the target record's ID (directly for ID-based types, via lookup for slug-based types)
3. Delete old references for this source
4. Create new references for current links

This happens automatically in the form's `save()` method.

## Authoring vs Storage Format

Slug-based types (`page`, `machine`, `model`) are converted to ID-based storage format so links survive renames. ID-based types are stored as-is.

**Authoring format** (what users see when editing any markdown field):

```markdown
See [[machine:blackout]] for repair history.
Refer to [[page:machines/blackout/repairs]] for the procedure.
This was reported in [[problem:142]].
```

**Storage format** (what's saved in the database):

```markdown
See [[machine:id:42]] for repair history.
Refer to [[page:id:17]] for the procedure.
This was reported in [[problem:142]].
```

| Link Type         | Authoring Format                     | Storage Format              |
| ----------------- | ------------------------------------ | --------------------------- |
| page              | `[[page:machines/blackout/repairs]]` | `[[page:id:17]]`            |
| machine           | `[[machine:blackout]]`               | `[[machine:id:42]]`         |
| model             | `[[model:black-knight]]`             | `[[model:id:15]]`           |
| problem           | `[[problem:142]]`                    | `[[problem:142]]`           |
| log               | `[[log:567]]`                        | `[[log:567]]`               |
| partrequest       | `[[partrequest:89]]`                 | `[[partrequest:89]]`        |
| partrequestupdate | `[[partrequestupdate:234]]`          | `[[partrequestupdate:234]]` |

**Why some types need `:id:` and others don't:**

- `page`, `machine`, and `model` use slugs/paths in authoring format. Since a machine could theoretically have slug `"42"`, the `:id:` prefix disambiguates IDs from slugs in storage.
- `problem`, `log`, `partrequest`, and `partrequestupdate` already use numeric IDs as their authoring identifier. There's no ambiguity, so authoring format = storage format. This also simplifies the code: no conversion needed on save/load for these types.

**Note on page links:** `[[page:id:N]]` stores the **WikiPageTag ID**, not the WikiPage ID. This is important because a WikiPage can appear in multiple locations (each with a different WikiPageTag). Using the WikiPageTag ID preserves which specific path was linked to. For example, if "System 6 Guide" appears at both `machines/blackout/system-6` and `guides/system-6`, linking to `[[page:machines/blackout/system-6]]` stores the WikiPageTag for that specific location, not the underlying page.

### Conversion Flow

Conversion only applies to slug-based types (`page`, `machine`, `model`). ID-based types (`problem`, `log`, `partrequest`, `partrequestupdate`) are stored exactly as authored.

**On save** (slug-based types only):

1. Parse `[[type:slug-or-path]]` links
2. Look up the record to get its ID
3. Replace with `[[type:id:N]]` format before storing

**On edit** (slug-based types only):

1. Parse `[[type:id:N]]` links from stored content
2. Look up the slug/path for each ID
3. Replace with authoring format for display

This conversion happens in the form layer.

## Technical Notes

### Autocomplete Cursor Position Calculation

The autocomplete dropdown needs to appear near the cursor position within the textarea. Since textareas don't expose cursor coordinates directly, we use the "mirror div" technique:

1. Create an invisible div with identical styling to the textarea
2. Copy text content up to cursor position
3. Add a marker span at the cursor position
4. Measure the marker's coordinates
5. Position the dropdown relative to those coordinates

### Autocomplete Keyboard Navigation

The autocomplete supports full keyboard navigation:

- Arrow keys to move between options
- Enter to select
- Escape to close
- Backspace to go back (from search to type selection)

The type selection stage and search results stage use separate keyboard handling to avoid conflicts.
