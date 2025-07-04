import pytest
import json
from unittest.mock import patch, MagicMock
import os
from logica_recursos.lambdas.enrollInCourse.main import handler

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
        'body': json.dumps({'courseId': 'course-abc'})
    }

def test_enroll_success(mock_dynamodb_table, api_event):
    """Prueba la inscripción exitosa en un curso."""
    context = MagicMock()
    context.function_name = "enrollInCourse"
    context.aws_request_id = "test-request-id"
    response = handler(api_event, context)

    assert response['statusCode'] == 201
    assert 'Successfully enrolled in course' in response['body']
    mock_dynamodb_table.put_item.assert_called_once()
    
    item = mock_dynamodb_table.put_item.call_args.kwargs['Item']
    assert item['PK'] == 'USER#user-123'
    assert item['SK'] == 'ENROLLMENT#course-abc'
    assert item['progress'] == 0

def test_enroll_no_course_id(mock_dynamodb_table, api_event):
    """Prueba la inscripción sin un courseId."""
    api_event['body'] = json.dumps({})
    context = MagicMock()
    context.function_name = "enrollInCourse"
    context.aws_request_id = "test-request-id"
    response = handler(api_event, context)

    assert response['statusCode'] == 400
    assert 'courseId is required' in response['body']
    mock_dynamodb_table.put_item.assert_not_called()


def test_enroll_internal_error(mock_dynamodb_table, api_event):
    """Prueba el manejo de un error interno del servidor."""
    mock_dynamodb_table.put_item.side_effect = Exception("Internal error")
    context = MagicMock()
    context.function_name = "enrollInCourse"
    context.aws_request_id = "test-request-id"
    response = handler(api_event, context)

    assert response['statusCode'] == 500
    assert 'Internal Server Error' in response['body']
    mock_dynamodb_table.put_item.assert_called_once()
