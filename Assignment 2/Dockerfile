from python:3-onbuild

RUN apk add --no-cache python3-dev

RUN pip3 install --upgrade pip

WORKDIR /app

COPY . /app

CMD ["python","waitress_server.py"]

EXPOSE 5000
