FROM python:3.19

COPY . /app
WORKDIR /app

RUN pdm install

CMD ["pdm", "run", "start"]