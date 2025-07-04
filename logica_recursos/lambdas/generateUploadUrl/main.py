# logica_recursos/lambdas/generateUploadUrl/main.py
import json
import os
import boto3
import uuid
from botocore.exceptions import ClientError

def handler(event, context):
    """
    Generates a pre-signed URL for uploading a video to S3.
    """
    s3_client = boto3.client('s3')
    bucket_name = os.environ.get('ORIGINAL_VIDEOS_BUCKET_NAME')
    log_data = {"function_name": context.function_name, "aws_request_id": context.aws_request_id}
    print(json.dumps({"level": "INFO", "message": "Request received", "details": log_data}))

    try:
        body = json.loads(event.get('body', '{}'))
        file_name = body.get('fileName')
        file_type = body.get('fileType')
        log_data.update({"file_name": file_name, "file_type": file_type})

        if not file_name or not file_type:
            print(json.dumps({"level": "WARN", "message": "Validation failed", "details": log_data}))
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'fileName and fileType are required'})
            }

        object_key = f"uploads/{uuid.uuid4()}-{file_name}"
        log_data["object_key"] = object_key

        print(json.dumps({"level": "INFO", "message": "Generating pre-signed URL", "details": log_data}))
        
        presigned_url = s3_client.generate_presigned_url(
            'put_object',
            Params={'Bucket': bucket_name, 'Key': object_key, 'ContentType': file_type},
            ExpiresIn=3600
        )

        print(json.dumps({"level": "INFO", "message": "Successfully generated pre-signed URL", "details": log_data}))

        return {
            'statusCode': 200,
            'headers': {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            'body': json.dumps({'uploadUrl': presigned_url, 'key': object_key})
        }

    except ClientError as e:
        log_data["error"] = str(e)
        print(json.dumps({"level": "ERROR", "message": "Error generating pre-signed URL", "details": log_data}))
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Could not generate upload URL'})
        }
    except Exception as e:
        log_data["error"] = str(e)
        print(json.dumps({"level": "ERROR", "message": "An unexpected error occurred", "details": log_data}))
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal Server Error'})
        }