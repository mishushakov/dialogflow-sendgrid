# Dialogflow Sendgrid

Mail your Dialogflow Agents with Sendgrid

For features and drawbacks, see the [original repo](https://github.com/mishushakov/dialogflow-inbox)

## Schema

![](https://i.imgur.com/CgnAVrU.png)

## Setup

### Preparation

1. Connect your Agents to a Dialogflow Gateway implementation ([more here](https://github.com/mishushakov/dialogflow-gateway-docs))
2. [Make a SendGrid account](https://app.sendgrid.com/login)
3. Visit "Settings" > "Sender Authentication" and "Authenticate Your Domain":

   ![](https://i.imgur.com/lYuGzes.png)

4. Verify your DNS records:

   ![](https://i.imgur.com/fZMNRGW.png)

5. Go to "API Keys" and generate API Key with full access to "Mail Send":

    ![](https://i.imgur.com/02UDY86.png)

6. Install Dialogflow Sendgrid (below) and add "Inbound Parse" entry in "Settings" with following options:

    ![](https://i.imgur.com/yhB0b5H.png)

    - Receiving Domain: your domain
    - Destination URL: endpoint to Dialogflow Sendgrid
    - Check incoming emails for spam: up to you
    - POST the raw, full MIME message: yes (check)

### Installation

#### Kubernetes

See [k8s](k8s) for examples

#### Manual

1. Python should be installed on the target
2. Install the requirements with `pip install -r requirements.txt`
3. Run `python inbox.py`

### Configuration

| Environment Variable | Description                                                   | Value                        |
|----------------------|---------------------------------------------------------------|------------------------------|
| INBOX_USER           | Sendgrid user                                                 | apikey                       |
| INBOX_PASSWORD       | Sendgrid API Key                                              | -                            |
| INBOX_HOST           | SMTP and IMAP server hostname                                 | smtp.sendgrid.net            |
| FALLBACK_LANG        | Fallback language if language detection fails                 | en                           |
| ENDPOINT             | Dialogflow Gateway Endpoint. {} fills Google Cloud project id | https://{}.core.ushaflow.com |
| DEBUG                | Debug mode                                                    | true                         |
| PORT                 | Listen on port                                                | 5000                         |

### Testing

Send a test mail to a agent in the following format: your-google-cloud-project-id@yourdomain