import pytest
import json
from unittest.mock import patch, MagicMock
import os
from logica_recursos.lambdas.generateUploadUrl.main import handler

os.environ['ORIGINAL_VIDEOS_BUCKET_NAME'] = 'test-bucket'

@pytest.fixture
def mock_s3_client():
    with patch('boto3.client') as mock_client:
        yield mock_client

@pytest.fixture
def api_gateway_event():
    return {
        'body': json.dumps({
            'fileName': 'video.mp4',
            'fileType': 'video/mp4'
        })
    }

def test_generate_url_success(mock_s3_client, api_gateway_event):
    """Prueba la generación exitosa de una URL prefirmada."""
    test_url = "https://s3.test.com/upload-here"
    mock_s3_client.return_value.generate_presigned_url.return_value = test_url
    
    context = MagicMock()
    context.function_name = "generateUploadUrl"
    context.aws_request_id = "test-request-id"
    response = handler(api_gateway_event, context)

    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['uploadUrl'] == test_url
    assert 'key' in body
    mock_s3_client.return_value.generate_presigned_url.assert_called_once()

def test_generate_url_missing_fields(mock_s3_client):
    """Prueba la llamada con campos faltantes."""
    event = {'body': json.dumps({'fileName': 'video.mp4'})} # Falta fileType
    context = MagicMock()
    context.function_name = "generateUploadUrl"
    context.aws_request_id = "test-request-id"
    response = handler(event, context)

    assert response['statusCode'] == 400
    assert 'fileName and fileType are required' in response['body']
    mock_s3_client.return_value.generate_presigned_url.assert_not_called()

def test_generate_url_s3_error(mock_s3_client, api_gateway_event):
    """Prueba el manejo de errores del cliente S3."""
    from botocore.exceptions import ClientError
    mock_s3_client.return_value.generate_presigned_url.side_effect = ClientError({'Error': {'Code': '500', 'Message': 'S3 Error'}}, 'generate_presigned_url')
    
    context = MagicMock()
    context.function_name = "generateUploadUrl"
    context.aws_request_id = "test-request-id"
    response = handler(api_gateway_event, context)

    assert response['statusCode'] == 500
    assert 'Could not generate upload URL' in response['body']


def test_generate_url_unexpected_error(mock_s3_client, api_gateway_event):
    """Prueba el manejo de errores inesperados."""
    mock_s3_client.return_value.generate_presigned_url.side_effect = Exception("Unexpected error")
    
    context = MagicMock()
    context.function_name = "generateUploadUrl"
    context.aws_request_id = "test-request-id"
    response = handler(api_gateway_event, context)

    assert response['statusCode'] == 500
    assert 'Internal Server Error' in response['body']
