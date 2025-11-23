# Deployment

## Production Environment

The live production system is deployed at: https://the-flip-production.up.railway.app/

It deploys every time the `main` branch is pushed to GitHub.

There are no other hosted environments as of yet: no staging, testing, UAT.


## Platform: Railway

[Railway](https://railway.app/) is the hosting platform.

## Deployment

 - Push `main` branch changes to GitHub
 - Railway automatically detects the push
 - Build takes ~2-5 minutes
 - You can follow along and see build logs on Railway

## Rollback

You can rollback to a previous version via the Railway dashboard.  It's point and click.

Rollbacks only affect application code, not the database.

## Application Logs

View logs in Railway dashboard

### Worker Health

Check worker status with management command:
```bash
railway run python manage.py check_worker
```

This shows:
- Recent successful tasks (last 24 hours)
- Recent failures
- Queued tasks
- Stuck video transcodes

### Django Admin

Access admin panel at: https://the-flip-production.up.railway.app/admin/

Monitor background tasks:
- Navigate to "Django Q" section
- View successful/failed tasks
- See queued jobs
- Manually retry failed jobs


## Database

### Backups

Railway automatically backs up the PostgreSQL database. It's a daily backup, not point in time (PITR).  Restore is point and click.


## Photo & Video File Storage

Railway provides persistent disk storage for uploaded photos and videos.

### File Backups & Restore

Railway automatically creates daily snapshots of the persistent disk. It's point and click.

### Storage Location

Photos and videos are stored in `/media/` directory on the persistent disk:


## Cost Monitoring

Monitor costs in Railway's dashboard.