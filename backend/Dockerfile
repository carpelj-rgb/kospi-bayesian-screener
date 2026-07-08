FROM python:3.10-slim

WORKDIR /code

ENV PYTHONPATH=/code \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

CMD ["sh", "-c", "cd /code && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
