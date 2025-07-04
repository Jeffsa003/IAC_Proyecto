import pytest
import json
from unittest.mock import patch, MagicMock
import os
from logica_recursos.lambdas.sendEmail.main import handler

os.environ['SENDER_EMAIL'] = 'sender@example.com'

@pytest.fixture
def mock_ses_client():
    with patch('boto3.client') as mock_client:
        yield mock_client

@pytest.fixture
def sqs_event():
    """Genera un evento de SQS de ejemplo."""
    return {
        "Records": [
            {
                "messageId": "1",
                "body": json.dumps({
                    "recipient": "recipient@example.com",
                    "subject": "Test Subject",
                    "body_text": "Hello World",
                    "body_html": "<h1>Hello World</h1>"
                })
            }
        ]
    }

def test_send_email_success(mock_ses_client, sqs_event):
    """Prueba el envío de correo exitoso."""
    context = MagicMock()
    context.function_name = "sendEmail"
    context.aws_request_id = "test-request-id"
    response = handler(sqs_event, context)

    assert response['statusCode'] == 200
    mock_ses_client.return_value.send_email.assert_called_once()
    
    # Verificar que los parámetros de send_email son correctos
    call_args, call_kwargs = mock_ses_client.return_value.send_email.call_args
    assert call_kwargs['Source'] == 'sender@example.com'
    assert call_kwargs['Destination']['ToAddresses'] == ['recipient@example.com']
    assert call_kwargs['Message']['Subject']['Data'] == 'Test Subject'

def test_send_email_malformed_message(mock_ses_client):
    """Prueba el manejo de un mensaje de SQS malformado."""
    event = {
        "Records": [
            {"messageId": "2", "body": json.dumps({"subject": "Missing fields"})}
        ]
    }
    context = MagicMock()
    context.function_name = "sendEmail"
    context.aws_request_id = "test-request-id"
    response = handler(event, context)

    assert response['statusCode'] == 200 # La función no debe fallar
    mock_ses_client.return_value.send_email.assert_not_called() # No se debe intentar enviar el correo

def test_send_email_ses_error(mock_ses_client, sqs_event):
    """Prueba el manejo de errores de SES."""
    mock_ses_client.return_value.send_email.side_effect = Exception("SES Error")
    context = MagicMock()
    context.function_name = "sendEmail"
    context.aws_request_id = "test-request-id"
    response = handler(sqs_event, context)

    assert response['statusCode'] == 200 # La función no debe fallar
    mock_ses_client.return_value.send_email.assert_called_once()


def test_send_email_multiple_messages(mock_ses_client):
    """Prueba el procesamiento de múltiples mensajes."""
    event = {
        "Records": [
            {"messageId": "3", "body": json.dumps({"recipient": "r1@test.com", "subject": "S1", "body_text": "t", "body_html": "h"})},
            {"messageId": "4", "body": json.dumps({"recipient": "r2@test.com", "subject": "S2", "body_text": "t", "body_html": "h"})}
        ]
    }
    context = MagicMock()
    context.function_name = "sendEmail"
    context.aws_request_id = "test-request-id"
    response = handler(event, context)

    assert response['statusCode'] == 200
    assert mock_ses_client.return_value.send_email.call_count == 2
