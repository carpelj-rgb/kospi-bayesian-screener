FROM python:3.10-slim

# 1. 컨테이너 내부의 작업 폴더를 /code 로 명확히 지정
WORKDIR /code

# 2. 의존성 패키지 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 3. 백엔드 소스코드 전체 복사 (app 폴더 포함)
COPY . .

# 4. Render 동적 포트에 맞춘 실행 명령어 (포트가 없으면 10000번 사용)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
