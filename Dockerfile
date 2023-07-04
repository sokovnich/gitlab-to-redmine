FROM python:alpine3.18

WORKDIR /app

ADD requirements.txt .

RUN pip install -r ./requirements.txt

ADD gitlab_to_redmine.py .

ENTRYPOINT python gitlab_to_redmine.py
