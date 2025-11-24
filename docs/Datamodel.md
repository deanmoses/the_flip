# Data Model

### Maintainer ([`Maintainer`](../the_flip/apps/accounts/models.py))
Person who performs work on the pinball machines. Linked to Django User account.

### Machine Model ([`MachineModel`](../the_flip/apps/catalog/models.py))
A model of pinball machine (e.g., "Star Trek", "Godzilla").

### Machine Instance ([`MachineInstance`](../the_flip/apps/catalog/models.py))
A specific physical machine in the museum (e.g., "Star Trek #12345").

### Problem Report ([`ProblemReport`](../the_flip/apps/maintenance/models.py))
Issue reported by museum visitor.

### Log Entry ([`LogEntry`](../the_flip/apps/maintenance/models.py))
Journal-type entry created by maintainers to document work on a machine.

### Log Entry Media ([`LogEntryMedia`](../the_flip/apps/maintenance/models.py))
Photos/videos attached to log entries.
