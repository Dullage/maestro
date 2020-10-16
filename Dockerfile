FROM python:3.8-alpine3.12

RUN mkdir /app
WORKDIR /app

COPY Pipfile /app
COPY Pipfile.lock /app
RUN pip install pipenv && pipenv install

COPY ./maestro /app


CMD ["pipenv", "run", "python", "maestro.py"]
