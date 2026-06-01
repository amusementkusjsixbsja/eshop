FROM python:3.10.10-slim

WORKDIR /app

COPY shared/ /app/shared/
RUN pip install --no-cache-dir -e /app/shared

COPY ai-service/requirements.txt /app/ai-service/
RUN pip install --no-cache-dir -r /app/ai-service/requirements.txt

COPY ai-service/ /app/ai-service/

WORKDIR /app/ai-service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8004"]
