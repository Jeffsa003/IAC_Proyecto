# logica_recursos/lambdas/purchaseCourse/main.py
import json
import os
import boto3
import uuid
import time

def handler(event, context):
    """
    Handles a course purchase.
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
            print(json.dumps({"level": "WARN", "message": "Validation failed: courseId is required", "details": log_data}))
            return {'statusCode': 400, 'body': json.dumps({'error': 'courseId is required'})}

        print(json.dumps({"level": "INFO", "message": "Simulating call to Stripe API", "details": log_data}))
        time.sleep(1)
        print(json.dumps({"level": "INFO", "message": "Stripe payment successful (simulated)", "details": log_data}))

        purchase_id = str(uuid.uuid4())
        item = {
            'PK': f"USER#{user_id}",
            'SK': f"COURSE#{course_id}",
            'purchaseId': purchase_id,
            'purchasedAt': int(time.time())
        }

        print(json.dumps({"level": "INFO", "message": "Recording purchase in DynamoDB", "details": log_data}))
        table.put_item(Item=item)
        print(json.dumps({"level": "INFO", "message": "Successfully recorded purchase", "details": log_data}))

        return {
            'statusCode': 201,
            'headers': {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            'body': json.dumps({'purchaseId': purchase_id, 'message': 'Course purchased successfully'})
        }

    except Exception as e:
        log_data["error"] = str(e)
        print(json.dumps({"level": "ERROR", "message": "Error processing request", "details": log_data}))
        return {'statusCode': 500, 'body': json.dumps({'error': 'Internal Server Error'})}