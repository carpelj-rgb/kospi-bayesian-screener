FROM python:3.10-slim
WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

RUN mkdir -p /code/data

ENV PYTHONPATH=/code
ENV SQLITE_PATH=/code/data/screener.db

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
