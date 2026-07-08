FROM python:3.11-slim

WORKDIR /app

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY run.py .

# Render sets PORT at runtime; default in run.py is 8000 for local Docker
EXPOSE 8000

CMD ["python", "run.py"]
