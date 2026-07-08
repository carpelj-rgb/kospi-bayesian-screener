FROM python:3.11-slim

# Bump CACHE_BUST to force Render "clear build cache" rebuild from this layer
ARG CACHE_BUST=3554c84-clear-cache-1

WORKDIR /app

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PORT=10000

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY run.py .

# Render assigns PORT at runtime (often 10000)
EXPOSE 10000

# Reads $PORT inside run.py; shell fallback keeps Render-compatible expansion
CMD ["sh", "-c", "exec python run.py"]
