FROM node:20-alpine AS client-builder

WORKDIR /tsd/pwa

COPY clients/tsd/pwa/package.json clients/tsd/pwa/package-lock.json ./
RUN npm ci

COPY clients/tsd/pwa ./
RUN npm run build


FROM python:3.9-slim

RUN pip install --upgrade pip python-multipart
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . /app
COPY --from=client-builder /tsd/pwa/assets /app/clients/tsd/pwa/assets
WORKDIR /app

ENV TZ=Asia/Tashkent
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]