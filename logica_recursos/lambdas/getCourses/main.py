# logica_recursos/lambdas/getCourses/main.py
import json
import os
import boto3

def handler(event, context):
    """
    Fetches all courses from the DynamoDB table.
    """
    # Inicializar el cliente de DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table_name = os.environ.get('DYNAMODB_TABLE_NAME', 'ElearningPlatformTable')
    table = dynamodb.Table(table_name)
    log_data = {"event": event, "function_name": context.function_name, "aws_request_id": context.aws_request_id}
    print(json.dumps({"level": "INFO", "message": "Request received", "details": log_data}))

    try:
        response = table.scan()
        courses = response.get('Items', [])
        
        print(json.dumps({"level": "INFO", "message": "Successfully scanned courses", "details": {"course_count": len(courses)}}))

        return {
            'statusCode': 200,
            'headers': {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            'body': json.dumps(courses)
        }
    except Exception as e:
        log_data["error"] = str(e)
        print(json.dumps({"level": "ERROR", "message": "Failed to scan DynamoDB table", "details": log_data}))
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal Server Error'})
        }