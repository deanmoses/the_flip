"""Environment and dependency tests for maintenance app."""

import shutil
import subprocess

from django.test import TestCase, tag


@tag("integration", "environment")
class FFmpegAvailabilityTest(TestCase):
    """Ensure ffmpeg/ffprobe are available for video processing."""

    def test_ffmpeg_available(self):
        if not shutil.which("ffmpeg"):
            self.fail("ffmpeg not found on PATH (video upload/transcode will fail)")
        result = subprocess.run(
            ["ffmpeg", "-version"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        self.assertIn("ffmpeg version", (result.stdout or "").lower())

    def test_ffprobe_available(self):
        if not shutil.which("ffprobe"):
            self.fail("ffprobe not found on PATH (video upload/transcode will fail)")
        result = subprocess.run(
            ["ffprobe", "-version"],
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        self.assertIn("ffprobe version", (result.stdout or "").lower())
