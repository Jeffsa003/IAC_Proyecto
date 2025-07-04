import pytest
import json
from unittest.mock import patch, MagicMock
import os
from logica_recursos.lambdas.createCourse.main import handler

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
        'body': json.dumps({
            'title': 'New Course',
            'description': 'A great course.'
        }),
        'requestContext': {
            'authorizer': {
                'claims': {
                    'sub': 'test-user-id'
                }
            }
        }
    }

def test_create_course_success(mock_dynamodb_table, api_event):
    """Prueba la creación de un curso exitosa."""
    context = MagicMock()
    context.function_name = "createCourse"
    context.aws_request_id = "test-request-id"
    response = handler(api_event, context)

    assert response['statusCode'] == 201
    body = json.loads(response['body'])
    assert 'courseId' in body
    mock_dynamodb_table.put_item.assert_called_once()
    
    item = mock_dynamodb_table.put_item.call_args.kwargs['Item']
    assert item['title'] == 'New Course'
    assert item['SK'] == 'METADATA'

def test_create_course_missing_fields(mock_dynamodb_table):
    """Prueba la creación de un curso con campos faltantes."""
    event = {'body': json.dumps({'title': 'Incomplete Course'})}
    context = MagicMock()
    context.function_name = "createCourse"
    context.aws_request_id = "test-request-id"
    response = handler(event, context)

    assert response['statusCode'] == 400
    assert 'Title and description are required' in response['body']
    mock_dynamodb_table.put_item.assert_not_called()


def test_create_course_internal_error(mock_dynamodb_table, api_event):
    """Prueba el manejo de un error interno del servidor."""
    mock_dynamodb_table.put_item.side_effect = Exception("Internal error")
    context = MagicMock()
    context.function_name = "createCourse"
    context.aws_request_id = "test-request-id"
    response = handler(api_event, context)

    assert response['statusCode'] == 500
    assert 'Internal Server Error' in response['body']
    mock_dynamodb_table.put_item.assert_called_once()