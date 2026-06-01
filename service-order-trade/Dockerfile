FROM python:3.10.10-slim

WORKDIR /app

COPY shared/ /app/shared/
RUN pip install --no-cache-dir -e /app/shared

COPY service-order-trade/requirements.txt /app/service-order-trade/
RUN pip install --no-cache-dir -r /app/service-order-trade/requirements.txt

COPY service-order-trade/ /app/service-order-trade/

WORKDIR /app/service-order-trade
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8002"]
