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

## Production Deployment

1. Set `DEBUG=False` in environment
2. Configure proper `SECRET_KEY`
3. Set up PostgreSQL database
4. Configure Redis for caching
5. Set up Celery for async tasks
6. Configure Nginx as reverse proxy
7. Use Gunicorn as WSGI server
8. Set up SSL certificate

## Support

For issues specific to the Safi, Kenya deployment, contact the development team.

## License

Proprietary - All rights reserved.
