FROM python:3.9-slim

  
RUN pip install --upgrade pip python-multipart
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . /app
WORKDIR /app

ENV TZ=Asia/Tashkent
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
