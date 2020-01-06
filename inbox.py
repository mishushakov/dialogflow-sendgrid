#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import smtplib
import requests

from flask import Flask, request
from email import message_from_string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import parseaddr, make_msgid
from langdetect import detect
from email_reply_parser import EmailReplyParser

# Retrieve environment variables
username = os.environ['INBOX_USER']
password = os.environ['INBOX_PASSWORD']
host = os.environ['INBOX_HOST']
gateway = os.environ['GATEWAY']

app = Flask(__name__)

# Handle POST request from Webhook
@app.route('/', methods=['POST'])
def inbox():
    # Parse E-Mail
    raw_email = request.form.to_dict()['email']
    parsed_email = message_from_string(raw_email)
    parsed_email_from = parseaddr(parsed_email['From'])[1]
    parsed_email_to = parseaddr(parsed_email['To'])[1]
    parsed_email_body = ''
    for part in parsed_email.walk():
        if part.get_content_type() == 'text/plain':
            parsed_email_body += part.get_payload()

    parsed_email_body = EmailReplyParser.parse_reply(parsed_email_body)

    # Log E-Mail
    app.logger.info('Received new E-Mail')
    app.logger.info('From: ' + parsed_email_from)
    app.logger.info('To: ' + parsed_email_to)
    app.logger.info('Subject: ' + parsed_email['Subject'])
    app.logger.info('Text: ' + parsed_email_body)
    app.logger.info('Message ID: ' + parsed_email['Message-ID'])

    # Build Dialogflow Gateway Request
    agent_id = parsed_email_to.split('@')[0]
    req = {
        'session': parsed_email_from,
        'queryInput': {
            'text': {
                'text': parsed_email_body,
                'languageCode': detect(parsed_email_body)
            }
        }
    }

    # Make the request
    baseurl = agent_id + '.gateway.dialogflow.cloud.ushakov.co'
    agent = requests.get(gateway, headers={'Host': baseurl})
    r = requests.post(gateway, headers={'Host': baseurl}, json=req)
    if r.status_code == 200:
        # Make new E-Mail for the response
        message = MIMEMultipart()
        message['Message-ID'] = make_msgid()
        message['In-Reply-To'] = parsed_email['Message-ID']
        message['References'] = parsed_email['Message-ID']
        message['From'] = (agent.json()['displayName'] + ' <' + parsed_email_to + '>') or parsed_email['To']
        message['To'] = parsed_email['From']
        message['Subject'] = parsed_email['Subject']

        # Attach the components
        result = r.json()['queryResult']
        if 'fulfillmentMessages' in result:
            for component in result['fulfillmentMessages']:
                if 'text' in component:
                    message.attach(MIMEText(component['text']['text'][0], 'plain'))
                elif 'simpleResponses' in component:
                    message.attach(MIMEText(component['simpleResponses']['simpleResponses'][0]['textToSpeech'], 'plain'))

        if 'webhookPayload' in result:
            if 'google' in result['webhookPayload']:
                for component in result['webhookPayload']['google']['richResponse']['items']:
                    if 'simpleResponse' in component:
                        message.attach(MIMEText(component['simpleResponse']['textToSpeech'], 'plain'))

        message.attach(MIMEText('<br><br>Powered by <a href="https://dialogflow.cloud.ushakov.co">Dialogflow Gateway</a>', 'html'))

        # Connect to SMTP and send the E-Mail
        session = smtplib.SMTP(host, 587)
        session.ehlo()
        session.starttls()
        session.ehlo()

        session.login(username, password)
        session.sendmail(parsed_email['To'], parsed_email['From'], message.as_string())
        session.quit()

        # Log response status
        app.logger.info('E-Mail response sent to ' + parsed_email_from)
    else:
        # Log request error
        app.logger.error('Dialogflow Gateway request failed')
        app.logger.error('Status: ' + r.status_code)
        app.logger.error('Error: ' + r.json())

    return "OK", 200

if __name__ == '__main__':
    app.run()