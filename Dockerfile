FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install build deps and runtime requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Default command uses the $PORT provided by Render; fallback to 8000
CMD ["sh", "-c", "python -m gunicorn app:app --bind 0.0.0.0:${PORT:-8000}"]
