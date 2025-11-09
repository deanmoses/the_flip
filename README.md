# Prototype of The Flip Pinball Musuem's Maintenance System

This is a prototype web app for managing pinball machine problem reports at The Flip pinball museum.

It allows museum visitors to report problems with pinball machines (via QR codes on each machine), and enables maintainers to track, update, and resolve these issues. 

## Live System
Check out the prototype live at https://the-flip.onrender.com

## Local Development Setup
It's in Django.

### Prerequisites
- Python 3.13+
- pip

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd the_flip
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set all the values, see the examples.

5. **Run migrations**
   ```bash
   cd the_flip
   python manage.py migrate
   ```

6. **Create a superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Load sample data (optional)**
   ```bash
   python manage.py populate_sample_games
   python manage.py populate_sample_problem_reports
   ```

8. **Run development server**
   ```bash
   python manage.py runserver
   ```

9. **Access the application**
   - Main site: http://localhost:8000/
   - Admin panel: http://localhost:8000/admin/

## Creating Maintainer Accounts

Maintainers need both a Django user account and a Maintainer profile:

1. Create user via Django admin or `createsuperuser` command
2. In the admin panel (`/admin/`), create a Maintainer record linked to that user
3. Maintainer can now log in and manage reports

Alternatively, staff users (with `is_staff=True`) can also manage reports without a Maintainer profile.


## Deploying the Public Prototype

The prototype at https://the-flip.onrender.com is deployed every time this repo's main branch is pushed to Github.

### Admin Account Setup

The build process automatically creates a default admin account using environment variables. In the Render dashboard, set:

- `ADMIN_USERNAME` (e.g., `admin`)
- `ADMIN_PASSWORD` (use a strong password!)
- `ADMIN_EMAIL` (e.g., `admin@theflip.com`)

After each deployment, you can log in at `/admin/` with these credentials. The admin user is automatically created with both superuser privileges and a Maintainer profile.

**Note:** Since the database resets on each deploy (SQLite on Render free tier), the admin account and sample data are recreated automatically by the `build.sh` script.