FROM python:3.12-slim

COPY . /app
WORKDIR /app

RUN pip3 install pdm && pdm install --prod

CMD ["pdm", "run", "start"]