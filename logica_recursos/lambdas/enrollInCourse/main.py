# logica_recursos/lambdas/enrollInCourse/main.py
import json
import os
import boto3
import time

def handler(event, context):
    """
    Enrolls a user in a course.
    """
    dynamodb = boto3.resource('dynamodb')
    table_name = os.environ.get('DYNAMODB_TABLE_NAME')
    table = dynamodb.Table(table_name)
    log_data = {"function_name": context.function_name, "aws_request_id": context.aws_request_id}
    print(json.dumps({"level": "INFO", "message": "Request received", "details": log_data}))

    try:
        authorizer_claims = event.get('requestContext', {}).get('authorizer', {}).get('claims', {})
        user_id = authorizer_claims.get('sub')
        
        if not user_id:
            raise Exception("User ID not found in token")

        body = json.loads(event.get('body', '{}'))
        course_id = body.get('courseId')
        log_data.update({"user_id": user_id, "course_id": course_id})

        if not course_id:
            print(json.dumps({"level": "WARN", "message": "Validation failed", "details": log_data}))
            return {'statusCode': 400, 'body': json.dumps({'error': 'courseId is required'})}

        item = {
            'PK': f"USER#{user_id}",
            'SK': f"ENROLLMENT#{course_id}",
            'courseId': course_id,
            'userId': user_id,
            'enrolledAt': int(time.time()),
            'progress': 0
        }

        log_data["item_to_put"] = item
        print(json.dumps({"level": "INFO", "message": "Creating enrollment item in DynamoDB", "details": log_data}))
        table.put_item(Item=item)
        print(json.dumps({"level": "INFO", "message": "Successfully created enrollment", "details": log_data}))

        return {
            'statusCode': 201,
            'headers': {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            'body': json.dumps({'message': 'Successfully enrolled in course'})
        }

    except Exception as e:
        log_data["error"] = str(e)
        print(json.dumps({"level": "ERROR", "message": "Error processing request", "details": log_data}))
        return {'statusCode': 500, 'body': json.dumps({'error': 'Internal Server Error'})}