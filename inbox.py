#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import smtplib
import requests

from dotenv import load_dotenv
from flask import Flask, request
from email import message_from_string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import parseaddr, make_msgid
from langdetect import detect
from email_reply_parser import EmailReplyParser

# Retrieve environment variables
load_dotenv()
host = os.environ.get('INBOX_HOST')
user = os.environ.get('INBOX_USER')
password = os.environ.get('INBOX_PASSWORD')
fallback_lang = os.environ.get('FALLBACK_LANG')
catchall = os.environ.get('CATCHALL')
endpoint = os.environ.get('ENDPOINT')
endpoint_ssr = os.environ.get('ENDPOINT_SSR')
debug = os.environ.get('DEBUG') == 'true'
port = int(os.environ.get('PORT'))

app = Flask(__name__)

# Handle POST request from Webhook
@app.route('/', methods=['POST'])
def inbox():
    # Parse E-Mail
    raw_email = request.form.to_dict()['email']
    parsed_email = message_from_string(raw_email)
    parsed_email_from = parseaddr(parsed_email['From'])[1]
    parsed_email_to = parseaddr(parsed_email['To'])[1]
    parsed_email_to_domain = parsed_email_to.split('@')[1]
    parsed_email_body = ''
    for part in parsed_email.walk():
        if part.get_content_type() == 'text/plain':
            parsed_email_body += part.get_payload()

    parsed_email_body = EmailReplyParser.parse_reply(parsed_email_body)
    parsed_email_lang = fallback_lang
    try:
        parsed_email_lang = detect(parsed_email_body)
    except:
        pass

    # Log E-Mail
    app.logger.info('Received new E-Mail')
    app.logger.info('From: ' + parsed_email_from)
    app.logger.info('To: ' + parsed_email_to)
    app.logger.info('Text: ' + parsed_email_body)
    app.logger.info('Message ID: ' + parsed_email['Message-ID'])

    # Build Request
    agent_id = parsed_email_to.split('@')[0]
    req = {
        'session': parsed_email_from,
        'queryInput': {
            'text': {
                'text': parsed_email_body,
                'languageCode': parsed_email_lang
            }
        },
        'queryParams': {
            'payload': {
                'email': {
                    'from': parsed_email_from,
                    'to': parsed_email_to,
                    'subject': parsed_email['Subject'],
                    'body': parsed_email_body
                }
            }
        }
    }

    # Connect to the SMTP Server
    session = smtplib.SMTP(host, 587)
    session.ehlo()
    session.starttls()
    session.ehlo()
    session.login(user, password)

    # Make the request
    agent = requests.get(endpoint.replace('*', agent_id))
    r = requests.post(endpoint_ssr.replace('*', agent_id), json=req)
    if r.status_code == 200:
        # Make new E-Mail for the response
        message = MIMEMultipart()
        message['Message-ID'] = make_msgid()
        message['In-Reply-To'] = parsed_email['Message-ID']
        message['References'] = parsed_email['Message-ID']
        message['From'] = (agent.json()['displayName'] + ' <' + parsed_email_to + '>') or parsed_email['To']
        message['To'] = parsed_email['From']
        message['Subject'] = parsed_email['Subject']

        message.attach(MIMEText(r.text, 'html'))

        # Send the E-Mail
        session.sendmail(message['From'], message['To'], message.as_string())

        # Log response status
        app.logger.info('E-Mail response sent to ' + parsed_email_from)
    elif r.status_code == 404 and catchall:
         # Make new E-Mail for the response
        message = MIMEMultipart()
        message['Message-ID'] = make_msgid()
        message['In-Reply-To'] = parsed_email['Message-ID']
        message['Reply-To'] = parsed_email['From']
        message['References'] = parsed_email['Message-ID']
        message['From'] = 'no-reply@' + parsed_email_to_domain
        message['To'] = catchall
        message['Subject'] = parsed_email['Subject']
        message.attach(MIMEText(parsed_email_body, 'plain'))

        # Send the E-Mail
        session.sendmail(message['From'], message['To'], message.as_string())

        # Log response status
        app.logger.info('E-Mail response sent to ' + parsed_email_from)
    else:
        # Log request error
        app.logger.error('Request failed')
        app.logger.error('Status: ' + str(r.status_code))
        app.logger.error(str(r.json()))

    return "OK", 200

if __name__ == '__main__':
    app.run(debug=debug, host='0.0.0.0', port=port)