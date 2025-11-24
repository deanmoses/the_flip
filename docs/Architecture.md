# Architecture

## System Components

### Web Application
- Serves the website and handles user requests

### Background Worker
- Processes video transcoding asynchronously to keep it off the UI thread

### Persistent File Storage
- Store uploaded photos and videos
- *In prod*: a persistent disk attached to the web application
- *In dev*: the local project directory

### Database
- Stores all application data
- *In prod*: PostgreSQL
- *In dev*: SQLite
