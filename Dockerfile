FROM python:3.11-slim

# Create app user với UID 1000 (thường match host user)
RUN useradd -u 1000 -m -s /bin/bash appuser

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Set ownership cho appuser
RUN chown -R appuser:appuser /app

# Tạo thư mục data với quyền đúng
RUN mkdir -p /app/data && chown -R appuser:appuser /app/data

USER appuser

CMD ["python", "app.py"]