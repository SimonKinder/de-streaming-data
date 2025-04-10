import pytest
import httpx
import respx
from src.exceptions import (
    RateLimitExceededError,
    ServerRequestError,
    ClientRequestError,
    APIError,
)
from src.guardian_api import raise_on_status_error, retry, get_articles
from types import FunctionType


class TestRaiseStatusError:
    @respx.mock
    @pytest.mark.it(
        "Confirm a RateLimitExceededError is raised upon a 429 response status code"
    )
    def test_rate_limit_exceeded(self):
        with pytest.raises(RateLimitExceededError):
            mock_response = httpx.Response(
                status_code=429,
                request=httpx.Request(method="GET", url="https://test.com"),
            )
            raise_on_status_error(response=mock_response)

    @respx.mock
    @pytest.mark.it(
        "Confirm a ClientRequestError is raised upon a 4XX response status code"
    )
    def test_client_request_error(self):
        with pytest.raises(ClientRequestError):
            mock_response = httpx.Response(
                status_code=401,
                request=httpx.Request(method="GET", url="https://test.com"),
            )
            raise_on_status_error(response=mock_response)

    @respx.mock
    @pytest.mark.it(
        "Confirm a ServerRequestError is raised upon a 5XX response status code"
    )
    def test_server_request_error(self):
        with pytest.raises(ServerRequestError):
            mock_response = httpx.Response(
                status_code=500,
                request=httpx.Request(method="GET", url="https://test.com"),
            )
            raise_on_status_error(response=mock_response)


class TestRetryDecorator:
    @pytest.mark.it("Confirm the decorator returns a function")
    def test_function_returned(self):
        def test_func():
            pass

        result = retry(test_func)
        assert isinstance(result, FunctionType)

    @pytest.mark.it("Confirm the decorated function is called")
    def test_function_called(self):
        is_called = False

        @retry
        def test_func():
            nonlocal is_called
            is_called = True

        test_func()
        assert is_called is True

    @pytest.mark.parametrize(
        "exception", [RateLimitExceededError, ServerRequestError]
    )
    @pytest.mark.it(
        "Confirm retriable exceptions are re-raised after max retries are reached"
    )
    def test_max_retries(self, exception):
        call_count = 0

        @retry
        def test_func():
            nonlocal call_count
            call_count += 1
            raise exception

        with pytest.raises(exception):
            test_func()
        assert call_count == 3

    @pytest.mark.it("Confirm a ClientRequestError is re-raised after 1 attempt")
    def test_client_error(self):
        call_count = 0

        @retry
        def test_func():
            nonlocal call_count
            call_count += 1
            raise ClientRequestError

        with pytest.raises(ClientRequestError):
            test_func()
        assert call_count == 1

    @pytest.mark.it(
        "Confirm a unhandled errors are re-raised as a APIError after 1 attempt"
    )
    def test_unhandled_error(self):
        call_count = 0

        @retry
        def test_func():
            nonlocal call_count
            call_count += 1
            raise ValueError

        with pytest.raises(APIError):
            test_func()
        assert call_count == 1

    @pytest.mark.it(
        "Confirm the correct data is returned for a succesful request"
    )
    def test_succesful_request(self):
        @retry
        def test_func():
            return [1, 2, 3]

        assert test_func() == [1, 2, 3]


class TestGetArticles:
    @respx.mock
    @pytest.mark.it("Confirm None is returned if no results are present")
    def test_zero_results(self):
        results = {"response": {"total": 0}}
        mock_response = httpx.Response(
            status_code=200,
            request=httpx.Request(method="GET", url="https://test.com"),
            json=results,
        )
        respx.get().mock(return_value=mock_response)
        with httpx.Client() as client:
            assert get_articles(query="test_query", client=client) is None

    @respx.mock
    @pytest.mark.it(
        "Confirm from-date parameter is removed when from_date is None"
    )
    def test_from_date_param_removed(self):
        results = {"response": {"total": 0}}
        route = respx.get("https://content.guardianapis.com/search").mock(
            return_value=httpx.Response(200, json=results)
        )

        with httpx.Client() as client:
            get_articles(query="test_query", client=client, from_date=None)

        assert "from-date" not in route.calls.last.request.url.params

    @respx.mock
    @pytest.mark.it(
        "Confirm the correct data is returned for a succesful request"
    )
    def test_correct_data(self):
        results = {"response": {"results": [1, 2, 3], "total": 3}}
        mock_response = httpx.Response(
            status_code=200,
            request=httpx.Request(method="GET", url="https://test.com"),
            json=results,
        )
        respx.get().mock(return_value=mock_response)
        with httpx.Client() as client:
            assert get_articles(query="test_query", client=client) == [1, 2, 3]
