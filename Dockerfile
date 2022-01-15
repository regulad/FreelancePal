# syntax=docker/dockerfile:1

FROM python:3.10.1-alpine

RUN apk add git

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python", "./main.py"]
