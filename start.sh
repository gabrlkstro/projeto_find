#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Running Django Database Migrations..."
python manage.py migrate

echo "==> Seeding Default Categories..."
python manage.py criar_categorias

echo "==> Generating Image Hashes..."
python manage.py gerar_hashes

echo "==> Starting Gunicorn Web Server..."
gunicorn find.wsgi:application
