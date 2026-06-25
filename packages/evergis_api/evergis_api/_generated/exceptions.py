"""Exceptions for HTTP clients."""

from typing import Optional, Dict, Any
import httpx


class ApiClientError(httpx.HTTPStatusError):
    """Custom exception for API client errors.

    Contains detailed information about HTTP request error:
    - status code
    - request URL
    - response body (text and JSON, if possible)
    - original response object
    - response headers

    Usage example:
    ```python
    try:
        result = await client.some_method()
    except ApiClientError as e:
        print(f"Error {e.status_code}: {e.url}")
        print(f"Server response: {e.response_text}")
        if e.response_json:
            print(f"JSON: {e.response_json}")
    ```
    """

    def __init__(
        self,
        message: str,
        *,
        request: httpx.Request,
        response: httpx.Response,
    ):
        """Initializes the exception with detailed error information.

        Args:
            message: Error message
            request: Original HTTP request
            response: HTTP error response
        """
        super().__init__(message, request=request, response=response)

        self.status_code = response.status_code
        self.url = str(request.url)
        self.method = request.method
        self.response_text = response.text
        self.response_headers = dict(response.headers)

        # Safely attempt to parse JSON
        self.response_json: Optional[Dict[str, Any]] = None
        try:
            if response.headers.get("content-type", "").startswith("application/json"):
                self.response_json = response.json()
        except Exception:
            # If JSON parsing failed, leave as None
            pass

    def __str__(self) -> str:
        """Returns string representation of the error."""
        msg = f"HTTP {self.status_code} {self.method} {self.url}"
        if self.response_text:
            # Limit response text length for readability
            text_preview = self.response_text[:200]
            if len(self.response_text) > 200:
                text_preview += "..."
            msg += f"\nServer response: {text_preview}"
        return msg 