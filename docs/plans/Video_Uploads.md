# Video Uploads

This is the spec for supporting maintainers uploading videos while logging their work.

## Implementation Status

**Status:** Implemented with architectural modification

The plan below was fully implemented. One significant change was made during implementation:

### Architecture Change: HTTP Upload

The original plan assumed the web server and worker process share a filesystem. In production on Railway, the worker runs as a separate service with no shared disk access.

**Solution:** The worker transcodes locally to temp files, then uploads the results to the web server via HTTP:

1. Worker transcodes video and generates poster to temp files
2. Worker POSTs files to `/api/transcoding/upload/` with Bearer token authentication
3. Web server validates token, saves files to storage, updates media record status

**Required environment variables:**
- `DJANGO_WEB_SERVICE_URL` - Base URL of web service (e.g., `http://localhost:8000`)
- `TRANSCODING_UPLOAD_TOKEN` - Shared secret for authentication

**Files added for HTTP transfer:**
- `the_flip/apps/maintenance/views.py` - `ReceiveTranscodedMediaView` endpoint
- `the_flip/apps/core/tasks.py` - `_upload_transcoded_files()` function

---

## Goals
- **Upload any format, transform to a widely understood format**: accept phone-recorded videos (MOV/HEVC/etc.) and transcode to widely playable H.264/AAC MP4.
- **Poster**: generate a poster image for UI display.
- **Responsive**: keep uploads responsive by offloading transcode to a background worker.
- **Minimize services/cost/ops**: reuse Postgres as the queue backend, no Redis.
- **Very low maintenance**: the volunteer staff does not want to do any maintenance on this system. Use Django patterns, admin visibility, automatic task cleanup.

## Approach
- Use **django-q2** with the ORM broker (tasks stored in Postgres/SQLite).
- Run a single worker process (`python manage.py qcluster`) to process transcodes.
- `ffmpeg` runs in the worker; cap video long side at 2400px and generate a poster.
- Automatically prune old task rows via django-q2 settings.
- Worker recycling after N tasks to prevent memory bloat from FFmpeg.

## Dependencies
- Add `django-q2` to `requirements.txt`.
- Ensure `ffmpeg` is installed in localhost and Railway.

## Settings

**File:** `the_flip/settings/base.py`

```python
INSTALLED_APPS += ["django_q"]

Q_CLUSTER = {
    "name": "the_flip_worker",
    "orm": "default",              # Use Django database as broker
    "workers": 1,                  # Single worker (sufficient for ~2 videos/week)
    "timeout": 600,                # 10 minutes per job (ffmpeg processing time)
    "retry": 660,                  # Must be > timeout; retry after 11 minutes
    "save_limit": 50,              # Keep last 50 successful tasks (auto-cleanup)
    "queue_limit": 50,             # Max queued tasks (backpressure)
    "recycle": 5,                  # CRITICAL: Restart worker after 5 tasks to prevent FFmpeg memory leaks
    "bulk": 1,                     # Process 1 task at a time
    "catch_up": False,             # Don't process old scheduled tasks on restart
    "max_attempts": 1,             # Only try once (user can re-upload if needed)
}
```

## Model changes
- Extend `LogEntryMedia` (already has `transcoded_file`, `poster_file`, `transcode_status`, `duration`).
- `transcode_status` values: pending -> processing -> ready/failed.

## Tasks

**File:** `the_flip/apps/core/tasks.py`

Key functions:
- `enqueue_transcode(media_id, model_name)` - Queue video transcode job
- `transcode_video_job(media_id, model_name)` - Main worker function
- `_upload_transcoded_files()` - HTTP POST to web service

**Key implementation details:**
- Uses `async_task()` for django-q2 integration
- FFmpeg stderr captured for debugging
- Temp files cleaned up after upload
- Original file deleted after successful transcode (saves ~50% storage)
- Worker recycles after 5 videos (per `Q_CLUSTER` settings)
- Exponential backoff retry for HTTP uploads (3 attempts)

## Upload flow
- Form/validation: allow `image/*,video/*` with size cap (200MB) and small video extension/MIME whitelist.
- On create/AJAX upload: detect video, set status to pending, enqueue transcode; photos follow existing path.
- UI: show poster/video when ready; "Processing..." while pending/processing; "failed" message otherwise.

## Worker
- Command: `python manage.py qcluster`.
- Railway: add a worker service with start command `python manage.py qcluster`.
- Local: run in a terminal alongside `runserver`.

## Management Commands

### Check FFmpeg Installation
Command: `python manage.py check_ffmpeg` - verifies ffmpeg/ffprobe are on PATH and prints versions.

### Check Worker Health
**File:** `the_flip/apps/maintenance/management/commands/check_worker.py`

**Usage:**
```bash
python manage.py check_worker
```

**Example output:**
```
Recent successful tasks (24h): 5
No recent failures
Queue is empty
No stuck video transcodes
```

**When to run:**
- After deploying worker service
- When videos aren't processing
- In monitoring scripts (e.g., health check endpoint)
- Debugging production issues

## FFmpeg commands (reference)
- Transcode:
  ```
  ffmpeg -i "$INPUT" \
    -vf "scale=min(iw\\,2400):min(ih\\,2400):force_original_aspect_ratio=decrease" \
    -c:v libx264 -pix_fmt yuv420p -profile:v main -crf 23 -preset medium \
    -c:a aac -b:a 128k -movflags +faststart -y "$OUTPUT.mp4"
  ```
- Poster:
  ```
  ffmpeg -i "$INPUT" -vf "thumbnail,scale=320:-2" -frames:v 1 -y "$OUTPUT.jpg"
  ```

### Critical FFmpeg parameters (why they matter)
- `-vf "scale=min(iw\,2400):min(ih\,2400):force_original_aspect_ratio=decrease"`: Resize down so the long side is max 2400px; never upscale; preserves aspect ratio and keeps dimensions even for H.264.
- `-c:v libx264`: H.264 video codec (universal browser support vs HEVC/H.265).
- `-pix_fmt yuv420p`: **CRITICAL** for iOS Safari playback; without this, videos won't play on iPhones.
- `-profile:v main`: Good compatibility balance (vs high/baseline).
- `-crf 23`: Quality setting (18-28 range; lower = better quality/bigger files).
- `-preset medium`: Encoding speed vs compression efficiency (faster/medium/slow/slower).
- `-c:a aac` / `-b:a 128k`: AAC audio at 128 kbps for broad support.
- `-movflags +faststart`: **CRITICAL** for progressive streaming; moves metadata to file start.
- Poster: `thumbnail,scale=320:-2` picks a representative frame and keeps aspect ratio with even dimensions.

## Monitoring & Debugging

### Django Admin Integration
Django-Q2 provides built-in admin views at `/admin/django_q/`:
- **Successful tasks**: View last 50 completed jobs (auto-pruned by `save_limit`)
- **Failed tasks**: See errors, retry failed jobs manually
- **Queued tasks**: Monitor pending video transcodes
- **Scheduled tasks**: (Not used for this feature)

### Task Lifecycle Visibility
1. User uploads video -> `transcode_status = 'pending'`
2. Worker picks up job -> `transcode_status = 'processing'`
3. FFmpeg completes -> `transcode_status = 'ready'` (or `'failed'`)
4. UI shows video player with poster (or error message)

### Debugging Failed Jobs
If video processing fails:
1. Check django-q2 admin for error message
2. Check worker logs: `railway logs` or Railway dashboard
3. FFmpeg stderr is captured in exception logs
4. User can re-upload (simpler than retry mechanism)

### No Extra Infrastructure
- No Redis to monitor
- No separate RQ dashboard to install
- No additional failure points
- All monitoring through tools volunteers already use (Django admin)

## Deployment

### Railway (Active Platform)
1. **Add Worker Service** via dashboard:
   - Service name: `the-flip-worker`
   - Source: Same repo as web service
   - Root directory: (same as web)
   - Build command: `./build.sh`
   - Start command: `python manage.py qcluster`
   - Instance: Starter ($5/mo)

2. **Environment Variables**:
   - Copy all env vars from web service (DATABASE_URL, SECRET_KEY, etc.)
   - Add `DJANGO_WEB_SERVICE_URL` (web service's Railway URL)
   - Add `TRANSCODING_UPLOAD_TOKEN` (generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
   - Railway auto-shares DATABASE_URL within project

3. **FFmpeg Installation**:
   - Already in `railpack.worker.json`: `buildAptPackages` and `deploy.aptPackages`
   - Shared build with web service

**Cost:** Worker service ~$5-10/mo (starter plan)

### Local Development

**Option 1: Two terminals**
```bash
# Terminal 1
python manage.py runserver

# Terminal 2
python manage.py qcluster
```

**Option 2: VS Code Compound Launch Configuration**

See `.vscode/launch.json` for "Django: Full Stack (Web + Worker)" configuration.

### Verification Checklist
After deploying worker:
- [ ] Worker service shows as "running" in dashboard
- [ ] `python manage.py check_ffmpeg` succeeds (both ffmpeg and ffprobe found)
- [ ] Upload test video, verify `transcode_status` changes: pending -> processing -> ready
- [ ] Check django-q2 admin shows successful task
- [ ] Verify transcoded video plays in browser
- [ ] Verify poster image displays
- [ ] Verify original file deleted (check storage size)
- [ ] Check worker memory usage after 5 videos (should recycle/drop)

## Test for FFmpeg in CI Pipeline

Add automated testing for FFmpeg availability in your CI pipeline to catch deployment issues early:
- Railway build changes could break FFmpeg installation
- railpack.worker.json edits might remove FFmpeg
- Dependency conflicts could prevent FFmpeg from being available
- Catch issues before deploying to production

### Implementation
Add a test case to the Django Test Suite; ensure the suite runs in the CI. It tests that:
- FFmpeg binary is available on PATH
- FFprobe binary is available on PATH
- Both execute successfully
- Versions are reported (useful for debugging)


## Rejected Alternative: Redis + RQ

Redis + RQ was considered but not chosen for this project.

### Decision Factors

**Volume Analysis:**
- Expected: ~2 videos/week (~100 videos/year)
- Worker utilization: <0.1% (mostly idle)
- Processing time: 2-5 minutes per video
- No concurrent processing needed

**Cost Comparison:**
| Approach | Services | Monthly Cost | Annual Cost |
|----------|----------|--------------|-------------|
| **django-q2 (DB)** | Web + Worker | ~$15-20 | ~$180-240 |
| Redis + RQ | Web + Worker + Redis | ~$25-30 | ~$300-360 |
| **Savings:** | -1 service | **-$10/mo** | **-$120/year** |

**Operational Complexity:**
| Factor | django-q2 (DB) | Redis + RQ |
|--------|----------------|------------|
| Services to deploy | 2 | 3 |
| Services to monitor | 2 | 3 |
| Infrastructure knowledge | Django only | Django + Redis |
| Task visibility | Django admin | Separate dashboard |
| Volunteer handoff | Easy | Moderate |
| Failure points | 2 | 3 |

**Performance Trade-offs:**
- **Redis:** Job pickup ~10-50ms, pub/sub architecture
- **django-q2 (DB):** Job pickup ~1-5 seconds, polling architecture
- **Impact:** Negligible - videos process in background over 2-5 minutes anyway
- **Verdict:** 5-second pickup delay doesn't matter for 3.5-day average job spacing

### Why Database-Backed Queue Was Chosen

1. **Simpler Architecture**
   - 2 services instead of 3
   - One database instead of database + Redis
   - Fewer environment variables to configure
   - Single platform (Railway) vs potential multi-platform

2. **Lower Cost**
   - No Redis monthly fee ($60-120/year savings)
   - Same worker cost (unavoidable)
   - Better value for volunteer organization budget

3. **Better Volunteer Experience**
   - Tasks visible in Django admin (already familiar)
   - No Redis concepts to learn (eviction policies, memory tuning, persistence)
   - Easier debugging (all data in one database)
   - Simpler deployment (one less service to configure)

4. **Maintenance-Free**
   - Automatic task cleanup via `save_limit` setting
   - No Redis memory management needed
   - No Redis version upgrades to track
   - Database already has backup strategy

5. **Django-Native**
   - Uses ORM (volunteers already know this)
   - Admin integration out of the box
   - Same patterns as rest of codebase
   - No impedance mismatch

### When Redis Would Be Better

Redis + RQ would be the better choice if:
- Processing >100 videos/day (we process ~0.3/day)
- Need sub-second job pickup (we don't)
- Complex multi-queue workflows (we have one queue)
- High-throughput requirements (we have low volume)
- Already using Redis for caching (we're not)
- Full-time DevOps team (we have volunteers)
