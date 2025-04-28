# Use an official Python runtime as a parent image
FROM python:3.10-slim-bullseye

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# --- ADD HARMLESS CACHE BUSTER ---
ARG CACHEBUST=1
# --- END CACHE BUSTER ---

# Set work directory
WORKDIR /app

# Install system dependencies (if any - psycopg2 might need some, but binary often includes them)
# RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project code
COPY . .

# Collect static files (Whitenoise needs this)
# Make sure DEBUG=False temporarily for collectstatic if needed, or handle via env vars
# Often safer to set DEBUG=False via env var during build on Koyeb
RUN python manage.py collectstatic --no-input

# Expose port (Gunicorn default is 8000)
EXPOSE 8000

# Command to run the application using Gunicorn
# Uses environment variables for host/port if available, defaults to 0.0.0.0:8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "school_system.wsgi:application"]
# Replace 'school_system' if your WSGI file is in a different project directory