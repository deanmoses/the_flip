# Architecture

## System Components

**Web Application**
- Serves the website and handles user requests

**Background Worker**
- Processes video transcoding asynchronously to keep it off the UI thread
- Uses Django Q task queue

**Database**
- Stores all application data
- PostgreSQL in production, SQLite for local development

**File Storage**
- Photos and videos uploaded by users
- Persistent disk in production, local project directory for development
