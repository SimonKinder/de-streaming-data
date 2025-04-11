from src.lambda_main import guardian_lambda
import argparse
import json
import logging

# logging.basicConfig(level=logging.INFO)


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Run the Guardian API function"
    )
    parser.add_argument(
        "--query", required=True, help="Search terms for the Guardian API"
    )
    parser.add_argument(
        "--from-date", help="Optional start date in YYYY-MM-DD format"
    )
    parser.add_argument("--queue-url", required=True, help="SQS queue URL")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()

    event = {"query": args.query, "queue_url": args.queue_url}

    # Only add from_date if it was provided
    if args.from_date:
        event["from_date"] = args.from_date
    else:
        event["from_date"] = None

    context = {}

    print(f"Running guardian_main with event: {json.dumps(event, indent=2)}\n")
    result = guardian_lambda(event, context)
    print(f"\nResult: {json.dumps(result, indent=2)}")
