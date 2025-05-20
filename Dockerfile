FROM python:3.11-slim-buster

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        gcc \
        netcat \
        curl \
        supervisor \
    && rm -rf /var/lib/apt/lists/*

# Install pipenv or pip requirements
COPY requirements.txt /app/
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Create a non-root user
RUN adduser --disabled-password --gecos '' django

# Copy project
COPY . /app/
RUN chown -R django:django /app

# Collect static files
# RUN python manage.py collectstatic --noinput

# Copy supervisord configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Start supervisord
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"] 