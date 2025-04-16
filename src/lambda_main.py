"""AWS Lambda function to retrieve Guardian articles, format the response and send to SQS Queue"""

import boto3
import httpx
from botocore.exceptions import ClientError

try:
    from src.guardian_api import get_articles, raise_on_status_error
    from src.utils import (
        format_results,
        update_message_retention,
        send_queue_message,
    )
    from src.exceptions import (
        APIError,
        ClientRequestError,
        ServerRequestError,
        BotocoreError,
        RateLimitExceededError,
    )
except ImportError:
    from guardian_api import get_articles, raise_on_status_error
    from utils import (
        format_results,
        update_message_retention,
        send_queue_message,
    )
    from exceptions import (
        APIError,
        ClientRequestError,
        ServerRequestError,
        BotocoreError,
        RateLimitExceededError,
    )


def guardian_lambda(event: dict, context: dict) -> dict:
    """_summary_

    Args:
        event (dict): {query, date_from, queue_url}
        context (dict): _description_

    Returns:
        dict: _description_
    """

    try:
        # Retrieve Guardian articles
        with httpx.Client(
            event_hooks={"response": [raise_on_status_error]}
        ) as client:
            search_results = get_articles(
                query=event["query"],
                from_date=event["from_date"],
                client=client,
            )

        if search_results is None:
            return {
                "statusCode": 204,
                "body": {
                    "message": f"No articles found mentioning {event['query']}"
                },
            }

        # Format search results
        formatted_results = format_results(search_results=search_results)

        # Message Broker
        sqs_client = boto3.client("sqs")
        # Update SQS Queue message retention if required
        update_message_retention(
            queue_url=event["queue_url"], sqs_client=sqs_client
        )

        # Send formatted data to SQS Queue
        message_id = send_queue_message(
            queue_url=event["queue_url"],
            message_id="guardian_content",
            message_body=formatted_results,
            sqs_client=sqs_client,
        )

        return {
            "statusCode": 200,
            "body": {
                "message": f"Succesfully sent articles from '{event['query']}'"
                f" query to {event['queue_url'].split('/')[-1]}",
                "data": {
                    "message_id": message_id,
                },
            },
        }

    except (
        ServerRequestError,
        RateLimitExceededError,
        ClientRequestError,
        APIError,
    ) as api_exc:
        return {
            "statusCode": 500,
            "body": {
                "message": f"Error retrieving data from Guardian API: {str(api_exc)}"
            },
        }

    except KeyError as format_exc:
        return {
            "statusCode": 500,
            "body": {
                "message": f"Error formatting search results: {str(format_exc)}"
            },
        }

    except (ClientError, BotocoreError) as boto_exc:
        return {
            "statusCode": 500,
            "body": {
                "message": f"Error interacting with AWS services: {str(boto_exc)}"
            },
        }

    except Exception as base_exc:
        return {
            "statusCode": 500,
            "body": {"message": f"Unexpected error occured: {str(base_exc)}"},
        }
