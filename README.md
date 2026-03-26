# DetailFlow - Car Detailing Workflow Management System

A comprehensive Django-based workflow management system for car detailing businesses in Thika, Kenya.

## Features

- **Dashboard**: Real-time Kanban board for job tracking
- **Job Management**: Create, track, and manage detailing jobs
- **Customer Management**: Customer database with vehicle information
- **Worker Management**: Track worker assignments and performance
- **Service Catalog**: Configurable services with pricing
- **Notifications**: Real-time notification system
- **Reports**: Business analytics and reporting
- **Role-based Access**: Admin, Manager, Worker, Viewer roles

## Tech Stack

- **Backend**: Django 5.0, Python 3.11+
- **Database**: MySQL
- **Cache**: Redis
- **Task Queue**: Celery
- **Frontend**: Bootstrap 5, HTMX
- **Deployment**: Docker, Nginx, Gunicorn

## Quick Start

### Prerequisites

- Python 3.11+
- MySQL
- Redis (optional, for caching/celery)

### Installation

1. **Clone and setup virtual environment**
```bash
gti clone https://github.com/Omollodev/car-detailing-workflow-management-system.git
cd car-detailing-workflow-management-system
python3 -m venv venv
source venv/Scripts/activate  # On Windows: venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your database credentials
```

4. **Run migrations**
```bash
python manage.py migrate
```

5. **Create initial data**
```bash
python scripts/setup_initial_data.py
# Or run: python manage.py setup
```

6. **Run development server**
```bash
python manage.py runserver
```

7. **Access the application**
- URL: http://localhost:8000
- Login: admin / admin123

## Docker Deployment

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f

# Stop
docker-compose down
```

## Project Structure

```
django_detailing/
├── config/                 # Project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/                   # Django applications
│   ├── accounts/           # User authentication
│   ├── customers/          # Customer & vehicle management
│   ├── jobs/               # Job management (core)
│   ├── services/           # Service catalog
│   ├── workers/            # Worker management
│   ├── notifications/      # Notification system
│   └── dashboard/          # Dashboard views
├── templates/              # HTML templates
├── static/                 # CSS, JS, images
├── scripts/                # Utility scripts
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## API Endpoints

- `GET /api/jobs/kanban/` - Kanban board data
- `POST /api/jobs/{id}/status/` - Update job status
- `GET /api/customers/{id}/vehicles/` - Customer vehicles
- `POST /api/jobs/{id}/assign/` - Assign workers

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DEBUG | Debug mode | False |
| SECRET_KEY | Django secret key | - |
| DB_NAME | Database name | detailflow |
| DB_USER | Database user | - |
| DB_PASSWORD | Database password | - |
| DB_HOST | Database host | localhost |
| REDIS_URL | Redis connection URL | - |

## User Roles

- **Admin**: Full system access
- **Manager**: Manage jobs, customers, workers
- **Worker**: View assigned jobs, update status
- **Viewer**: Read-only dashboard access

## Running Tests

```bash
python manage.py test
# Or with coverage
coverage run manage.py test
coverage report
```

## Railway Deployment

This project is configured for Railway with `railway.json`.

### Required Service Variables

Set these in Railway Variables for your web service:

```bash
DATABASE_PUBLIC_URL="postgresql://${{PGUSER}}:${{POSTGRES_PASSWORD}}@${{RAILWAY_TCP_PROXY_DOMAIN}}:${{RAILWAY_TCP_PROXY_PORT}}/${{PGDATABASE}}"
DATABASE_URL="postgresql://${{PGUSER}}:${{POSTGRES_PASSWORD}}@${{RAILWAY_PRIVATE_DOMAIN}}:5432/${{PGDATABASE}}"
PGDATA="/var/lib/postgresql/data/pgdata"
PGDATABASE="${{POSTGRES_DB}}"
PGHOST="${{RAILWAY_PRIVATE_DOMAIN}}"
PGPASSWORD="${{POSTGRES_PASSWORD}}"
PGPORT="5432"
PGUSER="${{POSTGRES_USER}}"
POSTGRES_DB="railway"
POSTGRES_USER="postgres"
RAILWAY_DEPLOYMENT_DRAINING_SECONDS="60"
SSL_CERT_DAYS="820"
```

Set your secrets separately in Railway (do not hardcode in git), including:

```bash
POSTGRES_PASSWORD="<your-secret-password>"
DJANGO_SECRET_KEY="<your-django-secret-key>"
DEBUG="False"
```

### Deploy flow

1. Link repo to Railway project
2. Provision PostgreSQL service
3. Add the variables above
4. Deploy (Railway runs `collectstatic`, then `migrate`, then starts Gunicorn)

## Support

For issues specific to the Safi, Kenya deployment, contact the development team.

## License

Proprietary - All rights reserved.
