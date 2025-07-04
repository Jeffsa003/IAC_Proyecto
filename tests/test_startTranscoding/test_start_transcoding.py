import pytest
import json
from unittest.mock import patch, MagicMock
import os
from logica_recursos.lambdas.startTranscoding.main import handler

# Establecer variables de entorno simuladas
os.environ['TRANSCODED_VIDEOS_BUCKET_NAME'] = 'test-transcoded-bucket'
os.environ['MEDIACONVERT_ROLE_ARN'] = 'arn:aws:iam::123456789012:role/MediaConvertRole'

@pytest.fixture
def mock_boto3_client():
    """Fixture para simular el cliente de boto3."""
    with patch('boto3.client') as mock_client_constructor:
        mock_mc_client = MagicMock()
        mock_mc_discovery_client = MagicMock()
        mock_mc_discovery_client.describe_endpoints.return_value = {'Endpoints': [{'Url': 'https://mediaconvert.test.com'}]}
        
        # El constructor devuelve diferentes mocks según el servicio
        def client_side_effect(service_name, endpoint_url=None):
            if service_name == 'mediaconvert' and endpoint_url:
                return mock_mc_client
            elif service_name == 'mediaconvert':
                return mock_mc_discovery_client
            return MagicMock()
            
        mock_client_constructor.side_effect = client_side_effect
        yield mock_mc_client

@pytest.fixture
def s3_event():
    """Genera un evento de S3 de ejemplo."""
    return {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": "test-original-bucket"},
                    "object": {"key": "uploads/video.mp4"}
                }
            }
        ]
    }

def test_start_transcoding_success(mock_boto3_client, s3_event):
    """Prueba el inicio exitoso de un trabajo de transcodificación."""
    context = MagicMock()
    context.function_name = "startTranscoding"
    context.aws_request_id = "test-request-id"
    response = handler(s3_event, context)

    assert response['statusCode'] == 200
    assert 'Transcoding job started successfully' in response['body']
    mock_boto3_client.create_job.assert_called_once()
    
    # Verificar que los datos correctos se pasaron a create_job
    call_args, call_kwargs = mock_boto3_client.create_job.call_args
    assert call_kwargs['Role'] == 'arn:aws:iam::123456789012:role/MediaConvertRole'
    assert call_kwargs['Settings']['Inputs'][0]['FileInput'] == 's3://test-original-bucket/uploads/video.mp4'
    assert 'UserMetadata' in call_kwargs
    assert call_kwargs['UserMetadata']['sourceObjectKey'] == 'uploads/video.mp4'

def test_start_transcoding_mediaconvert_error(mock_boto3_client, s3_event):
    """Prueba el manejo de errores al crear el trabajo en MediaConvert."""
    mock_boto3_client.create_job.side_effect = Exception("MediaConvert Error")

    with pytest.raises(Exception, match="MediaConvert Error"):
        context = MagicMock()
        context.function_name = "startTranscoding"
        context.aws_request_id = "test-request-id"
        handler(s3_event, context)


def test_start_transcoding_no_s3_event(mock_boto3_client):
    """Prueba el manejo de un evento sin la estructura esperada de S3."""
    with pytest.raises(KeyError):
        context = MagicMock()
        context.function_name = "startTranscoding"
        context.aws_request_id = "test-request-id"
        handler({"Records": [{}]}, context)
