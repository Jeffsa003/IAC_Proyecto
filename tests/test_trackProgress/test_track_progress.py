import pytest
import json
from unittest.mock import patch, MagicMock
import os
from decimal import Decimal
from logica_recursos.lambdas.trackProgress.main import handler

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
def api_event():
    return {
        'requestContext': {'authorizer': {'claims': {'sub': 'user-123'}}},
        'body': json.dumps({'courseId': 'course-abc', 'progress': 50})
    }

def test_track_progress_success(mock_dynamodb_table, api_event):
    """Prueba la actualización de progreso exitosa."""
    mock_dynamodb_table.update_item.return_value = {'Attributes': {'progress': Decimal('50')}}
    context = MagicMock()
    context.function_name = "trackProgress"
    context.aws_request_id = "test-request-id"
    response = handler(api_event, context)

    assert response['statusCode'] == 200
    assert 'Progress updated successfully' in response['body']
    mock_dynamodb_table.update_item.assert_called_once()
    
    call_kwargs = mock_dynamodb_table.update_item.call_args.kwargs
    assert call_kwargs['Key'] == {'PK': 'USER#user-123', 'SK': 'ENROLLMENT#course-abc'}
    assert call_kwargs['UpdateExpression'] == "SET progress = :p"
    assert call_kwargs['ExpressionAttributeValues'] == {":p": Decimal('50')}

def test_track_progress_invalid_value(mock_dynamodb_table, api_event):
    """Prueba la actualización con un valor de progreso inválido."""
    api_event['body'] = json.dumps({'courseId': 'course-abc', 'progress': 101})
    context = MagicMock()
    context.function_name = "trackProgress"
    context.aws_request_id = "test-request-id"
    response = handler(api_event, context)

    assert response['statusCode'] == 400
    assert 'Progress must be a number between 0 and 100' in response['body']
    mock_dynamodb_table.update_item.assert_not_called()


def test_track_progress_missing_fields(mock_dynamodb_table, api_event):
    """Prueba la actualización con campos faltantes."""
    api_event['body'] = json.dumps({'courseId': 'course-abc'})
    context = MagicMock()
    context.function_name = "trackProgress"
    context.aws_request_id = "test-request-id"
    response = handler(api_event, context)

    assert response['statusCode'] == 400
    assert 'courseId and progress are required' in response['body']
    mock_dynamodb_table.update_item.assert_not_called()


def test_track_progress_dynamodb_error(mock_dynamodb_table, api_event):
    """Prueba el manejo de un error de DynamoDB."""
    mock_dynamodb_table.update_item.side_effect = Exception("DynamoDB Error")
    context = MagicMock()
    context.function_name = "trackProgress"
    context.aws_request_id = "test-request-id"
    response = handler(api_event, context)

    assert response['statusCode'] == 500
    assert 'Internal Server Error' in response['body']
    mock_dynamodb_table.update_item.assert_called_once()