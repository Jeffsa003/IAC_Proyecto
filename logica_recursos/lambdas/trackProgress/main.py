# logica_recursos/lambdas/trackProgress/main.py
import json
import os
import boto3
from decimal import Decimal

# Clase para ayudar a serializar objetos Decimal de DynamoDB a JSON
class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            if o % 1 > 0:
                return float(o)
            else:
                return int(o)
        return super(DecimalEncoder, self).default(o)

def handler(event, context):
    """
    Updates a user's progress in a course.
    """
    dynamodb = boto3.resource('dynamodb')
    table_name = os.environ.get('DYNAMODB_TABLE_NAME')
    table = dynamodb.Table(table_name)
    log_data = {"function_name": context.function_name, "aws_request_id": context.aws_request_id}
    print(json.dumps({"level": "INFO", "message": "Request received"}, cls=DecimalEncoder))

    try:
        authorizer_claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        user_id = authorizer_claims.get('sub')
        
        if not user_id:
            raise Exception("User ID not found in token")

        body = json.loads(event.get('body', '{}'))
        course_id = body.get('courseId')
        progress = body.get('progress')
        log_data.update({"user_id": user_id, "course_id": course_id, "progress": progress})

        if not course_id or progress is None:
            print(json.dumps({"level": "WARN", "message": "Validation failed: missing fields", "details": log_data}, cls=DecimalEncoder))
            return {'statusCode': 400, 'body': json.dumps({'error': 'courseId and progress are required'})}

        if not isinstance(progress, (int, float)) or not (0 <= progress <= 100):
            print(json.dumps({"level": "WARN", "message": "Validation failed: invalid progress value", "details": log_data}, cls=DecimalEncoder))
            return {'statusCode': 400, 'body': json.dumps({'error': 'Progress must be a number between 0 and 100'})}

        key = {'PK': f"USER#{user_id}", 'SK': f"ENROLLMENT#{course_id}"}
        update_expression = "SET progress = :p"
        expression_attribute_values = {":p": Decimal(str(progress))} # Usar Decimal para la actualización

        print(json.dumps({"level": "INFO", "message": "Updating progress in DynamoDB", "details": log_data}, cls=DecimalEncoder))
        response = table.update_item(
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ReturnValues="UPDATED_NEW"
        )
        
        log_data["dynamodb_response"] = response.get('Attributes')
        print(json.dumps({"level": "INFO", "message": "Successfully updated progress", "details": log_data}, cls=DecimalEncoder))

        return {
            'statusCode': 200,
            'headers': {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            'body': json.dumps({'message': 'Progress updated successfully'})
        }

    except Exception as e:
        log_data["error"] = str(e)
        print(json.dumps({"level": "ERROR", "message": "Error processing request", "details": log_data}, cls=DecimalEncoder))
        return {'statusCode': 500, 'body': json.dumps({'error': 'Internal Server Error'})}
