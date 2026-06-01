FROM python:3.10.10-slim

WORKDIR /app

COPY shared/ /app/shared/
RUN pip install --no-cache-dir -e /app/shared

COPY service-admin/requirements.txt /app/service-admin/
RUN pip install --no-cache-dir -r /app/service-admin/requirements.txt

COPY service-admin/ /app/service-admin/

WORKDIR /app/service-admin
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8003"]
