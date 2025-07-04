import pytest
import json
from unittest.mock import patch, MagicMock
import os
from logica_recursos.lambdas.updateVideoStatus.main import handler

os.environ['DYNAMODB_TABLE_NAME'] = 'test-table'

@pytest.fixture
def mock_dynamodb_table():
    with patch('boto3.resource') as mock_boto3_resource:
        mock_dynamodb = MagicMock()
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_dynamodb
        yield mock_table

@pytest.fixture
def mediaconvert_event():
    """Genera un evento de MediaConvert de ejemplo."""
    return {
        "detail": {
            "status": "COMPLETE",
            "jobId": "12345",
            "userMetadata": {
                "sourceObjectKey": "uploads/video.mp4"
            }
        }
    }

def test_update_status_success(mock_dynamodb_table, mediaconvert_event):
    """Prueba la actualización de estado exitosa (simulada)."""
    context = MagicMock()
    context.function_name = "updateVideoStatus"
    context.aws_request_id = "test-request-id"
    response = handler(mediaconvert_event, context)

    assert response['statusCode'] == 200
    assert 'Processed status COMPLETE for job 12345' in response['body']
    
    # Como la actualización está comentada, verificamos que no se llama
    mock_dynamodb_table.update_item.assert_not_called()

def test_update_status_error_event(mock_dynamodb_table):
    """Prueba el manejo de un evento malformado."""
    event = {"detail": {"status": "ERROR"}} # Falta userMetadata
    
    with pytest.raises(Exception):
        context = MagicMock()
        context.function_name = "updateVideoStatus"
        context.aws_request_id = "test-request-id"
        handler(event, context)
    
    mock_dynamodb_table.update_item.assert_not_called()


def test_update_status_failed_job(mock_dynamodb_table, mediaconvert_event):
    """Prueba el manejo de un trabajo fallido."""
    mediaconvert_event['detail']['status'] = 'ERROR'
    context = MagicMock()
    context.function_name = "updateVideoStatus"
    context.aws_request_id = "test-request-id"
    response = handler(mediaconvert_event, context)

    assert response['statusCode'] == 200
    assert 'Processed status ERROR for job 12345' in response['body']
    mock_dynamodb_table.update_item.assert_not_called()
