FROM python:3.10-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential libpq-dev && \
  apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --upgrade pip && \
  pip install -r requirements.txt

COPY . /app/

# Ensure permissions for all project files
RUN chmod -R 755 /app

# Run database migrations
RUN python manage.py migrate

# Gunicorn
CMD ["gunicorn", "-c", "gunicorn-cfg.py", "config.wsgi:application"]
