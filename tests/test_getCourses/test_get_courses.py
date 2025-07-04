import json
import pytest
from unittest.mock import patch, MagicMock
import os
from logica_recursos.lambdas.getCourses.main import handler

os.environ['DYNAMODB_TABLE_NAME'] = 'test-table'

@pytest.fixture
def mock_dynamodb():
    """Fixture para simular DynamoDB."""
    with patch('boto3.resource') as mock_resource:
        mock_dynamodb_instance = MagicMock()
        mock_table = MagicMock()
        mock_resource.return_value = mock_dynamodb_instance
        mock_dynamodb_instance.Table.return_value = mock_table
        yield mock_table

def test_get_courses_success(mock_dynamodb):
    """Prueba el caso de éxito para obtener cursos."""
    # Configurar el mock para devolver una lista de cursos
    mock_courses = [
        {'id': 'c001', 'title': 'Curso 1'},
        {'id': 'c002', 'title': 'Curso 2'}
    ]
    mock_dynamodb.scan.return_value = {'Items': mock_courses}

    # Llamar al handler
    context = MagicMock()
    context.function_name = "getCourses"
    context.aws_request_id = "test-request-id"
    response = handler({}, context)

    # Verificar la respuesta
    assert response['statusCode'] == 200
    assert response['body'] == json.dumps(mock_courses)
    mock_dynamodb.scan.assert_called_once()

def test_get_courses_dynamodb_error(mock_dynamodb):
    """Prueba el manejo de errores de DynamoDB."""
    # Configurar el mock para que lance una excepción
    mock_dynamodb.scan.side_effect = Exception("DynamoDB Error")

    # Llamar al handler
    context = MagicMock()
    context.function_name = "getCourses"
    context.aws_request_id = "test-request-id"
    response = handler({}, context)

    # Verificar la respuesta de error
    assert response['statusCode'] == 500
    assert 'Internal Server Error' in response['body']


def test_get_courses_no_courses(mock_dynamodb):
    """Prueba el caso en que no hay cursos."""
    # Configurar el mock para no devolver cursos
    mock_dynamodb.scan.return_value = {'Items': []}

    # Llamar al handler
    context = MagicMock()
    context.function_name = "getCourses"
    context.aws_request_id = "test-request-id"
    response = handler({}, context)

    # Verificar la respuesta
    assert response['statusCode'] == 200
    assert response['body'] == json.dumps([])