import pytest
import os
from unittest.mock import patch

@pytest.fixture(autouse=True)
def aws_credentials():
    """Set AWS credentials for all tests."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_REGION"] = "us-east-1"

@pytest.fixture(autouse=True)
def mock_boto3_session():
    """Mock boto3 session to ensure region is always set."""
    with patch('boto3.session.Session.region_name', new='us-east-1', create=True):
        yield