"""Tests for maintenance app API endpoints."""

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase, tag
from django.urls import reverse

from the_flip.apps.accounts.models import Maintainer
from the_flip.apps.catalog.models import MachineInstance, MachineModel
from the_flip.apps.maintenance.models import LogEntry

User = get_user_model()


@tag("api", "ajax")
class MaintainerAutocompleteViewTests(TestCase):
    """Tests for the maintainer autocomplete API endpoint."""

    def setUp(self):
        """Set up test data."""
        # Create regular maintainers
        self.user1 = User.objects.create_user(
            username="alice",
            first_name="Alice",
            last_name="Smith",
            password="testpass123",
            is_staff=True,
        )
        self.user2 = User.objects.create_user(
            username="bob",
            first_name="Bob",
            last_name="Jones",
            password="testpass123",
            is_staff=True,
        )
        # Create a shared account
        self.shared_user = User.objects.create_user(
            username="workshop-terminal",
            password="testpass123",
            is_staff=True,
        )
        shared_maintainer = Maintainer.objects.get(user=self.shared_user)
        shared_maintainer.is_shared_account = True
        shared_maintainer.save()

        self.autocomplete_url = reverse("api-maintainer-autocomplete")

    def test_requires_authentication(self):
        """Anonymous users should be redirected to login."""
        response = self.client.get(self.autocomplete_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_requires_staff_permission(self):
        """Non-staff users should be denied access."""
        User.objects.create_user(username="regular", password="testpass123", is_staff=False)
        self.client.login(username="regular", password="testpass123")
        response = self.client.get(self.autocomplete_url)
        self.assertEqual(response.status_code, 403)

    def test_returns_maintainers_list(self):
        """Should return a list of maintainers."""
        self.client.login(username="alice", password="testpass123")
        response = self.client.get(self.autocomplete_url)

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("maintainers", data)
        self.assertIsInstance(data["maintainers"], list)

    def test_excludes_shared_accounts(self):
        """Shared accounts should not appear in the autocomplete list."""
        self.client.login(username="alice", password="testpass123")
        response = self.client.get(self.autocomplete_url)

        data = response.json()
        display_names = [m["display_name"] for m in data["maintainers"]]
        usernames = [m["username"] for m in data["maintainers"]]

        self.assertIn("Alice Smith", display_names)
        self.assertIn("Bob Jones", display_names)
        self.assertNotIn("workshop-terminal", usernames)

    def test_filters_by_query(self):
        """Should filter results by query parameter."""
        self.client.login(username="alice", password="testpass123")
        response = self.client.get(self.autocomplete_url + "?q=alice")

        data = response.json()
        display_names = [m["display_name"] for m in data["maintainers"]]

        self.assertIn("Alice Smith", display_names)
        self.assertNotIn("Bob Jones", display_names)

    def test_case_insensitive_filter(self):
        """Query filtering should be case-insensitive."""
        self.client.login(username="alice", password="testpass123")
        response = self.client.get(self.autocomplete_url + "?q=ALICE")

        data = response.json()
        display_names = [m["display_name"] for m in data["maintainers"]]

        self.assertIn("Alice Smith", display_names)

    def test_returns_sorted_results(self):
        """Results should be sorted alphabetically by display name."""
        self.client.login(username="alice", password="testpass123")
        response = self.client.get(self.autocomplete_url)

        data = response.json()
        display_names = [m["display_name"] for m in data["maintainers"]]

        self.assertEqual(display_names, sorted(display_names, key=str.lower))


@tag("api")
class ReceiveTranscodedMediaViewTests(TestCase):
    """Tests for the HTTP API endpoint that receives transcoded media from worker service."""

    def setUp(self):
        """Set up test data for API endpoint tests."""

        from django.core.files.uploadedfile import SimpleUploadedFile

        from the_flip.apps.maintenance.models import LogEntry, LogEntryMedia

        # Create machine and log entry
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
            text="Test log entry",
        )

        # Create original media record with a fake video file
        original_file = SimpleUploadedFile(
            "original.mp4", b"fake video content", content_type="video/mp4"
        )
        self.media = LogEntryMedia.objects.create(
            log_entry=self.log_entry,
            media_type=LogEntryMedia.TYPE_VIDEO,
            file=original_file,
            transcode_status=LogEntryMedia.STATUS_PROCESSING,
        )

        # Set up test token
        self.test_token = "test-secret-token-12345"  # noqa: S105
        settings.TRANSCODING_UPLOAD_TOKEN = self.test_token

        self.upload_url = reverse("api-transcoding-upload")

    def tearDown(self):
        """Clean up after tests."""
        # Reset settings
        settings.TRANSCODING_UPLOAD_TOKEN = None

    def test_requires_authorization_header(self):
        """Request without Authorization header should be rejected."""
        response = self.client.post(self.upload_url, {})
        self.assertEqual(response.status_code, 401)
        self.assertIn("Missing or invalid Authorization header", response.json()["error"])

    def test_rejects_invalid_token(self):
        """Request with wrong token should be rejected."""
        response = self.client.post(
            self.upload_url,
            {},
            HTTP_AUTHORIZATION="Bearer wrong-token",
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn("Invalid authentication token", response.json()["error"])

    def test_requires_log_entry_media_id(self):
        """Request without log_entry_media_id should be rejected."""
        response = self.client.post(
            self.upload_url,
            {},
            HTTP_AUTHORIZATION=f"Bearer {self.test_token}",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing log_entry_media_id", response.json()["error"])

    def test_requires_video_file(self):
        """Request without video_file should be rejected."""
        response = self.client.post(
            self.upload_url,
            {"log_entry_media_id": str(self.media.id)},
            HTTP_AUTHORIZATION=f"Bearer {self.test_token}",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Missing video_file", response.json()["error"])

    def test_validates_video_file_type(self):
        """Video file must have video/* content type."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        wrong_file = SimpleUploadedFile("fake.txt", b"not a video", content_type="text/plain")
        response = self.client.post(
            self.upload_url,
            {
                "log_entry_media_id": str(self.media.id),
                "video_file": wrong_file,
            },
            HTTP_AUTHORIZATION=f"Bearer {self.test_token}",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid video file type", response.json()["error"])

    def test_validates_poster_file_type_if_provided(self):
        """Poster file must have image/* content type if provided."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        video_file = SimpleUploadedFile("video.mp4", b"fake video", content_type="video/mp4")
        wrong_poster = SimpleUploadedFile("poster.txt", b"not an image", content_type="text/plain")

        response = self.client.post(
            self.upload_url,
            {
                "log_entry_media_id": str(self.media.id),
                "video_file": video_file,
                "poster_file": wrong_poster,
            },
            HTTP_AUTHORIZATION=f"Bearer {self.test_token}",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid poster file type", response.json()["error"])

    def test_rejects_nonexistent_media_id(self):
        """Request with non-existent media ID should be rejected."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        video_file = SimpleUploadedFile("video.mp4", b"fake video", content_type="video/mp4")
        response = self.client.post(
            self.upload_url,
            {
                "log_entry_media_id": "999999",
                "video_file": video_file,
            },
            HTTP_AUTHORIZATION=f"Bearer {self.test_token}",
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.json()["error"])

    def test_successful_upload_with_video_and_poster(self):
        """Successful upload should save files and update status."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        from the_flip.apps.maintenance.models import LogEntryMedia

        video_file = SimpleUploadedFile(
            "transcoded.mp4", b"transcoded video content", content_type="video/mp4"
        )
        poster_file = SimpleUploadedFile(
            "poster.jpg", b"poster image content", content_type="image/jpeg"
        )

        response = self.client.post(
            self.upload_url,
            {
                "log_entry_media_id": str(self.media.id),
                "video_file": video_file,
                "poster_file": poster_file,
            },
            HTTP_AUTHORIZATION=f"Bearer {self.test_token}",
        )

        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result["success"])
        self.assertIn("successfully", result["message"].lower())

        # Verify media record was updated
        self.media.refresh_from_db()
        self.assertEqual(self.media.transcode_status, LogEntryMedia.STATUS_READY)
        self.assertTrue(self.media.transcoded_file)
        self.assertTrue(self.media.poster_file)
        # Original file should be deleted
        self.assertFalse(self.media.file)

    def test_successful_upload_without_poster(self):
        """Upload can succeed with video only (poster optional)."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        from the_flip.apps.maintenance.models import LogEntryMedia

        video_file = SimpleUploadedFile(
            "transcoded.mp4", b"transcoded video content", content_type="video/mp4"
        )

        response = self.client.post(
            self.upload_url,
            {
                "log_entry_media_id": str(self.media.id),
                "video_file": video_file,
            },
            HTTP_AUTHORIZATION=f"Bearer {self.test_token}",
        )

        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result["success"])

        # Verify media record was updated
        self.media.refresh_from_db()
        self.assertEqual(self.media.transcode_status, LogEntryMedia.STATUS_READY)
        self.assertTrue(self.media.transcoded_file)
        self.assertFalse(self.media.poster_file)  # No poster uploaded

    def test_server_not_configured_for_uploads(self):
        """If TRANSCODING_UPLOAD_TOKEN is not set, should return 500."""
        settings.TRANSCODING_UPLOAD_TOKEN = None

        response = self.client.post(
            self.upload_url,
            {},
            HTTP_AUTHORIZATION="Bearer some-token",
        )
        self.assertEqual(response.status_code, 500)
        self.assertIn("Server not configured", response.json()["error"])
