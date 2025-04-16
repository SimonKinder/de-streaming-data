# Guardian Content Streaming Service

An AWS Lambda function that retrieves articles from The Guardian API based on search queries and streams the content to an SQS queue for further processing.

## Overview

This service provides a serverless solution to:

1. Search The Guardian's content API for articles matching specific queries
2. Format and filter the article data
3. Stream the processed content to an AWS SQS queue

## Prerequisites

- Python 3.12+
- AWS account with appropriate permissions
- Guardian API key
- UV package manager

## UV Package Manager

This project uses UV, a fast Python package installer and resolver written in Rust. To install UV:

```bash
# Using pip
pip install uv

# Using Homebrew (macOS)
brew install uv

# Using cargo
cargo install --git https://github.com/astral-sh/uv uv
```

UV provides faster package installation and dependency resolution compared to pip. For more information, visit [UV's documentation](https://github.com/astral-sh/uv).

## Installation

1. Clone the repository:

```bash
git clone <repository-url>
cd de-streaming-data
```

2. Set up your environment variables:

```bash
touch .env
echo "GUARDIAN_API_KEY=insert-api-key" >> .env
```

3. Test the project

```bash
uv run python run_guardian.py --query "query" --queue-url "sqs_queue_url" --from-date "YYYY-MM-DD"
```

## Project Structure

```
de-streaming-data/
├── src/
│   ├── guardian_api.py    # Guardian API interaction
│   ├── lambda_main.py     # Lambda function handler
│   ├── utils.py           # Utility functions
│   └── exceptions.py      # Custom exceptions
└── tests/
    ├── test_data.py       # Test data
    ├── test_guardian_api.py
    ├── test_lambda_main.py
    └── test_utils.py
```

## Usage

The Lambda function accepts an event with the following parameters:

```python
event = {
    "query": "search terms",
    "from_date": "YYYY-MM-DD",  # Optional
    "queue_url": "https://sqs.[region].amazonaws.com/[account]/[queue]"
}
```

### Response Format

Successful response (200):

```json
{
    "statusCode": 200,
    "body": {
        "message": "Successfully sent articles from '[query]' to [queue]",
        "data": {
            "message_id": "message-id"
        }
    }
}
```

No content response (204):

```json
{
    "statusCode": 204,
    "body": {
        "message": "No articles found mentioning [query]"
    }
}
```

Error response (500):

```json
{
    "statusCode": 500,
    "body": {
        "message": "[Error message]"
    }
}
```

## Testing

Run the test suite:

```bash
export PYTHONPATH=$(pwd)
uv run pytest
```

## Features

- Automatic retry mechanism for API rate limits and server errors
- Custom error handling for API and AWS interactions
- Configurable message retention period for SQS queues
- Comprehensive test coverage with mocked AWS services
- Logging for monitoring and debugging

## Error Handling

The service handles various error scenarios:

- Guardian API rate limiting and server errors
- AWS service interaction errors
- Data formatting issues
- Client request errors

## Dependencies

- `boto3`: AWS SDK for Python
- `httpx`: Modern HTTP client
- `python-dotenv`: Environment variable management
- `moto`: AWS service mocking for tests
- `pytest`: Testing framework
- `respx`: HTTP mocking for tests

## Development

Code quality is maintained using:

- Ruff for linting and formatting
- Pytest for testing
- Coverage reporting
- Type hints
