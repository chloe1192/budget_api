# Personal Finance Management API

A RESTful API built with Django REST Framework for managing personal finances. This backend service provides comprehensive endpoints for user authentication, transaction tracking, category management, and financial goal monitoring. Designed to support mobile and web applications with secure token-based authentication.

Disclaimer: This api/app is not made with any intention of going in production and host any real user data, it is for learning purposes only.

##  Features

> **Note**: Some features are still in development. See [Roadmap](#-roadmap) section below.

- **User Management** - Registration, authentication, and profile management
- **Transaction Management** - CRUD operations for income and expense transactions
- **Category Management** - Create and manage transaction categories with color coding
- **Financial Goals** - Set, track, and update financial goals
- **Token Authentication** - Secure API access with token-based authentication
- **CORS Support** - Cross-origin requests for frontend integration
- **MySQL Database** - Persistent data storage with Django ORM
- **Admin Dashboard** - Django admin interface for data management

##  Roadmap

Features in development and planned:
- [ ] Transaction filtering and advanced search
- [ ] Budget limits and spending alerts
- [ ] Transaction recurring/recurring patterns
- [ ] Data export (CSV, PDF)
- [ ] User statistics and analytics dashboard
- [ ] Multi-currency
- [ ] User settings and preferences

##  Tech Stack

- **Framework**: [Django 5.0.6](https://www.djangoproject.com/)
- **API**: [Django REST Framework](https://www.django-rest-framework.org/)
- **Authentication**: Token-based (DRF)
- **Database**: MySQL
- **CORS**: django-cors-headers
- **Environment**: python-dotenv

##  Prerequisites

- Python 3.10+
- MySQL Server
- pip (Python package manager)
- Virtual environment (recommended)

##  Getting Started

### 1. Clone and Setup Virtual Environment

```bash
# Navigate to project directory
cd <project-directory>
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key-here
DEBUG=True

# Database Configuration
DB_NAME=budget_db
DB_USER=root
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=3306

# CORS Settings
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 4. Database Setup

Run migrations:

```bash
python manage.py migrate
```

### 5. Create Superuser

```bash
python manage.py createsuperuser
```

### 6. Run Development Server

```bash
python manage.py runserver
```

The API will be available at `http://localhost:8000`

