# logica_recursos/lambdas/generateCertificate/main.py
import json
import os
import boto3

def handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    sqs_client = boto3.client('sqs')

    table_name = os.environ.get('DYNAMODB_TABLE_NAME')
    queue_url = os.environ.get('SQS_QUEUE_URL')
    table = dynamodb.Table(table_name)
    log_data = {"function_name": context.function_name, "aws_request_id": context.aws_request_id}
    print(json.dumps({"level": "INFO", "message": "Request received", "details": log_data}))

    try:
        authorizer_claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        user_id = authorizer_claims.get('sub')
        user_email = authorizer_claims.get('email') # El email está en los claims

        if not user_id or not user_email:
            raise Exception("User ID or email not found in token")
        
        log_data.update({"user_id": user_id, "user_email": user_email})

        body = json.loads(event.get('body', '{}'))
        course_id = body.get('courseId')
        log_data["course_id"] = course_id

        if not course_id:
            return {'statusCode': 400, 'body': json.dumps({'error': 'courseId is required'})}

        enrollment_key = {'PK': f"USER#{user_id}", 'SK': f"ENROLLMENT#{course_id}"}
        enrollment_item = table.get_item(Key=enrollment_key).get('Item')

        if not enrollment_item or enrollment_item.get('progress', 0) < 100:
            return {'statusCode': 400, 'body': json.dumps({'error': 'Course not completed yet'})}
        
        course_title = table.get_item(Key={'PK': f"COURSE#{course_id}", 'SK': 'METADATA'}).get('Item', {}).get('title', 'Curso Desconocido')
        log_data["course_title"] = course_title

        message_body = {
            'recipient': user_email,
            'subject': f"¡Felicidades! Tu certificado para {course_title}",
            'body_text': f"Hola,\n\nHas completado con éxito el curso '{course_title}'. ¡Adjunto encontrarás tu certificado! (Simulado)\n\nSaludos,\nEl Equipo de Elearning.",
            'body_html': f"<html><body><h2>¡Felicidades!</h2><p>Has completado con éxito el curso <strong>{course_title}</strong>. ¡Adjunto encontrarás tu certificado! (Simulado)</p><p>Saludos,<br>El Equipo de Elearning.</p></body></html>"
        }
        
        print(json.dumps({"level": "INFO", "message": "Sending certificate request to SQS", "details": log_data}))
        sqs_client.send_message(QueueUrl=queue_url, MessageBody=json.dumps(message_body))
        print(json.dumps({"level": "INFO", "message": "Successfully sent message to SQS", "details": log_data}))

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Certificate generation initiated. You will receive it by email.'})
        }

    except Exception as e:
        log_data["error"] = str(e)
        print(json.dumps({"level": "ERROR", "message": "Error processing request", "details": log_data}))
        return {'statusCode': 500, 'body': json.dumps({'error': 'Internal Server Error'})}