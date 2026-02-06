"""Signals for maintenance app — cleans up RecordReference rows on source deletion."""

from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_delete
from django.dispatch import receiver

from the_flip.apps.core.models import RecordReference

from .models import LogEntry, ProblemReport


@receiver(post_delete, sender=ProblemReport)
@receiver(post_delete, sender=LogEntry)
def cleanup_maintenance_references(sender, instance, **kwargs):
    """Clean up RecordReference rows when a maintenance record is deleted."""
    ct = ContentType.objects.get_for_model(sender)
    RecordReference.objects.filter(source_type=ct, source_id=instance.pk).delete()
