FROM python:slim

RUN apt update
RUN apt install ffmpeg -y

WORKDIR /app

COPY app.py requirements.txt /app/
RUN --mount=type=cache,target=/root/.cache \
    pip install -r requirements.txt

CMD ["./app.py"]
