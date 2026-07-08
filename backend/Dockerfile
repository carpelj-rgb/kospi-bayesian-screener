FROM python:3.11-slim

# Bump CACHE_BUST to force Render "clear build cache" rebuild from this layer
ARG CACHE_BUST=9ccad83-port-cmd-1

WORKDIR /app

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PORT=10000

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY run.py .

# Render injects PORT at runtime (often 10000)
EXPOSE 10000

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
