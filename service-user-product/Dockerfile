FROM python:3.10.10-slim

WORKDIR /app

# 安装共享库
COPY shared/ /app/shared/
RUN pip install --no-cache-dir -e /app/shared

# 安装服务依赖
COPY service-user-product/requirements.txt /app/service-user-product/
RUN pip install --no-cache-dir -r /app/service-user-product/requirements.txt

# 复制服务代码
COPY service-user-product/ /app/service-user-product/

WORKDIR /app/service-user-product
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
