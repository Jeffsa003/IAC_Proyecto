import pytest
import json
from unittest.mock import patch, MagicMock
import os
from logica_recursos.lambdas.registerUser.main import handler

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
def api_gateway_event():
    """Genera un evento de API Gateway de ejemplo."""
    return {
        'body': json.dumps({
            'name': 'Test User',
            'email': 'test@example.com'
        })
    }

def test_register_user_success(mock_dynamodb_table, api_gateway_event):
    """Prueba el registro de usuario exitoso."""
    mock_dynamodb_table.query.return_value = {'Items': []}
    context = MagicMock()
    context.function_name = "registerUser"
    context.aws_request_id = "test-request-id"
    response = handler(api_gateway_event, context)

    assert response['statusCode'] == 201
    body = json.loads(response['body'])
    assert 'userId' in body
    assert body['message'] == 'User created successfully'
    mock_dynamodb_table.put_item.assert_called_once()

def test_register_user_missing_fields(mock_dynamodb_table):
    """Prueba el registro de usuario con campos faltantes."""
    event = {'body': json.dumps({'name': 'Test User'})} # Falta el email
    context = MagicMock()
    context.function_name = "registerUser"
    context.aws_request_id = "test-request-id"
    response = handler(event, context)

    assert response['statusCode'] == 400
    assert 'Name and email are required' in response['body']
    mock_dynamodb_table.put_item.assert_not_called()

def test_register_user_dynamodb_error(mock_dynamodb_table, api_gateway_event):
    """Prueba el manejo de errores de DynamoDB."""
    mock_dynamodb_table.query.side_effect = Exception("DynamoDB Error")
    context = MagicMock()
    context.function_name = "registerUser"
    context.aws_request_id = "test-request-id"
    response = handler(api_gateway_event, context)

    assert response['statusCode'] == 500
    assert 'Internal Server Error' in response['body']


def test_register_user_already_exists(mock_dynamodb_table, api_gateway_event):
    """Prueba que no se crea un usuario si el email ya existe."""
    # Simular que la consulta a DynamoDB encuentra un usuario
    mock_dynamodb_table.query.return_value = {
        'Items': [{'userId': 'existing-user-123', 'email': 'test@example.com'}]
    }
    
    context = MagicMock()
    context.function_name = "registerUser"
    context.aws_request_id = "test-request-id"
    response = handler(api_gateway_event, context)

    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['userId'] == 'existing-user-123'
    assert 'User already exists' in body['message']
    mock_dynamodb_table.put_item.assert_not_called()