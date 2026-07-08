FROM python:3.10-slim
WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

# PYTHONPATH를 /code 또는 현재 디렉토리로 명시
ENV PYTHONPATH=/code

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
