# Model Patterns

This documents the model conventions used in this project. These are choices we've made, not Django basics.

## TimeStampedMixin

All models that need timestamps inherit from `TimeStampedMixin`:

```python
from the_flip.apps.core.models import TimeStampedMixin

class MyModel(TimeStampedMixin):
    # Automatically has created_at and updated_at
    name = models.CharField(max_length=200)
```

We use a mixin (not a base class) to discourage adding unrelated behavior.

## Choice Fields

**Target pattern** (migration pending [#131](https://github.com/deanmoses/the_flip/issues/131)):

```python
class ProblemReport(TimeStampedMixin):
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CLOSED = "closed", "Closed"

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)

# Usage
if report.status == ProblemReport.Status.OPEN:
    ...
```

TextChoices provides type safety and IDE autocomplete. Current code uses class constants (`STATUS_OPEN = "open"`) which works but is less explicit.

## Field Nullability

**Strings** (CharField, TextField): Use `blank=True` only. Django stores empty strings, not NULL.

```python
description = models.TextField(blank=True)  # Stores "" when empty
```

**Non-strings** (ForeignKey, DateTimeField, IntegerField, FileField): Use both `blank=True, null=True`.

```python
problem_report = models.ForeignKey(..., null=True, blank=True)
work_date = models.DateTimeField(null=True, blank=True)
transcoded_file = models.FileField(blank=True, null=True)
```

Note: FileField standardization pending [#132](https://github.com/deanmoses/the_flip/issues/132).

## ForeignKey Relationships

Always specify `related_name` and choose `on_delete` deliberately:

```python
# CASCADE: Delete logs when machine is deleted
machine = models.ForeignKey(MachineInstance, on_delete=models.CASCADE, related_name="log_entries")

# SET_NULL: Keep report if user is deleted
reported_by_user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="problem_reports_created")

# PROTECT: Prevent deleting referenced data
requested_by = models.ForeignKey(Maintainer, on_delete=models.PROTECT, related_name="part_requests")
```

## Custom QuerySets

Encapsulate reusable queries in QuerySet classes instead of repeating filter logic in views:

```python
class PartRequestQuerySet(models.QuerySet):
    def active(self):
        """Return part requests that are not cancelled."""
        return self.exclude(status=PartRequest.STATUS_CANCELLED)

    def pending(self):
        """Return part requests that are requested or ordered."""
        return self.filter(status__in=[PartRequest.STATUS_REQUESTED, PartRequest.STATUS_ORDERED])

class PartRequest(TimeStampedMixin):
    objects = PartRequestQuerySet.as_manager()

# Usage - clean, chainable, tested once
PartRequest.objects.active().pending()

# Instead of repeating this in every view:
PartRequest.objects.exclude(status="cancelled").filter(status__in=["requested", "ordered"])
```

The project uses this pattern in:
- `MachineInstanceQuerySet` - `visible()`, `active_for_matching()`
- `ProblemReportQuerySet` - `open()`
- `PartRequestQuerySet` - `active()`, `pending()`

## Query Optimization

Use `select_related` for ForeignKey/OneToOne (single JOIN) and `prefetch_related` for reverse/ManyToMany (separate query):

```python
# From maintenance/views.py - actual project usage
LogEntry.objects.filter(machine=self.machine)
    .select_related("machine", "problem_report")
    .prefetch_related("maintainers__user", "media")
    .order_by("-work_date")
```

Add these in views or QuerySet methods where queries are built, not in model methods.

## Model Checklist

When creating or modifying models:

- [ ] Add `__str__` method for admin/debugging
- [ ] Use appropriate field types (CharField with max_length, TextField for long text)
- [ ] Add `db_index=True` on fields used in filters/ordering
- [ ] Add `Meta` class with `ordering`, `verbose_name` if needed
- [ ] Write migration and test it both ways (migrate/rollback)
