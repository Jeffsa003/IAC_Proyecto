import pytest
import json
from unittest.mock import patch, MagicMock
import os
from logica_recursos.lambdas.purchaseCourse.main import handler

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
    """Genera un evento de API Gateway con contexto de autorizador."""
    return {
        'requestContext': {
            'authorizer': {
                'claims': {
                    'sub': 'user-123'
                }
            }
        },
        'body': json.dumps({
            'courseId': 'course-abc'
        })
    }

def test_purchase_course_success(mock_dynamodb_table, api_event):
    """Prueba la compra de un curso exitosa."""
    context = MagicMock()
    context.function_name = "purchaseCourse"
    context.aws_request_id = "test-request-id"
    response = handler(api_event, context)

    assert response['statusCode'] == 201
    body = json.loads(response['body'])
    assert 'purchaseId' in body
    assert body['message'] == 'Course purchased successfully'
    mock_dynamodb_table.put_item.assert_called_once()
    
    # Verificar que el item guardado es correcto
    call_args, call_kwargs = mock_dynamodb_table.put_item.call_args
    item = call_kwargs['Item']
    assert item['PK'] == 'USER#user-123'
    assert item['SK'] == 'COURSE#course-abc'

def test_purchase_course_no_course_id(mock_dynamodb_table, api_event):
    """Prueba el caso en que falta el courseId."""
    api_event['body'] = json.dumps({}) # Sin courseId
    context = MagicMock()
    context.function_name = "purchaseCourse"
    context.aws_request_id = "test-request-id"
    response = handler(api_event, context)

    assert response['statusCode'] == 400
    assert 'courseId is required' in response['body']
    mock_dynamodb_table.put_item.assert_not_called()

def test_purchase_course_no_auth(mock_dynamodb_table):
    """Prueba el caso sin información de autenticación."""
    event = {'body': json.dumps({'courseId': 'course-abc'})} # Sin requestContext
    context = MagicMock()
    context.function_name = "purchaseCourse"
    context.aws_request_id = "test-request-id"
    response = handler(event, context)

    assert response['statusCode'] == 500 # Debería ser un error interno por el KeyError
    assert 'Internal Server Error' in response['body']


def test_purchase_course_dynamodb_error(mock_dynamodb_table, api_event):
    """Prueba el manejo de un error de DynamoDB."""
    mock_dynamodb_table.put_item.side_effect = Exception("DynamoDB write error")
    context = MagicMock()
    context.function_name = "purchaseCourse"
    context.aws_request_id = "test-request-id"
    response = handler(api_event, context)

    assert response['statusCode'] == 500
    assert 'Internal Server Error' in response['body']
    mock_dynamodb_table.put_item.assert_called_once()