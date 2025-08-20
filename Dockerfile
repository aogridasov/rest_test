FROM python:3.10-bookworm

WORKDIR /home/web/app

RUN pip install poetry
COPY . .
RUN poetry lock
RUN export POETRY_DOTENV_LOCATION=./.dev
RUN poetry install --no-root
