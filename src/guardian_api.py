"""Functions to interact with the Guardian API"""

import os
import httpx
from dotenv import load_dotenv
from types import FunctionType
from functools import wraps
from src.utils import logger
from src.exceptions import (
    RateLimitExceededError,
    ServerRequestError,
    ClientRequestError,
    APIError,
)

# Load Enviroment Varaibles
load_dotenv()


def raise_on_status_error(response: httpx.Response) -> None:
    """HTTPX Middleware to raise custom Exceptions for select HTTP status codes.

    Args:
        response (httpx.Response): httpx response object

    Raises:
        RateLimitExceededError: Raised for status code 429
        ClientRequestError: Raised for status codes 4XX
        ServerRequestError: Raised for status codes 5XX
    """
    status_code = response.status_code
    url = response.url
    if status_code == 429:
        raise RateLimitExceededError(f"Rate Limit Exceeded - URL: {url}")
    if 400 <= status_code < 500:
        raise ClientRequestError(
            f"Client Side Error {status_code} - URL: {url}"
        )
    if 500 <= status_code < 600:
        raise ServerRequestError(
            f"Server Side Error {status_code} - URL: {url}"
        )


def retry_guardian_api(func: FunctionType) -> FunctionType:
    """Decorator to attempt retries and handle exceptions.

    Args:
        func (FunctionType): guardian_get_articles function

    Raises:
        MaxRetriesExceededError: Raised when max_retries is exceeded

    Returns:
        FunctionType: wrapped guardian_get_articles function
    """

    @wraps(func)
    def request_wrapper(**kwargs) -> list[dict]:
        """Wrapper function to handle retries and exceptions.

        Args:
            **kwargs: Arguments to pass to the function.

        Raises:
            APIError: Raised when an unexpected error occurs.

        Returns:
            list[dict]: Search results from the Guardian API.
        """
        retries = 0
        max_retries = 3
        while retries < max_retries:
            try:
                search_results = func(**kwargs)
                return search_results
            except (ServerRequestError, RateLimitExceededError) as retry_exc:
                retries += 1
                if retries >= max_retries:
                    logger.error("Max retries reached: %s", str(retry_exc))
                    raise
                logger.warning(
                    "Retry %(retries)s/%(max_retries)s failed: %(exc)s",
                    {
                        "retries": retries,
                        "max_retries": max_retries,
                        "exc": str(retry_exc),
                    },
                )
            except ClientRequestError as c_exc:
                logger.error("Client error: %s", str(c_exc))
                raise
            except Exception as exc:
                logger.error("Unexpected error: %s", str(exc))
                raise APIError(f"Unexpected error: {str(exc)}") from None

    return request_wrapper


@retry_guardian_api
def get_articles(
    query: str, client: httpx.Client, from_date: str | None = None
) -> list[dict]:
    """Retreive newest Guardian articles referencing query, maximum 10.

    Args:
        query (str): Terms to search for.
        client (httpx.Client): HTTPX Client object.
        from_date (str | None): Date to search from YYYY-MM-DD format. Defaults to None.

    Returns:
        list[dict]: List of Guardian articles matching the search query.
    """

    url = "https://content.guardianapis.com/search"
    api_key = os.getenv("GUARDIAN_API_KEY")
    params = {
        "api-key": api_key,
        "q": query,
        "from-date": from_date,
        "show-fields": "bodyText",
        "order-by": "newest",
        "show-tags": "keyword",
    }
    if from_date is None:
        params.pop("from-date")

    response = client.get(url=url, params=params)
    response.raise_for_status()
    if response.json()["response"]["total"] == 0:
        logger.warning("No articles found mentioning %s", query)
        return None
    search_results = response.json()["response"]["results"]
    logger.info(
        "Successfully retrieved %(amount)s latest articles mentioning %(query)s",
        {"amount": len(search_results), "query": query},
    )
    return search_results
