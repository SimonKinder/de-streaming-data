"""Utility functions to assist guardian_api and lambda_main files"""

import boto3
import json
import logging
from src.exceptions import BotocoreError
from botocore.exceptions import ClientError


logger = logging.getLogger(name="Guardian Search Content")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(handler)


def format_results(search_results: list[dict]) -> list[dict]:
    """Format the Guardian search content, keeping only information required."""

    try:
        keys_required = ["webPublicationDate", "webTitle", "webUrl"]
        filtered_data = []
        for response in search_results:
            updated_response = {
                key: value
                for key, value in response.items()
                if key in keys_required
            }
            updated_response["content_preview"] = response["fields"][
                "bodyText"
            ][:500]
            updated_response["keywords"] = [
                item["webTitle"] for item in response["tags"]
            ]
            filtered_data.append(updated_response)

        return filtered_data

    except KeyError as i_exc:
        raise KeyError(
            f"Error formatting search results: {str(i_exc)}"
        ) from None


def update_message_retention(queue_url: str, sqs_client: boto3.client) -> None:
    try:
        queue_attributes = sqs_client.get_queue_attributes(
            QueueUrl=queue_url, AttributeNames=["MessageRetentionPeriod"]
        )
        if queue_attributes["Attributes"]["MessageRetentionPeriod"] != "259200":
            sqs_client.set_queue_attributes(
                QueueUrl=queue_url,
                Attributes={"MessageRetentionPeriod": "259200"},
            )
            logger.info(
                "Successfully updated message retention period of %s to 3 days",
                queue_url.split("/")[-1],
            )

    except ClientError as c_exc:
        error_response = {
            "Error": {
                "Code": c_exc.response["Error"]["Code"],
                "Message": "Boto3 error updating queue attributes:"
                f" {c_exc.response['Error']['Message']}",
            }
        }
        raise ClientError(
            error_response=error_response, operation_name=c_exc.operation_name
        ) from None
    except Exception as e_exc:
        raise BotocoreError(
            f"Unexcepted error when updating message retention period: {str(e_exc)}"
        ) from None


def send_queue_message(
    queue_url: str,
    message_id: str,
    message_body: list[dict],
    sqs_client: boto3.client,
) -> None:
    queue_name = queue_url.split("/")[-1]
    try:
        response = sqs_client.send_message(
            QueueUrl=queue_url,
            MessageBody=json.dumps(message_body),
            MessageAttributes={
                "ID": {"DataType": "String", "StringValue": message_id},
            },
        )
        logger.info(
            "Succesfully sent message to %(queue_name)s - Message ID: %(id)s",
            {
                "queue_name": queue_name,
                "id": response["MessageId"],
            },
        )
        return response["MessageId"]

    except ClientError as c_exc:
        error_response = {
            "Error": {
                "Code": c_exc.response["Error"]["Code"],
                "Message": f"Boto3 error when sending message to {queue_name}:"
                f" {c_exc.response['Error']['Message']}",
            }
        }
        raise ClientError(
            error_response=error_response, operation_name=c_exc.operation_name
        ) from None
    except Exception as e_exc:
        raise BotocoreError(
            f"Unexpected error when sending message to {queue_name}: {str(e_exc)}"
        ) from None
