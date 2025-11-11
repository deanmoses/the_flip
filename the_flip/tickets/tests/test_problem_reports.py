from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse

from ..forms import ProblemReportCreateForm
from ..models import MachineModel, MachineInstance, Maintainer, ProblemReport


@override_settings(
    STORAGES={
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    }
)
class ReportCreateViewTests(TestCase):
    def setUp(self):
        cache.clear()
        # Create a machine model and instance
        self.model = MachineModel.objects.create(
            name='Test Game',
            manufacturer='Bally',
            year=1995,
            era=MachineModel.ERA_SS,
        )
        self.machine = MachineInstance.objects.create(
            model=self.model,
            location=MachineInstance.LOCATION_FLOOR,
            operational_status=MachineInstance.OPERATIONAL_STATUS_GOOD,
        )
        self.url = reverse('report_create')

    def _submission_payload(self, **overrides):
        payload = {
            'machine': self.machine.pk,
            'problem_type': ProblemReport.PROBLEM_STUCK_BALL,
            'problem_text': 'Ball stuck in left ramp.',
            'reported_by_name': 'Visitor',
            'reported_by_contact': 'visitor@example.com',
        }
        payload.update(overrides)
        return payload

    def test_anonymous_submission_records_ip(self):
        response = self.client.post(
            self.url,
            self._submission_payload(),
            HTTP_USER_AGENT='UnitTest/1.0',
            HTTP_X_FORWARDED_FOR='203.0.113.5',
        )
        self.assertEqual(response.status_code, 302)
        report = ProblemReport.objects.get()
        self.assertIsNone(report.reported_by_user)
        self.assertEqual(report.reported_by_name, 'Visitor')
        self.assertEqual(report.ip_address, '203.0.113.5')
        self.assertEqual(report.device_info, 'UnitTest/1.0')

    def test_authenticated_submission_records_user_and_contact(self):
        user = get_user_model().objects.create_user(
            username='maintainer',
            email='tech@example.com',
            password='pass1234',
            first_name='Tech',
            last_name='One',
        )
        Maintainer.objects.create(user=user, phone='555-1234')
        self.client.login(username='maintainer', password='pass1234')

        response = self.client.post(
            self.url,
            self._submission_payload(problem_text='Coil burnt out.'),
            REMOTE_ADDR='198.51.100.42',
        )
        self.assertEqual(response.status_code, 302)
        report = ProblemReport.objects.get()
        self.assertEqual(report.reported_by_user, user)
        self.assertEqual(report.reported_by_name, 'Tech One')
        self.assertEqual(report.reported_by_contact, 'tech@example.com')
        self.assertEqual(report.ip_address, '198.51.100.42')

    @override_settings(REPORT_SUBMISSION_RATE_LIMIT_MAX=2, REPORT_SUBMISSION_RATE_LIMIT_WINDOW_SECONDS=3600)
    def test_rate_limit_blocks_submissions_from_same_ip(self):
        payload = self._submission_payload(problem_text='Repeated issue.')
        headers = {'HTTP_X_FORWARDED_FOR': '203.0.113.8'}

        for _ in range(2):
            response = self.client.post(self.url, payload, **headers)
            self.assertEqual(response.status_code, 302)

        response = self.client.post(self.url, payload, **headers)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Too many problem reports from this device', status_code=200)
        self.assertEqual(ProblemReport.objects.count(), 2)


class ProblemReportFormMachineFilteringTests(TestCase):
    """Tests for machine filtering in ProblemReportCreateForm based on user authentication."""

    def setUp(self):
        # Create a machine model
        self.model = MachineModel.objects.create(
            name='Test Pinball',
            manufacturer='Williams',
            year=1992,
            era=MachineModel.ERA_SS,
        )

        # Create machines in different locations and statuses
        self.floor_good = MachineInstance.objects.create(
            model=self.model,
            name_override='Floor Good',
            location=MachineInstance.LOCATION_FLOOR,
            operational_status=MachineInstance.OPERATIONAL_STATUS_GOOD,
        )
        self.floor_broken = MachineInstance.objects.create(
            model=self.model,
            name_override='Floor Broken',
            location=MachineInstance.LOCATION_FLOOR,
            operational_status=MachineInstance.OPERATIONAL_STATUS_BROKEN,
        )
        self.workshop_good = MachineInstance.objects.create(
            model=self.model,
            name_override='Workshop Good',
            location=MachineInstance.LOCATION_WORKSHOP,
            operational_status=MachineInstance.OPERATIONAL_STATUS_GOOD,
        )
        self.workshop_broken = MachineInstance.objects.create(
            model=self.model,
            name_override='Workshop Broken',
            location=MachineInstance.LOCATION_WORKSHOP,
            operational_status=MachineInstance.OPERATIONAL_STATUS_BROKEN,
        )
        self.storage_good = MachineInstance.objects.create(
            model=self.model,
            name_override='Storage Good',
            location=MachineInstance.LOCATION_STORAGE,
            operational_status=MachineInstance.OPERATIONAL_STATUS_GOOD,
        )

        # Create a user for authenticated tests
        self.user = get_user_model().objects.create_user(
            username='testuser',
            password='testpass123'
        )

    def test_unauthenticated_user_sees_only_floor_machines(self):
        """Unauthenticated users should only see machines on the floor."""
        form = ProblemReportCreateForm(user=None)
        queryset = form.fields['machine'].queryset
        machine_ids = set(queryset.values_list('id', flat=True))

        # Should include both floor machines
        self.assertIn(self.floor_good.id, machine_ids)
        self.assertIn(self.floor_broken.id, machine_ids)

        # Should NOT include workshop or storage machines
        self.assertNotIn(self.workshop_good.id, machine_ids)
        self.assertNotIn(self.workshop_broken.id, machine_ids)
        self.assertNotIn(self.storage_good.id, machine_ids)

    def test_unauthenticated_user_sees_broken_machines_on_floor(self):
        """Unauthenticated users should see broken machines if they're on the floor."""
        form = ProblemReportCreateForm(user=None)
        queryset = form.fields['machine'].queryset
        machine_ids = set(queryset.values_list('id', flat=True))

        # Broken machine on floor should be visible
        self.assertIn(self.floor_broken.id, machine_ids)

    def test_authenticated_user_sees_all_machines(self):
        """Authenticated users should see machines in all locations."""
        form = ProblemReportCreateForm(user=self.user)
        queryset = form.fields['machine'].queryset
        machine_ids = set(queryset.values_list('id', flat=True))

        # Should include all machines regardless of location
        self.assertIn(self.floor_good.id, machine_ids)
        self.assertIn(self.floor_broken.id, machine_ids)
        self.assertIn(self.workshop_good.id, machine_ids)
        self.assertIn(self.workshop_broken.id, machine_ids)
        self.assertIn(self.storage_good.id, machine_ids)

    def test_authenticated_user_sees_broken_machines(self):
        """Authenticated users should see broken machines."""
        form = ProblemReportCreateForm(user=self.user)
        queryset = form.fields['machine'].queryset
        machine_ids = set(queryset.values_list('id', flat=True))

        # Should include broken machines
        self.assertIn(self.floor_broken.id, machine_ids)
        self.assertIn(self.workshop_broken.id, machine_ids)

    def test_qr_code_scenario_bypasses_filtering(self):
        """When machine is pre-selected via QR code, filtering doesn't apply."""
        # Workshop machine should be usable via QR code even for unauthenticated users
        form = ProblemReportCreateForm(machine=self.workshop_good, user=None)

        # Machine field should be hidden
        self.assertIsInstance(form.fields['machine'].widget, form.fields['machine'].hidden_widget().__class__)

        # Machine should be pre-selected
        self.assertEqual(form.fields['machine'].initial, self.workshop_good)


@override_settings(
    STORAGES={
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    }
)
class ReportListPrivacyTests(TestCase):
    """Tests to ensure public view doesn't expose personal data."""

    def setUp(self):
        cache.clear()
        # Create a machine model and instance
        self.model = MachineModel.objects.create(
            name='Test Game',
            manufacturer='Bally',
            year=1995,
            era=MachineModel.ERA_SS,
        )
        self.machine = MachineInstance.objects.create(
            model=self.model,
            location=MachineInstance.LOCATION_FLOOR,
            operational_status=MachineInstance.OPERATIONAL_STATUS_GOOD,
        )

        # Create a problem report with personal data
        self.report = ProblemReport.objects.create(
            machine=self.machine,
            problem_type=ProblemReport.PROBLEM_STUCK_BALL,
            problem_text='Ball stuck in left ramp.',
            reported_by_name='John Doe',
            reported_by_contact='john.doe@email.com',
            device_info='iPhone 13',
            ip_address='192.168.1.100',
        )

        self.url = reverse('report_list')

    def test_public_view_does_not_show_reporter_column(self):
        """Public (unauthenticated) view should not show Reporter column at all."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # Should not contain the Reporter column header
        # Note: We use a regex-like check - if "Reporter" appears as a header, it would be in <th>
        content = response.content.decode('utf-8')
        # Check that we don't have a Reporter header in the table
        self.assertNotIn('<th>Reporter</th>', content)

    def test_public_view_does_not_show_reporter_email(self):
        """Public view should not display reporter email."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # Should not contain the reporter's email
        self.assertNotContains(response, 'john.doe@email.com')

    def test_public_view_does_not_show_reporter_phone(self):
        """Public view should not display reporter phone."""
        # Create a report with phone number
        report_with_phone = ProblemReport.objects.create(
            machine=self.machine,
            problem_type=ProblemReport.PROBLEM_NO_CREDITS,
            problem_text='No credits showing.',
            reported_by_name='Jane Smith',
            reported_by_contact='415-555-1234',
        )

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # Should not contain the reporter's phone or name (entire Reporter column is hidden)
        self.assertNotContains(response, '415-555-1234')
        self.assertNotContains(response, 'Jane Smith')

    def test_public_view_does_not_show_device_info(self):
        """Public view should not display device/user agent info."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # Should not contain device info
        self.assertNotContains(response, 'iPhone 13')

    def test_public_view_does_not_show_ip_address(self):
        """Public view should not display IP address."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # Should not contain IP address
        self.assertNotContains(response, '192.168.1.100')

    def test_public_view_shows_machine_and_problem_info(self):
        """Public view should still show non-personal information."""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        # Should contain machine name and problem text (non-personal data)
        self.assertContains(response, 'Test Game')
        self.assertContains(response, 'Ball stuck in left ramp')
