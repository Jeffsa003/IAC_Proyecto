# logica_recursos/lambdas/sendEmail/main.py
import json
import os
import boto3

def handler(event, context):
    """
    Processes messages from an SQS queue and sends emails using SES.
    """
    ses_client = boto3.client('ses')
    SENDER_EMAIL = os.environ.get('SENDER_EMAIL')
    log_data = {"function_name": context.function_name, "aws_request_id": context.aws_request_id, "event": event}
    print(json.dumps({"level": "INFO", "message": "Request received", "details": log_data}))

    for record in event['Records']:
        message_id = record.get('messageId', 'N/A')
        log_data["sqs_message_id"] = message_id
        
        try:
            message_body = json.loads(record['body'])
            recipient_email = message_body.get('recipient')
            subject = message_body.get('subject')
            body_text = message_body.get('body_text')
            body_html = message_body.get('body_html')

            log_data["email_recipient"] = recipient_email
            log_data["email_subject"] = subject

            if not all([recipient_email, subject, body_text, body_html]):
                print(json.dumps({"level": "WARN", "message": "Skipping malformed message", "details": log_data}))
                continue

            print(json.dumps({"level": "INFO", "message": "Sending email via SES", "details": log_data}))
            ses_client.send_email(
                Source=SENDER_EMAIL,
                Destination={'ToAddresses': [recipient_email]},
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': {
                        'Text': {'Data': body_text, 'Charset': 'UTF-8'},
                        'Html': {'Data': body_html, 'Charset': 'UTF-8'}
                    }
                }
            )
            print(json.dumps({"level": "INFO", "message": "Successfully sent email", "details": log_data}))

        except Exception as e:
            log_data["error"] = str(e)
            print(json.dumps({"level": "ERROR", "message": "Error processing SQS message", "details": log_data}))
            pass
    
    return {
        'statusCode': 200,
        'body': json.dumps('Finished processing messages.')
    }