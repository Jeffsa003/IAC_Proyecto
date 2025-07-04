import pytest
import json
from unittest.mock import patch, MagicMock
import os
from logica_recursos.lambdas.generateCertificate.main import handler

os.environ['DYNAMODB_TABLE_NAME'] = 'test-table'
os.environ['SQS_QUEUE_URL'] = 'http://test.queue.url'

@pytest.fixture
def mock_boto3_clients():
    with patch('boto3.resource') as mock_boto3_resource, \
         patch('boto3.client') as mock_boto3_client:
        
        mock_dynamodb = MagicMock()
        mock_table = MagicMock()
        mock_dynamodb.Table.return_value = mock_table
        mock_boto3_resource.return_value = mock_dynamodb
        
        mock_sqs = MagicMock()
        mock_boto3_client.return_value = mock_sqs
        
        yield mock_table, mock_sqs

@pytest.fixture
def api_event():
    return {
        'requestContext': {'authorizer': {'claims': {'sub': 'user-123', 'email': 'test@example.com'}}},
        'body': json.dumps({'courseId': 'course-abc'})
    }

def test_cert_generate_success(mock_boto3_clients, api_event):
    """Prueba la generación de certificado exitosa."""
    mock_table, mock_sqs = mock_boto3_clients
    
    # Simular que el usuario completó el curso
    mock_table.get_item.side_effect = [
        {'Item': {'progress': 100}}, # Primer get_item para el progreso
        {'Item': {'title': 'Amazing Course'}} # Segundo get_item para el título
    ]
    
    context = MagicMock()
    context.function_name = "generateCertificate"
    context.aws_request_id = "test-request-id"
    response = handler(api_event, context)

    assert response['statusCode'] == 200
    assert 'Certificate generation initiated' in response['body']
    mock_sqs.send_message.assert_called_once()
    
    # Verificar el mensaje enviado a SQS
    message_body = json.loads(mock_sqs.send_message.call_args.kwargs['MessageBody'])
    assert message_body['recipient'] == 'test@example.com'
    assert 'Amazing Course' in message_body['subject']

def test_cert_generate_course_not_completed(mock_boto3_clients, api_event):
    """Prueba el caso en que el curso no está completado."""
    mock_table, mock_sqs = mock_boto3_clients
    mock_table.get_item.return_value = {'Item': {'progress': 50}}
    
    context = MagicMock()
    context.function_name = "generateCertificate"
    context.aws_request_id = "test-request-id"
    response = handler(api_event, context)

    assert response['statusCode'] == 400
    assert 'Course not completed yet' in response['body']
    mock_sqs.send_message.assert_not_called()


def test_cert_generate_internal_error(mock_boto3_clients, api_event):
    """Prueba el manejo de un error interno."""
    mock_table, mock_sqs = mock_boto3_clients
    mock_table.get_item.side_effect = Exception("Internal error")
    
    context = MagicMock()
    context.function_name = "generateCertificate"
    context.aws_request_id = "test-request-id"
    response = handler(api_event, context)

    assert response['statusCode'] == 500
    assert 'Internal Server Error' in response['body']
    mock_sqs.send_message.assert_not_called()