import os
import pytest
from moto import mock_aws
from botocore.exceptions import ClientError
from src.exceptions import (
    BotocoreError,
    APIError,
    ClientRequestError,
    ServerRequestError,
    RateLimitExceededError,
)
from src.lambda_main import guardian_lambda
from test_data import unformated_results
from unittest.mock import patch


@pytest.fixture(scope="module")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "eu-west-2"


@pytest.fixture(scope="function")
def event():
    test_event = {
        "query": "test",
        "from_date": "2023-01-01",
        "queue_url": "https://sqs.test.com/test_queue",
    }
    return test_event


class TestLambdaFunction:
    """
    Tests:
    - succesful run
    - api errors
    - key errors
    - boto3 errors
    - unexpected errors
    - no search results
    """

    @mock_aws
    @patch("src.lambda_main.get_articles", return_value=unformated_results)
    @patch("src.lambda_main.update_message_retention", return_value=None)
    @patch("src.lambda_main.send_queue_message", return_value="test_message_id")
    @pytest.mark.it("Confirm the return value is correct for successful run")
    def test_successful_run(
        self, mock_result, mock_update, mock_message, event
    ):
        result = guardian_lambda(event, {})

        assert result["statusCode"] == 200
        assert (
            result["body"]["message"]
            == "Succesfully sent articles from 'test' query to test_queue"
        )
        assert result["body"]["data"]["message_id"] == "test_message_id"

    @mock_aws
    @patch("src.lambda_main.get_articles", return_value=None)
    @pytest.mark.it("Confirm the return value is correct for no search results")
    def test_no_search_results(self, mock_result, event):
        result = guardian_lambda(event, {})

        assert result["statusCode"] == 204
        assert result["body"]["message"] == "No articles found mentioning test"

    @mock_aws
    @pytest.mark.parametrize(
        "error_type",
        [
            APIError,
            ClientRequestError,
            ServerRequestError,
            RateLimitExceededError,
        ],
    )
    @patch("src.lambda_main.get_articles")
    @pytest.mark.it(
        "Confirm the return value is correct for get_articles errors"
    )
    def test_api_error(self, mock_result, error_type, event):
        mock_result.side_effect = error_type("test_error")
        result = guardian_lambda(event, {})

        assert result["statusCode"] == 500
        assert (
            result["body"]["message"]
            == "Error retrieving data from Guardian API: test_error"
        )

    @mock_aws
    @patch("src.lambda_main.get_articles", return_value=unformated_results)
    @patch("src.lambda_main.format_results", side_effect=KeyError("test_error"))
    @pytest.mark.it(
        "Confirm the return value is correct for format_results error"
    )
    def test_format_results_error(self, mock_result, mock_format, event):
        result = guardian_lambda(event, {})
        assert result["statusCode"] == 500
        assert (
            result["body"]["message"]
            == "Error formatting search results: 'test_error'"
        )

    @mock_aws
    @patch("src.lambda_main.get_articles", return_value=unformated_results)
    @patch("src.lambda_main.update_message_retention", return_value=None)
    @patch("src.lambda_main.send_queue_message")
    @pytest.mark.it("Confirm the return value is correct for ClientErrors")
    def test_client_error(self, mock_result, mock_update, mock_message, event):
        mock_message.side_effect = ClientError(
            error_response={
                "Error": {"Code": "test_error", "Message": "Test message"}
            },
            operation_name="test",
        )

        result = guardian_lambda(event, {})
        assert (
            "Error interacting with AWS services:" in result["body"]["message"]
        )
        assert "test_error" in result["body"]["message"]
        assert result["statusCode"] == 500

    @mock_aws
    @patch("src.lambda_main.get_articles", return_value=unformated_results)
    @patch("src.lambda_main.update_message_retention", return_value=None)
    @patch("src.lambda_main.send_queue_message")
    @pytest.mark.it("Confirm the return value is correct for BotocoreErrors")
    def test_boto_error(self, mock_result, mock_update, mock_message, event):
        mock_message.side_effect = BotocoreError("test_error")

        result = guardian_lambda(event, {})
        assert (
            result["body"]["message"]
            == "Error interacting with AWS services: test_error"
        )
        assert result["statusCode"] == 500

    @mock_aws
    @patch("src.lambda_main.get_articles", return_value=unformated_results)
    @patch("src.lambda_main.update_message_retention", return_value=None)
    @patch("src.lambda_main.send_queue_message")
    @pytest.mark.it("Confirm the return value is correct for unexpected errors")
    def test_unexcepted_error(
        self, mock_result, mock_update, mock_message, event
    ):
        mock_message.side_effect = ValueError("test_error")

        result = guardian_lambda(event, {})
        assert (
            result["body"]["message"] == "Unexpected error occured: test_error"
        )
        assert result["statusCode"] == 500
