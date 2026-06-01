FROM node:20-alpine

WORKDIR /app
# build context 是项目根目录，所以路径从那里开始
COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install
COPY frontend/ ./

EXPOSE 5173
CMD ["npx", "vite", "--host", "0.0.0.0", "--port", "5173"]

