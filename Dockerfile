FROM python:alpine

ADD inbox.py .
ADD requirements.txt .
RUN pip install -r requirements.txt

ENTRYPOINT python inbox.py