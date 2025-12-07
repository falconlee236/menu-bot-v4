# 1. 가볍고 안정적인 Python 3.9 slim 버전 사용
FROM python:3.9-slim

# 2. 컨테이너 내 작업 디렉토리 설정
WORKDIR /app

# 3. 환경 변수 설정 (로그 즉시 출력, .pyc 파일 생성 방지)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 4. 의존성 설치 (캐싱 효율을 위해 소스보다 먼저 복사)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. 전체 소스 코드 복사
COPY . .

# 6. 포트 노출 (config.py에 설정된 7753번 포트)
EXPOSE 7753

# 7. 실행 명령어 (aiohttp는 python으로 직접 실행)
# 주의: 메인 실행 파일명이 app.py가 아니라면 수정하세요 (예: main.py)
CMD ["python", "app.py"]