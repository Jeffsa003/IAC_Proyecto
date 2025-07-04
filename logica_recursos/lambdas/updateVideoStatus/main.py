# logica_recursos/lambdas/updateVideoStatus/main.py
import json
import os
import boto3
from urllib.parse import unquote_plus

def handler(event, context):
    """
    Updates the video status in DynamoDB based on MediaConvert job events.
    """
    dynamodb = boto3.resource('dynamodb')
    table_name = os.environ.get('DYNAMODB_TABLE_NAME')
    table = dynamodb.Table(table_name)
    log_data = {"function_name": context.function_name, "aws_request_id": context.aws_request_id, "event": event}
    print(json.dumps({"level": "INFO", "message": "Request received", "details": log_data}))

    try:
        job_status = event['detail']['status']
        job_id = event['detail']['jobId']
        input_details = event['detail']['userMetadata']
        object_key = unquote_plus(input_details['sourceObjectKey'])

        log_data.update({"job_status": job_status, "job_id": job_id, "object_key": object_key})
        
        # En una implementación real, se buscaría el item del curso/video y se actualizaría.
        print(json.dumps({"level": "INFO", "message": "Video status update processed (simulated)", "details": log_data}))

        return {
            'statusCode': 200,
            'body': json.dumps(f"Processed status {job_status} for job {job_id}")
        }

    except Exception as e:
        log_data["error"] = str(e)
        print(json.dumps({"level": "ERROR", "message": "Error processing MediaConvert event", "details": log_data}))
        raise e