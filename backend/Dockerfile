FROM python:3.11-slim

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
