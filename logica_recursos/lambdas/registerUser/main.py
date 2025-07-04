# logica_recursos/lambdas/registerUser/main.py
import json
import os
import boto3
import uuid
from boto3.dynamodb.conditions import Key

def handler(event, context):
    dynamodb = boto3.resource('dynamodb')
    table_name = os.environ.get('DYNAMODB_TABLE_NAME')
    table = dynamodb.Table(table_name)
    log_data = {"function_name": context.function_name, "aws_request_id": context.aws_request_id}
    print(json.dumps({"level": "INFO", "message": "Request received", "details": log_data}))

    try:
        body = json.loads(event.get('body', '{}'))
        user_name = body.get('name')
        user_email = body.get('email')
        log_data["user_email"] = user_email

        if not user_name or not user_email:
            # ... (código de validación igual que antes)
            return {'statusCode': 400, 'body': json.dumps({'error': 'Name and email are required'})}

        # --- LÓGICA DE VERIFICACIÓN ---
        response = table.query(
            IndexName='EmailIndex',
            KeyConditionExpression=Key('email').eq(user_email)
        )

        if response['Items']:
            print(json.dumps({"level": "WARN", "message": "User with this email already exists", "details": log_data}))
            # Devolver el usuario existente en lugar de crear uno nuevo
            existing_user = response['Items'][0]
            return {
                'statusCode': 200, # O 409 Conflict, pero 200 es más simple para el cliente
                'body': json.dumps({'userId': existing_user['userId'], 'message': 'User already exists'})
            }
        # --- FIN DE LA LÓGICA DE VERIFICACIÓN ---

        user_id = str(uuid.uuid4())
        item = {
            'PK': f"USER#{user_id}",
            'SK': f"PROFILE#{user_email}",
            'userId': user_id,
            'name': user_name,
            'email': user_email,
            'createdAt': context.aws_request_id
        }

        table.put_item(Item=item)
        print(json.dumps({"level": "INFO", "message": "Successfully created new user", "details": log_data}))

        return {
            'statusCode': 201,
            'headers': {"Content-Type": "application/json"},
            'body': json.dumps({'userId': user_id, 'message': 'User created successfully'})
        }

    except Exception as e:
        # ... (código de manejo de errores igual que antes)
        return {'statusCode': 500, 'body': json.dumps({'error': 'Internal Server Error'})}
