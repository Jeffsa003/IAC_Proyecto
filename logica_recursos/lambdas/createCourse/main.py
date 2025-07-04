# logica_recursos/lambdas/createCourse/main.py
import json
import os
import boto3
import uuid
import time

def handler(event, context):
    """
    Creates a new course.
    """
    dynamodb = boto3.resource('dynamodb')
    table_name = os.environ.get('DYNAMODB_TABLE_NAME')
    table = dynamodb.Table(table_name)
    log_data = {"function_name": context.function_name, "aws_request_id": context.aws_request_id}
    print(json.dumps({"level": "INFO", "message": "Request received", "details": log_data}))

    try:
        body = json.loads(event.get('body', '{}'))
        title = body.get('title')
        description = body.get('description')
        log_data.update({"title": title, "description": description})

        if not title or not description:
            print(json.dumps({"level": "WARN", "message": "Validation failed", "details": log_data}))
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Title and description are required'})
            }

        course_id = str(uuid.uuid4())
        item = {
            'PK': f"COURSE#{course_id}",
            'SK': "METADATA",
            'courseId': course_id,
            'title': title,
            'description': description,
            'createdAt': int(time.time())
        }

        log_data["item_to_put"] = item
        print(json.dumps({"level": "INFO", "message": "Creating course item in DynamoDB", "details": log_data}))
        table.put_item(Item=item)
        print(json.dumps({"level": "INFO", "message": "Successfully created course", "details": log_data}))

        return {
            'statusCode': 201,
            'headers': {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            'body': json.dumps({'courseId': course_id, 'message': 'Course created successfully'})
        }

    except Exception as e:
        log_data["error"] = str(e)
        print(json.dumps({"level": "ERROR", "message": "Error processing request", "details": log_data}))
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal Server Error'})
        }