from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import MachineModel, MachineInstance, Maintainer, ProblemReport


class MachineStatusReportIntegrationTests(TestCase):
    """Tests for machine status changes affecting problem reports."""

    def setUp(self):
        self.model = MachineModel.objects.create(
            name='Test Pinball',
            manufacturer='Test',
            year=1990,
            era=MachineModel.ERA_SS,
        )
        self.machine = MachineInstance.objects.create(
            model=self.model,
            location=MachineInstance.LOCATION_FLOOR,
            operational_status=MachineInstance.OPERATIONAL_STATUS_BROKEN,
        )
        self.user = get_user_model().objects.create_user(
            username='maintainer',
            password='testpass'
        )
        self.maintainer = Maintainer.objects.create(user=self.user)

        self.report = ProblemReport.objects.create(
            machine=self.machine,
            problem_type=ProblemReport.PROBLEM_OTHER,
            problem_text='Test problem',
            status=ProblemReport.STATUS_OPEN,
        )

    def test_setting_machine_good_closes_report(self):
        """Setting machine status to 'good' should close the report."""
        update = self.report.set_machine_status(
            MachineInstance.OPERATIONAL_STATUS_GOOD,
            self.maintainer,
            "Fixed!"
        )
        self.report.refresh_from_db()
        self.machine.refresh_from_db()

        self.assertEqual(self.report.status, ProblemReport.STATUS_CLOSED)
        self.assertEqual(self.machine.operational_status, MachineInstance.OPERATIONAL_STATUS_GOOD)
        self.assertEqual(update.status, ProblemReport.STATUS_CLOSED)
        self.assertEqual(update.machine_status, MachineInstance.OPERATIONAL_STATUS_GOOD)

    def test_setting_machine_broken_opens_report(self):
        """Setting machine status to 'broken' should open the report."""
        # First close the report
        self.report.status = ProblemReport.STATUS_CLOSED
        self.report.save()

        # Then set machine to broken
        update = self.report.set_machine_status(
            MachineInstance.OPERATIONAL_STATUS_BROKEN,
            self.maintainer,
            "Problem returned"
        )
        self.report.refresh_from_db()

        self.assertEqual(self.report.status, ProblemReport.STATUS_OPEN)
        self.assertEqual(update.status, ProblemReport.STATUS_OPEN)

    def test_setting_machine_fixing_opens_report(self):
        """Setting machine status to 'fixing' should keep/open the report."""
        self.report.status = ProblemReport.STATUS_CLOSED
        self.report.save()

        update = self.report.set_machine_status(
            MachineInstance.OPERATIONAL_STATUS_FIXING,
            self.maintainer,
            "Working on it"
        )
        self.report.refresh_from_db()

        self.assertEqual(self.report.status, ProblemReport.STATUS_OPEN)

    def test_setting_machine_unknown_does_not_change_report(self):
        """Setting machine status to 'unknown' should not change report status."""
        original_status = self.report.status

        update = self.report.set_machine_status(
            MachineInstance.OPERATIONAL_STATUS_UNKNOWN,
            self.maintainer,
            "Status unclear"
        )
        self.report.refresh_from_db()

        self.assertEqual(self.report.status, original_status)
