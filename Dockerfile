FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml /app/pyproject.toml
COPY config /app/config
COPY apps /app/apps
COPY templates /app/templates
COPY static /app/static
COPY manage.py /app/manage.py

RUN uv pip install --system .

EXPOSE 8880

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8880", "--workers", "3", "--timeout", "120"]
