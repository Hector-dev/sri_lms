# Dockerfile para sri_lms - Producción
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Crear directorios necesarios
RUN mkdir -p /app/staticfiles /app/media /app/logs /app/temp

# Recoge archivos estáticos
RUN python manage.py collectstatic --noinput

# Crear usuario no-root para seguridad
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Exponer puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

CMD ["gunicorn", "sri_lms.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "120"] 