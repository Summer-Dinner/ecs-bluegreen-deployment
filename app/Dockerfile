FROM 423623840566.dkr.ecr.us-east-1.amazonaws.com/base/python:3.12-slim

WORKDIR /app

COPY requirements.txt /app

RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y curl

COPY . .

EXPOSE 5000

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]