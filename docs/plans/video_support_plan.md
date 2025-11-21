# Video Uploads with RQ (Render & Railway)

## Goals
- Accept phone-recorded videos (MOV/HEVC/etc.) and transcode to widely playable H.264/AAC MP4.
- Generate a poster image for UI display.
- Keep uploads responsive by offloading transcode to an RQ worker.
- Deployable on Render and Railway without custom Dockerfiles.

## Requirements
- **Redis** for RQ queue.
- **RQ** Python package (worker + scheduler optional).
- **FFmpeg** available at runtime for transcode/poster extraction.
- **Storage** headroom for originals + MP4s + posters (consider pruning originals after success).

## App Changes (code-level)
- **Dependencies**: add `rq`, `rq-scheduler` (if periodic), and ensure FFmpeg is present.
- **Settings**: `RQ_REDIS_URL` (from env), job timeouts/concurrency defaults.
- **Models**: extend `LogEntryMedia` for videos: fields for `transcoded_file`, `poster_file`, `duration`, `width`, `height`, `transcode_status` (pending/processing/ready/failed), maybe `original_kept` flag.
- **Tasks**:
  - Enqueue on upload: `enqueue(transcode_video, media_id)`.
  - `transcode_video`: run FFmpeg to H.264/AAC MP4, cap long side at 2400px and constrain bitrate, extract poster (JPEG), store metadata, mark status.
  - Cleanup task to delete originals after successful transcode.
- **Validation**: server-side size limit (e.g., 200–500 MB), allowed MIME/ext for video; client hint via `accept="video/*"`.
- **UI**: render videos with `<video controls poster="...">` once ready; show “processing” status for pending/processing; surface errors if failed.

## Deploy: Render (YAML-driven)
- Add Redis service in `render.yaml`:
  ```yaml
  - type: redis
    name: the-flip-redis
  ```
- FFmpeg: add to `buildCommand` (or shared script):
  ```yaml
  buildCommand: |
    apt-get update
    apt-get install -y ffmpeg
    ./build.sh
  ```
- Worker service for RQ:
  ```yaml
  - type: worker
    name: the-flip-rq-worker
    runtime: python
    buildCommand: "<same as web>"
    startCommand: "rq worker --url $REDIS_URL default"
    envVars:
      - key: REDIS_URL
        fromService: the-flip-redis
  ```
- (Optional) Scheduler:
  ```yaml
  - type: worker
    name: the-flip-rq-scheduler
    runtime: python
    buildCommand: "<same as web>"
    startCommand: "rqscheduler --url $REDIS_URL"
    envVars:
      - key: REDIS_URL
        fromService: the-flip-redis
  ```
- Web service: keep existing, add `REDIS_URL` env from Redis service.

## Deploy: Railway (manual Redis provision)
- Provision Redis via UI/CLI (`railway add redis`); note the connection URL.
- FFmpeg: add to `nixpacks.toml`:
  ```toml
  [phases.setup]
  aptPkgs = ["libheif1", "libheif-dev", "ffmpeg"]
  ```
- Worker service (new Railway service) using same repo:
  - Build: reuse `build.sh`.
  - Start command: `rq worker --url $REDIS_URL default`.
  - Env: set `REDIS_URL` from the Redis plugin variable.
- (Optional) Scheduler service: `rqscheduler --url $REDIS_URL`.
- Web service: add `REDIS_URL` env var.

## FFmpeg Commands

### Video Transcode (Complete Command)
```bash
ffmpeg -i "$INPUT" \
  -vf "scale=min(iw\\,2400):min(ih\\,2400):force_original_aspect_ratio=decrease" \
  -c:v libx264 \
  -pix_fmt yuv420p \
  -profile:v main \
  -crf 23 \
  -preset medium \
  -c:a aac \
  -b:a 128k \
  -movflags +faststart \
  -y \
  "$OUTPUT.mp4"
```

### Poster Extraction
```bash
ffmpeg -i "$INPUT" \
  -vf "thumbnail,scale=320:-2" \
  -frames:v 1 \
  -y \
  "$OUTPUT.jpg"
```

### Critical FFmpeg Parameters Explained

**Video Processing:**
- `-vf "scale=min(iw\,2400):min(ih\,2400):force_original_aspect_ratio=decrease"`: Resize down so the long side is max 2400px; never upscale; preserves aspect ratio and keeps dimensions even for H.264
- `-c:v libx264`: H.264 video codec (universal browser support vs HEVC/H.265)
- `-pix_fmt yuv420p`: **CRITICAL** - Pixel format required for iOS Safari playback (without this, videos won't play on iPhones)
- `-profile:v main`: H.264 main profile (good compatibility balance vs high/baseline profiles)
- `-crf 23`: Constant Rate Factor for quality (18-28 range; lower=better quality, 23 is recommended default)
- `-preset medium`: Encoding speed vs compression efficiency (faster/medium/slow/slower)

**Audio Processing:**
- `-c:a aac`: AAC audio codec (universal browser support)
- `-b:a 128k`: Audio bitrate (128 kbps is good quality for speech/music)

**Streaming Optimization:**
- `-movflags +faststart`: **CRITICAL** - Moves metadata to file start, enables progressive streaming (without this, entire video must download before playback starts)

**Poster Extraction:**
- `thumbnail` filter: Analyzes video to pick a visually interesting frame (better than arbitrary timestamp)
- `scale=320:-2`: Resize poster to 320px width, maintain aspect ratio with even height

### Why These Settings Matter

**Without `-pix_fmt yuv420p`**: Videos will not play on iOS Safari (most phone users!)

**Without `-movflags +faststart`**: Poor user experience - users must wait for entire download before watching

**HEVC/H.265 Problem**: Modern iPhones record in HEVC by default, but browser support is limited (~70% of browsers). Converting to H.264 ensures universal playback.

## Implementation Phases

### Phase 1: Database Schema
**File:** `the_flip/apps/maintenance/models.py`

Add to `LogEntryMedia` model:
```python
transcoded_file = models.FileField(upload_to=..., blank=True, null=True)
poster_file = models.ImageField(upload_to=..., blank=True, null=True)
transcode_status = models.CharField(
    max_length=20,
    choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('ready', 'Ready'),
        ('failed', 'Failed'),
    ],
    default='pending',
    blank=True,
)
duration = models.IntegerField(null=True, blank=True, help_text="Duration in seconds")
original_width = models.IntegerField(null=True, blank=True)
original_height = models.IntegerField(null=True, blank=True)
original_kept = models.BooleanField(default=True, help_text="Whether original file is retained")
```

Create and run migration: `python manage.py makemigrations && python manage.py migrate`

### Phase 2: Dependencies & Settings
**File:** `requirements.txt`
```
rq==1.16.2
rq-scheduler==0.13.1  # Optional, for cleanup jobs
```

**File:** `the_flip/settings/base.py`
```python
import os

# RQ Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
RQ_QUEUES = {
    'default': {
        'URL': REDIS_URL,
        'DEFAULT_TIMEOUT': 600,  # 10 minutes for video processing
    }
}
```

**File:** `the_flip/settings/prod.py`
```python
import os

# Override for production
if 'REDIS_URL' in os.environ:
    REDIS_URL = os.environ['REDIS_URL']
# RQ_QUEUES picks up REDIS_URL from base
```

### Phase 3: Video Processing Backend
**File:** `the_flip/apps/maintenance/video_utils.py` (new file)

Create utilities:
- `get_video_info(file_path)`: Use ffprobe to extract codec, dimensions, duration
- `transcode_video(input_path, output_path, max_dimension=2400)`: Run FFmpeg transcode
- `generate_poster(video_path, output_path)`: Extract poster frame
- Helper: `is_hevc(file_path)`: Check if video needs conversion

**File:** `the_flip/apps/maintenance/tasks.py` (new file)

Create RQ job:
```python
from rq import get_current_job
from rq.job import Job
import logging

logger = logging.getLogger(__name__)

def transcode_video_job(media_id):
    """
    RQ job to transcode uploaded video.
    Updates LogEntryMedia.transcode_status throughout process.
    """
    try:
        media = LogEntryMedia.objects.get(id=media_id)
        media.transcode_status = 'processing'
        media.save()

        # Get video info
        info = get_video_info(media.file.path)
        media.duration = info['duration']
        media.original_width = info['width']
        media.original_height = info['height']
        media.save()

        # Transcode video
        transcoded_path = transcode_video(media.file.path)
        media.transcoded_file.save(
            f"transcoded_{media.file.name}",
            File(open(transcoded_path, 'rb')),
            save=False
        )

        # Generate poster
        poster_path = generate_poster(transcoded_path)
        media.poster_file.save(
            f"poster_{media.id}.jpg",
            File(open(poster_path, 'rb')),
            save=False
        )

        media.transcode_status = 'ready'
        media.save()

        logger.info(f"Successfully transcoded video {media_id}")

    except LogEntryMedia.DoesNotExist:
        logger.error(f"Media {media_id} not found for transcode job")
        return
    except Exception as e:
        logger.error(f"Failed to transcode video {media_id}: {e}", exc_info=True)
        media.transcode_status = 'failed'
        media.save(update_fields=["transcode_status"])
        raise
```

### Phase 4: Upload Flow
**File:** `the_flip/apps/maintenance/forms.py`

Update form field:
```python
media = forms.FileField(
    label="Photo or Video",
    required=False,
    widget=forms.ClearableFileInput(attrs={
        "accept": "image/*,video/*,.heic,.heif"
    }),
)
```

Add validation method:
```python
def clean_media(self):
    media = self.cleaned_data.get('media')
    if media:
        # Check file size (200MB max)
        if media.size > 200 * 1024 * 1024:
            raise ValidationError("File too large. Maximum size is 200MB.")

        # Validate content type
        content_type = media.content_type
        if not (content_type.startswith('image/') or content_type.startswith('video/')):
            raise ValidationError("Only images and videos are allowed.")

    return media
```

**File:** `the_flip/apps/maintenance/views.py`

Update create view to enqueue job:
```python
from rq import Queue
from redis import Redis
from django.conf import settings

def form_valid(self, form):
    # ... existing code ...

    if media_file:
        # Detect if video
        is_video = media_file.content_type.startswith('video/')

        media = LogEntryMedia.objects.create(
            log_entry=log_entry,
            file=media_file,
            media_type=LogEntryMedia.TYPE_VIDEO if is_video else LogEntryMedia.TYPE_PHOTO,
        )

        if is_video:
            # Enqueue transcode job
            redis_url = settings.RQ_QUEUES['default']['URL']
            redis_conn = Redis.from_url(redis_url)
            queue = Queue('default', connection=redis_conn, default_timeout=settings.RQ_QUEUES['default']['DEFAULT_TIMEOUT'])
            queue.enqueue('the_flip.apps.maintenance.tasks.transcode_video_job', media.id)

    # ... rest of method ...
```

### Phase 5: UI Templates
**File:** `the_flip/apps/maintenance/templates/maintenance/log_entry_detail.html`

Update media display:
```django
{% if media.media_type == 'video' %}
    {% if media.transcode_status == 'ready' %}
        <video controls poster="{{ media.poster_file.url }}" style="max-width: 100%;">
            <source src="{{ media.transcoded_file.url }}" type="video/mp4">
            Your browser doesn't support video playback.
        </video>
        {% if media.duration %}
            <p class="text-muted">Duration: {{ media.duration|format_duration }}</p>
        {% endif %}
    {% elif media.transcode_status == 'processing' or media.transcode_status == 'pending' %}
        <div class="alert alert-info">
            <i class="spinner-border spinner-border-sm"></i>
            Processing video... This may take a few minutes.
        </div>
    {% elif media.transcode_status == 'failed' %}
        <div class="alert alert-danger">
            Video processing failed.
            <a href="{% url 'retry_transcode' media.id %}" class="btn btn-sm btn-primary">Retry</a>
        </div>
    {% endif %}
{% else %}
    <img src="{{ media.file.url }}" alt="Log entry photo" style="max-width: 100%;">
{% endif %}
```

Add template filter for duration formatting:
```python
# the_flip/apps/maintenance/templatetags/media_filters.py
@register.filter
def format_duration(seconds):
    """Format seconds as MM:SS"""
    if not seconds:
        return ""
    minutes = seconds // 60
    secs = seconds % 60
    return f"{minutes}:{secs:02d}"
```

### Phase 6: Management Commands
**File:** `the_flip/apps/maintenance/management/commands/check_ffmpeg.py` (new)

Create command to verify FFmpeg availability:
```python
from django.core.management.base import BaseCommand
import subprocess

class Command(BaseCommand):
    help = 'Check FFmpeg availability and version'

    def handle(self, *args, **options):
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                check=True
            )
            self.stdout.write(self.style.SUCCESS('✓ FFmpeg is available'))
            self.stdout.write(result.stdout.split('\n')[0])
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('✗ FFmpeg not found'))
            return

        try:
            result = subprocess.run(
                ['ffprobe', '-version'],
                capture_output=True,
                text=True,
                check=True
            )
            self.stdout.write(self.style.SUCCESS('✓ FFprobe is available'))
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR('✗ FFprobe not found'))
```

## Testing Checklist

### Video Format Testing
- [ ] iPhone HEVC/H.265 video (portrait orientation)
- [ ] iPhone HEVC/H.265 video (landscape orientation)
- [ ] Android H.264 video
- [ ] Already H.264 video (should process quickly)
- [ ] Large video >2400px (verify resize)
- [ ] Small video <2400px (verify no upscaling)
- [ ] Video with no audio track
- [ ] Very short video (<5 seconds)
- [ ] Video exceeding 200MB limit (verify validation error)

### Browser Compatibility Testing
- [ ] Safari (macOS)
- [ ] Safari (iOS)
- [ ] Chrome (desktop)
- [ ] Chrome (Android)
- [ ] Firefox (desktop)
- [ ] Edge (desktop)

### Functional Testing
- [ ] Upload video via quick log form
- [ ] Upload video via AJAX (existing log)
- [ ] Verify "processing" status shows immediately
- [ ] Verify poster generates correctly
- [ ] Verify transcoded video plays with controls
- [ ] Verify progressive streaming works (can start watching before download completes)
- [ ] Test failed transcode handling
- [ ] Test retry functionality
- [ ] Verify duration displays correctly
- [ ] Verify original file retained (or deleted if cleanup enabled)

### Performance Testing
- [ ] Worker handles job without timeout
- [ ] Multiple concurrent uploads queue correctly
- [ ] RQ dashboard shows job status
- [ ] Failed jobs appear in failed queue
- [ ] FFmpeg stderr captured in logs

### Deployment Testing
- [ ] Verify FFmpeg installed in Render build
- [ ] Verify FFmpeg installed in Railway build
- [ ] Verify Redis connectivity
- [ ] Verify worker service starts correctly
- [ ] Verify environment variables set correctly
- [ ] Run `python manage.py check_ffmpeg` in production

## Operational Notes
- Set RQ worker concurrency and timeouts conservatively to fit host CPU/RAM (default: 1 worker, 600s timeout)
- Track job status to show UI feedback; retry failed jobs with backoff
- Logging: capture FFmpeg stderr for debugging (already in task code)
- Monitor Redis memory usage; set `maxmemory-policy noeviction` for job queue reliability
- Consider cleanup job to delete original files after 30 days if `transcode_status='ready'`
- Storage projection: ~40GB over 3 years at ~2 videos/week (per hosting.md)
