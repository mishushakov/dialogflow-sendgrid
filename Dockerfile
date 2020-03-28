FROM python:alpine

ADD inbox.py .
ADD requirements.txt .

ENV INBOX_USER apikey
ENV INBOX_HOST smtp.sendgrid.net
ENV FALLBACK_LANG en
ENV ENDPOINT https://*.core.ushaflow.io
ENV ENDPOINT_SSR https://*.ssr.ushaflow.io
ENV DEBUG false
ENV PORT 5000

RUN pip install -r requirements.txt

ENTRYPOINT python inbox.py