"""Tests for log entry views and functionality."""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, tag
from django.urls import reverse
from django.utils import timezone

from the_flip.apps.accounts.models import Maintainer
from the_flip.apps.catalog.models import MachineInstance, MachineModel
from the_flip.apps.maintenance.forms import LogEntryQuickForm
from the_flip.apps.maintenance.models import LogEntry

User = get_user_model()


@tag("models")
class LogEntryWorkDateTests(TestCase):
    """Tests for LogEntry work_date field."""

    def setUp(self):
        """Set up test data."""
        self.machine_model = MachineModel.objects.create(
            name="Test Machine",
            manufacturer="Test Mfg",
            year=2020,
            era=MachineModel.ERA_SS,
        )
        self.machine = MachineInstance.objects.create(
            model=self.machine_model,
            slug="test-machine",
            operational_status=MachineInstance.STATUS_GOOD,
        )

    def test_work_date_defaults_to_now(self):
        """LogEntry work_date should default to current time."""
        before = timezone.now()
        log_entry = LogEntry.objects.create(
            machine=self.machine,
            text="Test entry",
        )
        after = timezone.now()

        self.assertIsNotNone(log_entry.work_date)
        self.assertGreaterEqual(log_entry.work_date, before)
        self.assertLessEqual(log_entry.work_date, after)

    def test_work_date_can_be_set_explicitly(self):
        """LogEntry work_date can be set to a specific datetime."""
        specific_date = timezone.now() - timedelta(days=5)
        log_entry = LogEntry.objects.create(
            machine=self.machine,
            text="Historical entry",
            work_date=specific_date,
        )

        self.assertEqual(log_entry.work_date, specific_date)

    def test_log_entries_ordered_by_work_date_descending(self):
        """LogEntry queryset should be ordered by work_date descending."""
        old_entry = LogEntry.objects.create(
            machine=self.machine,
            text="Old entry",
            work_date=timezone.now() - timedelta(days=10),
        )
        new_entry = LogEntry.objects.create(
            machine=self.machine,
            text="New entry",
            work_date=timezone.now(),
        )

        entries = list(LogEntry.objects.all())
        self.assertEqual(entries[0], new_entry)
        self.assertEqual(entries[1], old_entry)


@tag("forms")
class LogEntryQuickFormWorkDateTests(TestCase):
    """Tests for LogEntryQuickForm work_date validation."""

    def test_form_valid_with_past_date(self):
        """Form should be valid with a past work_date."""
        past_date = timezone.now() - timedelta(days=5)
        form_data = {
            "work_date": past_date.strftime("%Y-%m-%dT%H:%M"),
            "submitter_name": "Test User",
            "text": "Test description",
        }
        form = LogEntryQuickForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_valid_with_today(self):
        """Form should be valid with today's date."""
        today = timezone.localtime().replace(hour=12, minute=0, second=0, microsecond=0)
        form_data = {
            "work_date": today.strftime("%Y-%m-%dT%H:%M"),
            "submitter_name": "Test User",
            "text": "Test description",
        }
        form = LogEntryQuickForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_form_invalid_with_future_date(self):
        """Form should be invalid with a future work_date."""
        future_date = timezone.now() + timedelta(days=5)
        form_data = {
            "work_date": future_date.strftime("%Y-%m-%dT%H:%M"),
            "submitter_name": "Test User",
            "text": "Test description",
        }
        form = LogEntryQuickForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("work_date", form.errors)
        self.assertIn("future", form.errors["work_date"][0].lower())


@tag("views")
class MachineLogCreateViewWorkDateTests(TestCase):
    """Tests for MachineLogCreateView work_date handling."""

    def setUp(self):
        """Set up test data."""
        self.machine_model = MachineModel.objects.create(
            name="Test Machine",
            manufacturer="Test Mfg",
            year=2020,
            era=MachineModel.ERA_SS,
        )
        self.machine = MachineInstance.objects.create(
            model=self.machine_model,
            slug="test-machine",
            operational_status=MachineInstance.STATUS_GOOD,
        )
        self.staff_user = User.objects.create_user(
            username="staffuser",
            password="testpass123",
            is_staff=True,
        )
        self.create_url = reverse("log-create-machine", kwargs={"slug": self.machine.slug})

    def test_create_log_entry_with_work_date(self):
        """Creating a log entry should save the work_date."""
        self.client.login(username="staffuser", password="testpass123")

        work_date = timezone.now() - timedelta(days=3)
        response = self.client.post(
            self.create_url,
            {
                "work_date": work_date.strftime("%Y-%m-%dT%H:%M"),
                "submitter_name": "Test User",
                "text": "Work performed three days ago",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(LogEntry.objects.count(), 1)

        log_entry = LogEntry.objects.first()
        # Compare dates (ignoring seconds since form doesn't capture them)
        self.assertEqual(
            log_entry.work_date.strftime("%Y-%m-%d %H:%M"),
            work_date.strftime("%Y-%m-%d %H:%M"),
        )

    def test_create_log_entry_rejects_future_date(self):
        """Creating a log entry with future date should fail validation."""
        self.client.login(username="staffuser", password="testpass123")

        future_date = timezone.now() + timedelta(days=5)
        response = self.client.post(
            self.create_url,
            {
                "work_date": future_date.strftime("%Y-%m-%dT%H:%M"),
                "submitter_name": "Test User",
                "text": "Future work",
            },
        )

        # Should re-render form with errors (200), not redirect
        self.assertEqual(response.status_code, 200)
        self.assertEqual(LogEntry.objects.count(), 0)


@tag("views", "ajax")
class LogEntryDetailViewWorkDateTests(TestCase):
    """Tests for LogEntryDetailView work_date AJAX update."""

    def setUp(self):
        """Set up test data."""
        self.machine_model = MachineModel.objects.create(
            name="Test Machine",
            manufacturer="Test Mfg",
            year=2020,
            era=MachineModel.ERA_SS,
        )
        self.machine = MachineInstance.objects.create(
            model=self.machine_model,
            slug="test-machine",
            operational_status=MachineInstance.STATUS_GOOD,
        )
        self.log_entry = LogEntry.objects.create(
            machine=self.machine,
            text="Test entry",
        )
        self.staff_user = User.objects.create_user(
            username="staffuser",
            password="testpass123",
            is_staff=True,
        )
        self.detail_url = reverse("log-detail", kwargs={"pk": self.log_entry.pk})

    def test_update_work_date_ajax(self):
        """AJAX update_work_date action should update the work_date."""
        self.client.login(username="staffuser", password="testpass123")

        new_date = timezone.now() - timedelta(days=7)
        response = self.client.post(
            self.detail_url,
            {
                "action": "update_work_date",
                "work_date": new_date.strftime("%Y-%m-%dT%H:%M"),
            },
        )

        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result["success"])

        self.log_entry.refresh_from_db()
        self.assertEqual(
            self.log_entry.work_date.strftime("%Y-%m-%d %H:%M"),
            new_date.strftime("%Y-%m-%d %H:%M"),
        )

    def test_update_work_date_rejects_future(self):
        """AJAX update_work_date should reject future dates."""
        self.client.login(username="staffuser", password="testpass123")

        future_date = timezone.now() + timedelta(days=5)
        response = self.client.post(
            self.detail_url,
            {
                "action": "update_work_date",
                "work_date": future_date.strftime("%Y-%m-%dT%H:%M"),
            },
        )

        self.assertEqual(response.status_code, 400)
        result = response.json()
        self.assertFalse(result["success"])
        self.assertIn("future", result["error"].lower())

    def test_update_work_date_rejects_invalid_format(self):
        """AJAX update_work_date should reject invalid date formats."""
        self.client.login(username="staffuser", password="testpass123")

        response = self.client.post(
            self.detail_url,
            {
                "action": "update_work_date",
                "work_date": "not-a-valid-date",
            },
        )

        self.assertEqual(response.status_code, 400)
        result = response.json()
        self.assertFalse(result["success"])
        self.assertIn("Invalid date format", result["error"])

    def test_update_work_date_rejects_empty(self):
        """AJAX update_work_date should reject empty date."""
        self.client.login(username="staffuser", password="testpass123")

        response = self.client.post(
            self.detail_url,
            {
                "action": "update_work_date",
                "work_date": "",
            },
        )

        self.assertEqual(response.status_code, 400)
        result = response.json()
        self.assertFalse(result["success"])


@tag("models")
class LogEntryCreatedByTests(TestCase):
    """Tests for LogEntry created_by field."""

    def setUp(self):
        """Set up test data."""
        self.machine_model = MachineModel.objects.create(
            name="Test Machine",
            manufacturer="Test Mfg",
            year=2020,
            era=MachineModel.ERA_SS,
        )
        self.machine = MachineInstance.objects.create(
            model=self.machine_model,
            slug="test-machine",
            operational_status=MachineInstance.STATUS_GOOD,
        )
        self.staff_user = User.objects.create_user(
            username="staffuser",
            password="testpass123",
            is_staff=True,
        )
        self.create_url = reverse("log-create-machine", kwargs={"slug": self.machine.slug})

    def test_created_by_set_when_creating_log_entry(self):
        """Creating a log entry should set the created_by field."""
        self.client.login(username="staffuser", password="testpass123")

        response = self.client.post(
            self.create_url,
            {
                "work_date": timezone.now().strftime("%Y-%m-%dT%H:%M"),
                "submitter_name": "Some Other Person",
                "text": "Work performed",
            },
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(LogEntry.objects.count(), 1)

        log_entry = LogEntry.objects.first()
        self.assertEqual(log_entry.created_by, self.staff_user)

    def test_created_by_can_differ_from_maintainer(self):
        """created_by (who entered data) can be different from maintainer (who did work)."""
        # Create another maintainer who did the work
        work_doer = User.objects.create_user(
            username="workdoer",
            first_name="Work",
            last_name="Doer",
            password="testpass123",
            is_staff=True,
        )

        self.client.login(username="staffuser", password="testpass123")

        response = self.client.post(
            self.create_url,
            {
                "work_date": timezone.now().strftime("%Y-%m-%dT%H:%M"),
                "submitter_name": "Work Doer",  # Name of who did the work
                "text": "Work performed by someone else",
            },
        )

        self.assertEqual(response.status_code, 302)
        log_entry = LogEntry.objects.first()

        # created_by is the logged-in user (who entered the data)
        self.assertEqual(log_entry.created_by, self.staff_user)

        # maintainers is who did the actual work
        self.assertIn(Maintainer.objects.get(user=work_doer), log_entry.maintainers.all())
