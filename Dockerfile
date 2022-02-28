FROM python:slim

RUN apt update
RUN apt install ffmpeg -y

WORKDIR /app

COPY . /app
RUN pip install -r requirements.txt

CMD ["./app.py"]
