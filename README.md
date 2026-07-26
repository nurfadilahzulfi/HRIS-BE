# HRIS Enterprise Backend

Backend REST API untuk sistem HRIS (Human Resource Information System) enterprise.

## Tech Stack

- **Framework**: Django 4.2 LTS + Django REST Framework
- **Database**: PostgreSQL
- **Auth**: JWT (djangorestframework-simplejwt)
- **Task Queue**: Celery + Redis
- **PDF**: WeasyPrint
- **API Docs**: drf-spectacular (Swagger)

## Setup

### Prerequisites

- Python 3.11+
- PostgreSQL
- Redis

### Installation

```bash
# Clone & setup virtual env
python -m venv venv
.\venv\Scripts\activate   # Windows
source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements/development.txt

# Setup environment variables
cp .env .env.local
# Edit .env with your database & email credentials

# Create database
createdb hris_db  # or use pgAdmin

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Running Celery (for async tasks)

```bash
# Worker
celery -A config worker -l info

# Beat (scheduler)
celery -A config beat -l info
```

### API Documentation

Visit: http://localhost:8000/api/docs/

### Docker (Optional)

```bash
docker-compose up -d
```

## Apps

| App | Description |
|-----|-------------|
| `core` | Auth, User, JWT, RBAC |
| `company` | Company & Entity management |
| `employees` | Employee data, org chart |
| `contracts` | PKWT/PKWTT/BHL contracts |
| `attendance` | Attendance (API-agnostic) |
| `leave` | Leave management & approval |
| `payroll` | Payroll calculation |
| `tax` | PPh21 engine |
| `salary_slip` | PDF slip generation |
| `training` | Training programs |
| `assessment` | Quiz/assessment engine |
| `kpi` | KPI management |
| `notifications` | Email scheduler |
