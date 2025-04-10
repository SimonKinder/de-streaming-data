import os
import json
import pytest
import boto3
from moto import mock_aws
from copy import deepcopy
from botocore.exceptions import ClientError
from src.exceptions import BotocoreError
from src.utils import (
    format_results,
    update_message_retention,
    send_queue_message,
)
from test_data import unformated_results


class TestFormatResults:
    @pytest.mark.it("Confirm the input list object is not mutated")
    def test_non_mutation(self):
        unused_data = deepcopy(unformated_results)
        format_results(unformated_results)
        assert unused_data == unformated_results

    @pytest.mark.it(
        "Confirm the returned list object has different reference to the input list"
    )
    def test_new_reference(self):
        formatted_results = format_results(unformated_results)
        assert formatted_results is not unformated_results

    @pytest.mark.it("Confirm the correct data is returned")
    def test_correct_data(self):
        expected_types = {
            "webPublicationDate": str,
            "webTitle": str,
            "webUrl": str,
            "content_preview": str,
            "keywords": list,
        }

        formatted_results = format_results(unformated_results)

        for result in formatted_results:
            assert len(result.keys()) == 5
            for key, value in result.items():
                assert isinstance(value, expected_types[key])

    @pytest.mark.it("Confirm a KeyError is re-raised with context message")
    def test_key_error(self):
        incorrect_format_results = [{"bad_key_1": 1, "bad_key_2": 2}]

        with pytest.raises(KeyError) as i_exc:
            format_results(incorrect_format_results)
            assert "Error formatting search results" in str(i_exc)


@pytest.fixture(scope="module")
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "eu-west-2"


@pytest.fixture(scope="function")
def sqs_fixure(aws_credentials):
    with mock_aws():
        test_client = boto3.client("sqs")
        response = test_client.create_queue(QueueName="test_queue")
        queue_url = response["QueueUrl"]
        yield test_client, queue_url


class TestUpdateMessageRetention:
    @mock_aws
    @pytest.mark.it("Confirm ClientError is re-raised with context")
    def test_client_error(self):
        sqs_client = boto3.client("sqs")
        with pytest.raises(ClientError) as c_exc:
            update_message_retention("bad_url", sqs_client)
            assert "Boto3 error updating queue attributes:" in c_exc

    @mock_aws
    @pytest.mark.it(
        "Confirm the message retention time is updated when required"
    )
    def test_update_message_retention(self, sqs_fixure):
        sqs_client, queue_url = sqs_fixure
        sqs_client.set_queue_attributes(
            QueueUrl=queue_url,
            Attributes={"MessageRetentionPeriod": "1000"},
        )

        update_message_retention(queue_url=queue_url, sqs_client=sqs_client)
        queue_attributes = sqs_client.get_queue_attributes(
            QueueUrl=queue_url, AttributeNames=["MessageRetentionPeriod"]
        )

        assert (
            queue_attributes["Attributes"]["MessageRetentionPeriod"] == "259200"
        )

    @mock_aws
    @pytest.mark.it("Confirm an unexpected error raises a BotocoreError")
    def test_unexcepted_error(self):
        with pytest.raises(BotocoreError):
            update_message_retention("bad_url", boto3.client("s3"))


class TestSendQueueMessage:
    """
    Tests:
    - random error
    """

    @mock_aws
    @pytest.mark.it("Confirm ClientError is re-raised with context")
    def test_client_error(self):
        sqs_client = boto3.client("sqs")
        with pytest.raises(ClientError) as c_exc:
            send_queue_message(
                queue_url="bad_url",
                message_id="test",
                message_body={"test": "test"},
                sqs_client=sqs_client,
            )
            assert "Boto3 error when sending message to" in c_exc

    @mock_aws
    @pytest.mark.it(
        "Confirm BotocoreError is raised with context for unexpected error"
    )
    def test_unexpected_error(self):
        incorrect_client = boto3.client("s3")
        with pytest.raises(BotocoreError) as c_exc:
            send_queue_message(
                queue_url="bad_url",
                message_id="test",
                message_body={"test": "test"},
                sqs_client=incorrect_client,
            )
            assert "Unexpected error when sending message to " in c_exc

    @mock_aws
    @pytest.mark.it("Confirm a message is succesfully sent to SQS queue")
    def test_success_message(self, sqs_fixure):
        sqs_client, queue_url = sqs_fixure
        message_id = "test_id"
        message_body = {"key_1": "test"}
        attributes = {
            "ID": {"DataType": "String", "StringValue": message_id},
        }

        message_queue_id = send_queue_message(
            queue_url=queue_url,
            message_id=message_id,
            message_body=message_body,
            sqs_client=sqs_client,
        )

        messages = sqs_client.receive_message(
            QueueUrl=queue_url, MessageAttributeNames=["ID"]
        )
        assert messages["Messages"][0]["MessageId"] == message_queue_id
        assert json.loads(messages["Messages"][0]["Body"]) == message_body
        assert messages["Messages"][0]["MessageAttributes"] == attributes
