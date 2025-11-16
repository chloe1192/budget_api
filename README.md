# Personal Finance Management API

A RESTful API built with Django REST Framework for managing personal finances. This backend service provides comprehensive endpoints for user authentication, transaction tracking, category management, and financial goal monitoring. Designed to support mobile and web applications with secure token-based authentication.

## 🎯 Features

> **Note**: Some features are still in development. See [Roadmap](#-roadmap) section below.

- **User Management** - Registration, authentication, and profile management
- **Transaction Management** - CRUD operations for income and expense transactions
- **Category Management** - Create and manage transaction categories with color coding
- **Financial Goals** - Set, track, and update financial goals
- **Token Authentication** - Secure API access with token-based authentication
- **CORS Support** - Cross-origin requests for frontend integration
- **MySQL Database** - Persistent data storage with Django ORM
- **Admin Dashboard** - Django admin interface for data management

## 📍 Roadmap

Features in development and planned:
- [ ] Transaction filtering and advanced search
- [ ] Budget limits and spending alerts
- [ ] Transaction recurring/recurring patterns
- [ ] Data export (CSV, PDF)
- [ ] User statistics and analytics dashboard
- [ ] Multi-currency support
- [ ] API documentation (Swagger/OpenAPI)
- [ ] WebSocket support for real-time updates
- [ ] File upload for receipts/attachments
- [ ] User settings and preferences

## 🛠️ Tech Stack

- **Framework**: [Django 5.0.6](https://www.djangoproject.com/)
- **API**: [Django REST Framework](https://www.django-rest-framework.org/)
- **Authentication**: Token-based (DRF)
- **Database**: MySQL
- **CORS**: django-cors-headers
- **Environment**: python-dotenv

## 📋 Prerequisites

- Python 3.10+
- MySQL Server
- pip (Python package manager)
- Virtual environment (recommended)

## 🚀 Getting Started

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

## 📚 API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | User login (returns token) |
| GET | `/api/auth/user` | Get current user profile |
| PUT | `/api/auth/user` | Update user profile |

### Users

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users/<id>` | Get user details |
| PUT | `/api/users/<id>` | Update user |
| DELETE | `/api/users/<id>` | Delete user |

### Categories

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/categories` | List all categories |
| POST | `/api/categories` | Create new category |
| GET | `/api/categories/<id>` | Get category details |
| PUT | `/api/categories/<id>` | Update category |
| DELETE | `/api/categories/<id>` | Delete category |

### Transactions

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/transactions` | List all transactions |
| POST | `/api/transactions` | Create new transaction |
| GET | `/api/transactions/<id>` | Get transaction details |
| PUT | `/api/transactions/<id>` | Update transaction |
| DELETE | `/api/transactions/<id>` | Delete transaction |

### Goals

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/goals` | List all goals |
| POST | `/api/goals` | Create new goal |
| GET | `/api/goals/<id>` | Get goal details |
| PUT | `/api/goals/<id>` | Update goal |
| DELETE | `/api/goals/<id>` | Delete goal |

## 🏗️ Project Structure

```
project-root/
├── api/                    # Main Django project settings
│   ├── settings.py        # Project settings and configurations
│   ├── urls.py            # URL routing configuration
│   ├── wsgi.py            # WSGI configuration for deployment
│   └── asgi.py            # ASGI configuration
├── api_service/           # Main application
│   ├── models.py          # Database models (User, Category, Transaction, Goal)
│   ├── serializers.py     # DRF serializers
│   ├── views.py           # API views
│   ├── urls.py            # App-specific routes
│   ├── admin.py           # Admin configurations
│   └── migrations/        # Database migrations
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (not in repo)
└── db.sqlite3            # SQLite database (development only)
```

## 📊 Database Models

### User
```python
- username (CharField)
- email (EmailField)
- first_name (CharField)
- last_name (CharField)
- dob (DateTimeField, optional)
- avatar (ImageField, optional)
- initial_balance (DecimalField)
- created_at (DateTimeField)
- edited_at (DateTimeField)
```

### Category
```python
- user (ForeignKey → User)
- name (CharField)
- type (CharField: 'INCOME' or 'EXPENSE')
- color (CharField: hex color code)
```

### Transaction
```python
- user (ForeignKey → User)
- category (ForeignKey → Category)
- title (CharField)
- description (TextField)
- amount (DecimalField)
- date (DateTimeField)
- created_at (DateTimeField)
```

### Goal
```python
- user (ForeignKey → User)
- title (CharField)
- description (TextField)
- amount (DecimalField)
- date (DateTimeField)
- created_at (DateTimeField)
- updated_at (DateTimeField)
```

## 🔐 Authentication

The API uses token-based authentication. Include the token in request headers:

```
Authorization: Token <your-auth-token>
```

Example:
```bash
curl -H "Authorization: Token abc123xyz" http://localhost:8000/api/user/
```

## ⚙️ Configuration

### CORS Settings

Configure allowed origins in `api/settings.py`:

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8100",    # Ionic dev server
    "http://127.0.0.1:8100",
    "https://yourdomain.com",   # Production domain
]
```

### Database

The project uses MySQL by default. Update database settings in `api/settings.py` or `.env` file.

For development with SQLite, update `DATABASES` in settings:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

## 🧪 Testing

Run tests:

```bash
python manage.py test
```

Run with coverage:

```bash
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## 📦 Deployment

### Using Gunicorn

```bash
pip install gunicorn
gunicorn api.wsgi:application --bind 0.0.0.0:8000
```

### Using uWSGI

```bash
pip install uwsgi
uwsgi --http :8000 --wsgi-file api/wsgi.py --master --processes 4 --threads 2
```

### Production Checklist

- [ ] Set `DEBUG = False` in `.env`
- [ ] Update `SECRET_KEY` to a secure random value
- [ ] Configure `ALLOWED_HOSTS` with your domain
- [ ] Use a production database (MySQL/PostgreSQL)
- [ ] Enable HTTPS
- [ ] Set up proper error logging
- [ ] Configure static and media files storage
- [ ] Run security checks: `python manage.py check --deploy`

## 🐛 Troubleshooting

### Database Connection Error
Ensure MySQL is running and credentials in `.env` are correct:
```bash
mysql -u root -p
# Then test connection
```

### Migration Issues
```bash
# Reset migrations (development only)
python manage.py migrate api_service zero
python manage.py migrate
```

### CORS Errors
Check that the frontend URL is in `CORS_ALLOWED_ORIGINS` in settings.

### Port Already in Use
Run on a different port:
```bash
python manage.py runserver 8001
```

## 📝 API Documentation

For interactive API documentation, navigate to:
- Swagger UI: `http://localhost:8000/swagger/` (if swagger is installed)
- ReDoc: `http://localhost:8000/redoc/` (if available)

## 📄 License

See [LICENSE](./LICENSE) file for details.

## ✏️ About This Project

This is a full-featured personal finance management API built to demonstrate modern backend development practices with Django and DRF. The project showcases REST API design, authentication, database modeling, and integration with frontend applications.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📧 Contact

For questions or feedback, please open an issue in the repository.
