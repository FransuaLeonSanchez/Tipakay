FROM python:3.10-slim

WORKDIR /app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential libpq-dev && \
  apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/

# install python dependencies
RUN pip install --upgrade pip && \
  pip install -r requirements.txt

COPY . /app/

RUN mkdir -p /app/staticfiles

# running migrations
RUN python manage.py migrate

# gunicorn
CMD ["gunicorn", "-c", "gunicorn-cfg.py", "config.wsgi:application"]
