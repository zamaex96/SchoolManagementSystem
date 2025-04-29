


# School Management System

A Django-based application for managing students, teachers, classes, attendance, announcements, and results.

---

## Table of Contents

1. [Features](#features)  
2. [Prerequisites](#prerequisites)  
3. [Installation & Local Setup](#installation--local-setup)  
4. [Configuration](#configuration)  
5. [Running in Development](#running-in-development)  
6. [Deployment to Production](#deployment-to-production)  
7. [Customisation](#customisation)  
8. [Contributing](#contributing)  
9. [License](#license)  

---
## Demo

![Quick Demo](media/SMSclip.gif)

## Features

- User authentication (admin, teachers, parents)  
- CRUD for Students, Teachers, Classes, Subjects  
- Attendance tracking & reports  
- Announcements & news articles with images  
- Result management & transcripts  

---

## Prerequisites

- Python 3.10+  
- pip (or `pipenv` / `poetry`)  
- Git  
- PostgreSQL (or any other RDBMS supported by Django)  
- (For production) Gunicorn, Nginx  

---

## Installation & Local Setup

1. **Clone repository**  
   ```bash
   git clone https://github.com/zamaex96/SchoolManagementSystem.git
   cd SchoolManagementSystem
   ```

2. **Create virtual environment**  
   ```bash
   python -m venv .venv
   .venv\Scripts\activate     # Windows
   source .venv/bin/activate  # macOS/Linux
   ```

3. **Install dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment variables**  
   Copy `.env.example` to `.env`, then set:
   ```
   SECRET_KEY=your-django-secret-key
   DEBUG=True
   DATABASE_URL=postgres://USER:PASSWORD@HOST:PORT/DB_NAME
   ```

5. **Database migrations & superuser**  
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```



## Configuration

In `settings.py` (or via env vars):

- **`DEFAULT_AUTO_FIELD`**  
  ```python
  DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
  ```
- **Database**  
  Ensure `DATABASES['default']['ENGINE']` matches your RDBMS.  
- **Static & Media**  
  ```python
  STATIC_URL = '/static/'
  MEDIA_URL  = '/media/'
  ```

---

## Running in Development

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000/`.  
Admin interface: `http://127.0.0.1:8000/admin/`

---

## Deployment to Production

1. **Install production dependencies**  
   ```bash
   pip install gunicorn whitenoise psycopg2-binary
   ```

2. **Settings adjustments**  
   ```python
   DEBUG = False
   ALLOWED_HOSTS = ['yourdomain.com']
   MIDDLEWARE = [
       'whitenoise.middleware.WhiteNoiseMiddleware',
       # ...
   ]
   STATIC_ROOT = BASE_DIR / 'staticfiles'
   ```

3. **Collect static files**  
   ```bash
   python manage.py collectstatic
   ```

4. **Gunicorn & Nginx**  
   - Gunicorn command:
     ```bash
     gunicorn school_system.wsgi:application --bind 0.0.0.0:8000
     ```
   - Configure Nginx to proxy `127.0.0.1:8000` and serve `/static/` from `staticfiles/`.

5. **Process manager**  
   Use systemd or Supervisor to keep Gunicorn alive.

---

## Customisation

- **Adding new models:**  
  1. Define in `core/models.py`  
  2. Register in `core/admin.py`  
  3. `makemigrations` → `migrate`
- **Overriding templates:**  
  Place custom templates in `templates/` mirroring app structure.  
- **Custom settings:**  
  Create `settings_local.py`, import in main settings.

---

## Contributing

1. Fork the repository  
2. Create feature branch: `git checkout -b feature/YourFeature`  
3. Commit changes & push:  
   ```bash
   git push origin feature/YourFeature
   ```  
4. Open a Pull Request  

Please follow PEP 8 and include tests for new functionality.

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
```

Feel free to adjust any paths or settings to suit your environment.
