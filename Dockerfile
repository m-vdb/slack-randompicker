FROM python:3.7

ADD pyproject.toml poetry.lock /app/
ADD randompicker /app/randompicker
WORKDIR /app

RUN pip install poetry
RUN poetry install --no-dev

EXPOSE 80
ENV PYTHONPATH "/app/"

# DATABASE_URL, SLACK_TOKEN, SLACK_SIGNING_SECRET env variables are required
CMD [ "poetry", "run", "python", "./randompicker/app.py" ]
