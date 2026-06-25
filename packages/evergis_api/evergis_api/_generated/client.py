"""Synchronous HTTP clients."""

from typing import Any, Dict, List, Optional, Union
from uuid import UUID
import logging
import time
import asyncio

import httpx
from urllib.parse import urljoin

from .schemas import *
from .exceptions import ApiClientError

logger = logging.getLogger(__name__)

class BaseClient:
    """Synchronous base HTTP client."""

    def __init__(self, base_url: str = "http://evergis", timeout: float = 120.0, connect_timeout: float = 10.0, read_timeout: Optional[float] = None, sb_token: Optional[str] = None, *, _shared_client: Optional[httpx.Client] = None):
        """Initializes the client.

        Args:
            base_url: Base API URL (default: http://evergis)
            timeout: General request timeout in seconds (default: 120)
            connect_timeout: Connection timeout in seconds (default: 10)
            read_timeout: Read timeout in seconds (if None, uses timeout)
            sb_token: Authorization parameter
            _shared_client: Internal parameter for shared httpx client (do not use directly)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout or timeout
        self.sb_token = sb_token
        self._bearer_token = None

        if _shared_client is not None:
            # Use shared client from parent APIClient
            self.client = _shared_client
            self._owns_client = False
        else:
            # Create own client
            timeout_config = httpx.Timeout(
                connect=self.connect_timeout,
                read=self.read_timeout,
                write=30.0,
                pool=10.0
            )
            self.client = httpx.Client(timeout=timeout_config)
            self._owns_client = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._owns_client:
            self.client.close()

    def close(self):
        """Closes HTTP client."""
        if self._owns_client:
            self.client.close()

    def set_bearer_token(self, token: str):
        """Sets Bearer token for authorization."""
        self._bearer_token = token
        self.client.headers["Authorization"] = f"Bearer {token}"

    def clear_bearer_token(self):
        """Clears Bearer token."""
        self._bearer_token = None
        self.client.headers.pop("Authorization", None)

    def _build_url(self, path: str) -> str:
        """Builds full URL."""
        return urljoin(self.base_url + '/', path.lstrip('/'))

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Executes HTTP request with retry logic and improved error handling."""
        url = self._build_url(path)
        
        # Add sb_token as parameter if present
        if self.sb_token:
            params = kwargs.get('params', {})
            params['_sk'] = self.sb_token
            kwargs['params'] = params
        
        # Retry logic for temporary failures
        max_retries = 3
        for attempt in range(max_retries + 1):
            try:
                response = self.client.request(method, url, **kwargs)
                
                # Check response success
                if response.is_success:
                    return response
                
                # Don't retry for some status codes
                if response.status_code in (400, 401, 403, 404, 422):
                    break
                
                # Retry for server errors (5xx) or timeout
                if attempt < max_retries and response.status_code >= 500:
                    logger.warning(f"Retry {attempt + 1}/{max_retries} for {method} {url}, status: {response.status_code}")
                    self._sleep_before_retry(attempt)
                    continue
                
                break
                
            except (httpx.TimeoutException, httpx.ConnectError, httpx.ReadTimeout) as e:
                if attempt < max_retries:
                    logger.warning(f"Retry {attempt + 1}/{max_retries} for {method} {url}, error: {type(e).__name__}")
                    self._sleep_before_retry(attempt)
                    continue
                # Re-raise error when retry limit exceeded
                raise
        
        # Error handling after all attempts
        if not response.is_success:
            logger.error(
                f"HTTP {response.status_code} {method} {url}"
                f"\nServer response: {response.text[:500]}"
            )
            
            error_msg = f"HTTP {response.status_code} {method} {url}"
            request = self.client.build_request(method, url, **kwargs)
            raise ApiClientError(error_msg, request=request, response=response)
        
        return response

    def _sleep_before_retry(self, attempt: int):
        """Wait before retry with exponential backoff."""
        import time
        delay = min(2 ** attempt, 10)  # Maximum 10 seconds
        time.sleep(delay)


from typing import List, Optional

class AccountClient(BaseClient):
    """Client for Account operations"""

    def get_users(self, filter: Optional[str] = None, orderBy: Optional[str] = None, offset: Optional[int] = None, limit: Optional[int] = None, users: Optional[List[str]] = None, roles: Optional[List[str]] = None) -> 'PagedList_UserInfoDc':
        """
        Returns the list of users that correspond to the given conditions.
        
        Args:
        filter: String filter for the user (uses % and _ wild cards like SQL).
        orderBy: Ordering property name.
        offset: First index in the list to get.
        limit: Max number of entries in the returned list.
        users: If given, will retrieve only users that belong to one of the given username.
        roles: If given, will retrieve only users that have one of the given roles.
        
        Returns:
            'PagedList_UserInfoDc': Response data
        """
        path = "/account/user/list"

        # Build request parameters
        params = {}
        if filter is not None:
            params["filter"] = filter
        if orderBy is not None:
            params["orderBy"] = orderBy
        if offset is not None:
            params["offset"] = offset
        if limit is not None:
            params["limit"] = limit
        if users is not None:
            params["users"] = users
        if roles is not None:
            params["roles"] = roles

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.PagedList_UserInfoDc)
        return adapter.validate_json(response.content)

    def get_extended_users(self, filter: Optional[str] = None, orderBy: Optional[str] = None, offset: Optional[int] = None, limit: Optional[int] = None, users: Optional[List[str]] = None, roles: Optional[List[str]] = None) -> 'PagedList_ExtendedUserInfoDc':
        """
        Returns the list of extended users informations that correspond to the given conditions.
        
        Args:
        filter: String filter for the user (uses % and _ wild cards like SQL).
        orderBy: Ordering property name.
        offset: First index in the list to get.
        limit: Max number of entries in the returned list.
        users: If given, will retrieve only users that belong to one of the given username.
        roles: If given, will retrieve only users that have one of the given roles.
        
        Returns:
            'PagedList_ExtendedUserInfoDc': Response data
        """
        path = "/account/user/extendedlist"

        # Build request parameters
        params = {}
        if filter is not None:
            params["filter"] = filter
        if orderBy is not None:
            params["orderBy"] = orderBy
        if offset is not None:
            params["offset"] = offset
        if limit is not None:
            params["limit"] = limit
        if users is not None:
            params["users"] = users
        if roles is not None:
            params["roles"] = roles

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.PagedList_ExtendedUserInfoDc)
        return adapter.validate_json(response.content)

    def get_user_info(self) -> 'UserInfoDc':
        """
        Get current user basic information.
        
        Returns:
            'UserInfoDc': Response data
        """
        path = "/account"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.UserInfoDc)
        return adapter.validate_json(response.content)

    def get_user_info_1(self, username: str) -> 'UserInfoDc':
        """
        Get user basic information.
        
        Args:
        username: User name.
        
        Returns:
            'UserInfoDc': Response data
        """
        # Build path
        path = f"/account/{username}"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.UserInfoDc)
        return adapter.validate_json(response.content)

    def get_extended_user_info(self) -> 'ExtendedUserInfoDc':
        """
        Get current user extended information.
        
        Returns:
            'ExtendedUserInfoDc': Response data
        """
        path = "/account/extended"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.ExtendedUserInfoDc)
        return adapter.validate_json(response.content)

    def get_extended_user_info_1(self, username: str) -> 'ExtendedUserInfoDc':
        """
        Get user extended information.
        
        Args:
        username: User name.
        
        Returns:
            'ExtendedUserInfoDc': Response data
        """
        # Build path
        path = f"/account/extended/{username}"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.ExtendedUserInfoDc)
        return adapter.validate_json(response.content)

    def is_username_exists(self, username: str) -> bool:
        """
        Checks if the user with the given name is registered in the system.
        
        Args:
        username: User name to check.
        
        Returns:
            bool: Response data
        """
        path = "/account/user/exists"

        # Build request parameters
        params = {}
        if username is not None:
            params["username"] = username

        # Execute request
        response = self._request("get", path, params=params)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def is_email_exists(self, email: str) -> bool:
        """
        Checks if the user with the given email is registered in the system.
        
        Args:
        email: Email to check.
        
        Returns:
            bool: Response data
        """
        path = "/account/user/email/exists"

        # Build request parameters
        params = {}
        if email is not None:
            params["email"] = email

        # Execute request
        response = self._request("get", path, params=params)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def register_user(self, body: 'RegisterUserDc') -> bool:
        """
        Register new user.
        
        Args:
        body: Request body data
        
        Returns:
            bool: Response data
        """
        path = "/account/register"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def create_user(self, body: 'CreateUserDc', sendConfirmEmail: Optional[bool] = None, createNamespace: Optional[bool] = None) -> bool:
        """
        Create new user.
        
        Only for users with Everpoint.Sdk.Security.Abstractions.ISecurityManager.SuperuserRole role.
        
        Args:
        sendConfirmEmail: Is need to send confirm email message.
        createNamespace: Create user namespace if true.
        body: Request body data
        
        Returns:
            bool: Response data
        """
        path = "/account/user"

        # Build request parameters
        params = {}
        if sendConfirmEmail is not None:
            params["sendConfirmEmail"] = sendConfirmEmail
        if createNamespace is not None:
            params["createNamespace"] = createNamespace

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, params=params, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def update_user(self, body: 'UpdateUserDc') -> bool:
        """
        Update exist user.
        
        Args:
        body: Request body data
        
        Returns:
            bool: Response data
        """
        path = "/account/user"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("patch", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def confirm_email(self, username: str) -> bool:
        """
        Confirm user email.
        
        Only for users with Everpoint.Sdk.Security.Abstractions.ISecurityManager.SuperuserRole role.
        
        Args:
        username: User name.
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/account/user/{username}/email/confirm"

        # Execute request
        response = self._request("post", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def verify_email(self, username: str) -> bool:
        """
        Send email with verification code.
        
        Args:
        username: User name.
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/account/user/{username}/email/verify"

        # Execute request
        response = self._request("post", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def set_email(self, email: str, password: str) -> bool:
        """
        For a user that does not have a set email, sets the email and password. Requires email confirmation through link.
        
        Args:
        email: User email to set.
        password: Password to set.
        
        Returns:
            bool: Response data
        """
        path = "/account/setEmail"

        # Build data for multipart/form-data
        data = {}
        if email is not None:
            data["email"] = email
        if password is not None:
            data["password"] = password

        # Execute request
        response = self._request("post", path, data=data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def confirm_email_1(self, username: str, code: str) -> bool:
        """
        Confirm user email by code.
        
        Args:
        username: User name.
        code: Verification code.
        
        Returns:
            bool: Response data
        """
        path = "/account/user/email/confirm"

        # Build request parameters
        params = {}
        if username is not None:
            params["username"] = username
        if code is not None:
            params["code"] = code

        # Execute request
        response = self._request("post", path, params=params)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def change_email(self, newEmail: str, password: str) -> bool:
        """
        Send email message with confirmation code to new email address.
        
        Args:
        newEmail: New email address.
        password: Current user password.
        
        Returns:
            bool: Response data
        """
        path = "/account/user/email/change"

        # Build request parameters
        params = {}
        if newEmail is not None:
            params["newEmail"] = newEmail
        if password is not None:
            params["password"] = password

        # Execute request
        response = self._request("post", path, params=params)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def confirm_change_email(self, username: str, newEmail: str, code: str) -> bool:
        """
        Check confirmation code and change email address.
        
        Args:
        username: Username.
        newEmail: New email address.
        code: Confirmation code.
        
        Returns:
            bool: Response data
        """
        path = "/account/user/email/change/confirm"

        # Build request parameters
        params = {}
        if username is not None:
            params["username"] = username
        if newEmail is not None:
            params["newEmail"] = newEmail
        if code is not None:
            params["code"] = code

        # Execute request
        response = self._request("post", path, params=params)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def set_user_password(self, body: 'LoginDc') -> bool:
        """
        Set user password.
        
        Args:
        body: Request body data
        
        Returns:
            bool: Response data
        """
        path = "/account/password/set"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("patch", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def change_password(self, oldPassword: str, password: str) -> bool:
        """
        Change current user password.
        
        Args:
        oldPassword: Current password.
        password: New password.
        
        Returns:
            bool: Response data
        """
        path = "/account/password/change"

        # Build data for multipart/form-data
        data = {}
        if oldPassword is not None:
            data["oldPassword"] = oldPassword
        if password is not None:
            data["password"] = password

        # Execute request
        response = self._request("patch", path, data=data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def reset_password(self, email: Optional[str] = None) -> bool:
        """
        Send reset password message.
        
        Args:
        email: Email.
        
        Returns:
            bool: Response data
        """
        path = "/account/password/reset"

        # Build request parameters
        params = {}
        if email is not None:
            params["email"] = email

        # Execute request
        response = self._request("post", path, params=params)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def reset_password_callback(self, username: str, code: str, newPassword: str) -> bool:
        """
        Reset password.
        
        Args:
        username: User name.
        code: Reset code.
        newPassword: Password to set.
        
        Returns:
            bool: Response data
        """
        path = "/account/password/reset/confirm"

        # Build data for multipart/form-data
        data = {}
        if username is not None:
            data["username"] = username
        if code is not None:
            data["code"] = code
        if newPassword is not None:
            data["newPassword"] = newPassword

        # Execute request
        response = self._request("post", path, data=data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def remove_user(self, username: str) -> bool:
        """
        Remove user.
        
        Args:
        username: Username.
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/account/user/{username}"

        # Execute request
        response = self._request("delete", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def create_namespace(self, userName: str, adjustName: Optional[bool] = None) -> 'NamespaceInfoDc':
        """
        Creates a new namespace.
        
        Args:
        userName: Name of the user to create the namespace for. This user will be the owner of the namespace.
        adjustName: If false, the name of the created namespace will be exactly the name of the user. If set to true, the server will try to use the username as the namespace name, but if the name is occupied, it will find a close free name for the namespace, create it and return it as the result of the operation.
        
        Returns:
            'NamespaceInfoDc': Response data
        """
        path = "/account/namespace"

        # Build request parameters
        params = {}
        if userName is not None:
            params["userName"] = userName
        if adjustName is not None:
            params["adjustName"] = adjustName

        # Execute request
        response = self._request("post", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.NamespaceInfoDc)
        return adapter.validate_json(response.content)

    def remove_namespace_async(self, name: str, hardDelete: Optional[bool] = None) -> bool:
        """
        Remove namespace.
        
        Args:
        name: Namespace name.
        hardDelete: Hard delete flag.
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/account/namespace/{name}"

        # Build request parameters
        params = {}
        if hardDelete is not None:
            params["hardDelete"] = hardDelete

        # Execute request
        response = self._request("delete", path, params=params)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def activate_user(self, username: str) -> bool:
        """
        Activate user.
        
        Args:
        username: Username.
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/account/user/{username}/activate"

        # Execute request
        response = self._request("post", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def deactivate_user(self, username: str) -> bool:
        """
        Deactivate user.
        
        Args:
        username: Username.
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/account/user/{username}/deactivate"

        # Execute request
        response = self._request("post", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def authenticate(self, body: 'LoginDc', client_id: Optional[UUID] = None, response_type: Optional['ResponseType'] = None, redirect_uri: Optional[str] = None) -> 'LoginResultDc':
        """
        Login.
        
        Args:
        client_id: Client id.
        response_type: Response type.
        redirect_uri: Redirect uri.
        body: Request body data
        
        Returns:
            'LoginResultDc': Response data
        """
        path = "/account/login"

        # Build request parameters
        params = {}
        if client_id is not None:
            params["client_id"] = client_id
        if response_type is not None:
            params["response_type"] = response_type
        if redirect_uri is not None:
            params["redirect_uri"] = redirect_uri

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, params=params, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.LoginResultDc)
        return adapter.validate_json(response.content)

    def refresh_token(self, body: 'RefreshTokenDc') -> 'LoginResultDc':
        """
        Refresh JWT token.
        
        Args:
        body: Request body data
        
        Returns:
            'LoginResultDc': Response data
        """
        path = "/account/refresh-token"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.LoginResultDc)
        return adapter.validate_json(response.content)

    def revoke_token(self) -> bool:
        """
        Revoke refresh token.
        
        Returns:
            bool: Response data
        """
        path = "/account/revoke-token"

        # Execute request
        response = self._request("delete", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def ldap_login(self, body: 'LoginDc') -> 'LoginResultDc':
        """
        The external login callback.
        
        Args:
        body: Request body data
        
        Returns:
            'LoginResultDc': Response data
        """
        path = "/account/external/login/ldap"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.LoginResultDc)
        return adapter.validate_json(response.content)

    def register_client(self, body: 'RegisterClientRequestDc') -> 'RegisterClientResponseDc':
        """
        Register new client.
        
        Args:
        body: Request body data
        
        Returns:
            'RegisterClientResponseDc': Response data
        """
        path = "/account/oauth2/client"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.RegisterClientResponseDc)
        return adapter.validate_json(response.content)

    def unbind_client(self, clientId: UUID) -> bool:
        """
        Unbind client with id.
        
        Args:
        clientId: Client id.
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/account/oauth2/client/{clientId}"

        # Execute request
        response = self._request("delete", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def token(self, body: 'TokenRequestDc') -> 'TokenResponseDc':
        """
        Get access token request.
        
        Args:
        body: Request body data
        
        Returns:
            'TokenResponseDc': Response data
        """
        path = "/account/oauth2/token"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.TokenResponseDc)
        return adapter.validate_json(response.content)

    def get_roles(self, filter: Optional[str] = None, userFilter: Optional[str] = None, orderBy: Optional[str] = None, withSystem: Optional[bool] = None, offset: Optional[int] = None, limit: Optional[int] = None) -> 'PagedList_RoleInfoDc':
        """
        Enumerate exist roles.
        
        Args:
        filter: String filter for the role (uses % and _ wild cards like SQL).
        userFilter: String filter for the user (uses % and _ wild cards like SQL).
        orderBy: Ordering property name.
        withSystem: Include system roles (starts from '__').
        offset: First index in the list to get.
        limit: Max number of entries in the returned list.
        
        Returns:
            'PagedList_RoleInfoDc': Response data
        """
        path = "/account/role/list"

        # Build request parameters
        params = {}
        if filter is not None:
            params["filter"] = filter
        if userFilter is not None:
            params["userFilter"] = userFilter
        if orderBy is not None:
            params["orderBy"] = orderBy
        if withSystem is not None:
            params["withSystem"] = withSystem
        if offset is not None:
            params["offset"] = offset
        if limit is not None:
            params["limit"] = limit

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.PagedList_RoleInfoDc)
        return adapter.validate_json(response.content)

    def create_role(self, body: 'CreateRoleDc') -> bool:
        """
        Create new role.
        
        Args:
        body: Request body data
        
        Returns:
            bool: Response data
        """
        path = "/account/role"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def update_role(self, body: 'UpdateRoleDc') -> bool:
        """
        Update exist role.
        
        Args:
        body: Request body data
        
        Returns:
            bool: Response data
        """
        path = "/account/role"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("patch", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def remove_role(self, rolename: str) -> bool:
        """
        Remove role.
        
        Args:
        rolename: Role name.
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/account/role/{rolename}"

        # Execute request
        response = self._request("delete", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def add_to_role(self, username: str, role: str) -> bool:
        """
        Add user to role.
        
        Args:
        username: User name.
        role: Role name.
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/account/user/{username}/role/{role}"

        # Execute request
        response = self._request("post", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def remove_from_role(self, username: str, role: str) -> bool:
        """
        Remove user from role.
        
        Args:
        username: User name.
        role: Role name.
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/account/user/{username}/role/{role}"

        # Execute request
        response = self._request("delete", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def post_used_projects(self, body: 'UsedProjectDc') -> 'UsedProjectDc':
        """
        Set used project.
        
        Args:
        body: Request body data
        
        Returns:
            'UsedProjectDc': Response data
        """
        path = "/account/latest_projects"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.UsedProjectDc)
        return adapter.validate_json(response.content)

    def get_used_projects(self) -> List['UsedProjectDc']:
        """
        Get used projects.
        
        Returns:
            List['UsedProjectDc']: Response data
        """
        path = "/account/latest_projects"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(List[schemas.UsedProjectDc])
        return adapter.validate_json(response.content)

    def truncate_used_projects(self) -> bool:
        """
        Truncate used projects.
        
        Returns:
            bool: Response data
        """
        path = "/account/latest_projects"

        # Execute request
        response = self._request("delete", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'



from typing import Optional

class AccountPreviewClient(BaseClient):
    """Client for AccountPreview operations"""

    def get_preview(self) -> bytes:
        """
        Get current user preview image.
        
        Returns:
            bytes: Response data
        """
        path = "/account/user/preview"

        # Execute request
        response = self._request("get", path)

        return response.content

    def upload_preview(self, file: Optional[bytes] = None) -> 'FileUploadResponse':
        """
        Set current user preview image.
        
        Args:
        file: IForm file.
        
        Returns:
            'FileUploadResponse': Response data
        """
        path = "/account/user/preview"

        # Build data for multipart/form-data
        files = {}
        if file is not None:
            import mimetypes
            # Determine Content-Type by file name
            file_name = data.get('fileName', 'file')
            content_type = mimetypes.guess_type(file_name)[0] or 'application/octet-stream'
            files["file"] = (file_name, file, content_type)

        # Execute request
        response = self._request("post", path, files=files if files else None)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.FileUploadResponse)
        return adapter.validate_json(response.content)

    def delete_preview(self) -> bool:
        """
        Delete current user preview.
        
        Returns:
            bool: Response data
        """
        path = "/account/user/preview"

        # Execute request
        response = self._request("delete", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def get_preview_1(self, username: str) -> bytes:
        """
        Get user preview image.
        
        Args:
        username: User name.
        
        Returns:
            bytes: Response data
        """
        # Build path
        path = f"/account/user/preview/{username}"

        # Execute request
        response = self._request("get", path)

        return response.content

    def upload_preview_1(self, username: str, file: Optional[bytes] = None) -> 'FileUploadResponse':
        """
        Set user preview image.
        
        Args:
        username: User name.
        file: IForm file.
        
        Returns:
            'FileUploadResponse': Response data
        """
        # Build path
        path = f"/account/user/preview/{username}"

        # Build data for multipart/form-data
        files = {}
        if file is not None:
            import mimetypes
            # Determine Content-Type by file name
            file_name = data.get('fileName', 'file')
            content_type = mimetypes.guess_type(file_name)[0] or 'application/octet-stream'
            files["file"] = (file_name, file, content_type)

        # Execute request
        response = self._request("post", path, files=files if files else None)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.FileUploadResponse)
        return adapter.validate_json(response.content)

    def delete_preview_1(self, username: str) -> bool:
        """
        Delete user preview.
        
        Args:
        username: User name.
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/account/user/preview/{username}"

        # Execute request
        response = self._request("delete", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'



from typing import List

class BulkOperationsClient(BaseClient):
    """Client for BulkOperations operations"""

    def batch_resources_permissions_set(self, body: 'BatchResourcesAclDc') -> List['BulkOperationResultDc']:
        """
        Perform resources set acl access batch operation.
        
        Args:
        body: Request body data
        
        Returns:
            List['BulkOperationResultDc']: Response data
        """
        path = "/bulk/resources/permissions"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("put", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(List[schemas.BulkOperationResultDc])
        return adapter.validate_json(response.content)



from typing import List, Optional

class CatalogClient(BaseClient):
    """Client for Catalog operations"""

    def get_parents(self, resourceId: str) -> List['ResourceParentDc']:
        """
        Get parents.
        
        Args:
        resourceId: Resource id.
        
        Returns:
            List['ResourceParentDc']: Response data
        """
        # Build path
        path = f"/resources/{resourceId}/parents"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(List[schemas.ResourceParentDc])
        return adapter.validate_json(response.content)

    def get_tags(self, filter: Optional[str] = None, limit: Optional[int] = None, offset: Optional[int] = None) -> 'PagedTagsListDc':
        """
        Get all tags of given user.
        
        Args:
        filter: Text filter.
        limit: Limit response page.
        offset: Offset objects from start.
        
        Returns:
            'PagedTagsListDc': Response data
        """
        path = "/resources/tags"

        # Build request parameters
        params = {}
        if filter is not None:
            params["filter"] = filter
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.PagedTagsListDc)
        return adapter.validate_json(response.content)

    def put_tags(self, resourceId: str, body: List[str]) -> 'ExtendedCatalogResourceDc':
        """
        Put tags to resource.
        
        Args:
        resourceId: Resource id.
        body: Request body data
        
        Returns:
            'ExtendedCatalogResourceDc': Response data
        """
        # Build path
        path = f"/resources/{resourceId}/tags"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("put", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.ExtendedCatalogResourceDc)
        return adapter.validate_json(response.content)

    def post_link(self, body: 'CreateSymlinkDc') -> 'ExtendedCatalogResourceDc':
        """
        Put link to resource.
        
        Args:
        body: Request body data
        
        Returns:
            'ExtendedCatalogResourceDc': Response data
        """
        path = "/resources/links"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.ExtendedCatalogResourceDc)
        return adapter.validate_json(response.content)

    def post_get_all(self, body: 'ListResourcesDc', limit: Optional[int] = None, offset: Optional[int] = None) -> 'PagedResourcesListDc':
        """
        Get all resource with given.
        
        Args:
        limit: Limit response page.
        offset: Offset objects from start.
        body: Request body data
        
        Returns:
            'PagedResourcesListDc': Response data
        """
        path = "/resources"

        # Build request parameters
        params = {}
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, params=params, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.PagedResourcesListDc)
        return adapter.validate_json(response.content)

    def get_resource(self, resourceId: str) -> 'ExtendedCatalogResourceDc':
        """
        Get resource with given id.
        
        Args:
        resourceId: Resource id.
        
        Returns:
            'ExtendedCatalogResourceDc': Response data
        """
        # Build path
        path = f"/resources/{resourceId}"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.ExtendedCatalogResourceDc)
        return adapter.validate_json(response.content)

    def patch_resource(self, resourceId: str, body: 'PatchResourceDc') -> 'ExtendedCatalogResourceDc':
        """
        Update resource.
        
        Args:
        resourceId: Resource id.
        body: Request body data
        
        Returns:
            'ExtendedCatalogResourceDc': Response data
        """
        # Build path
        path = f"/resources/{resourceId}"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("patch", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.ExtendedCatalogResourceDc)
        return adapter.validate_json(response.content)

    def delete_resource(self, resourceId: str, cascade: Optional[bool] = None) -> bool:
        """
        Delete resource.
        
        Args:
        resourceId: Resource id.
        cascade: Cascade deletion.
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/resources/{resourceId}"

        # Build request parameters
        params = {}
        if cascade is not None:
            params["cascade"] = cascade

        # Execute request
        response = self._request("delete", path, params=params)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def resource_exists_by_id_async(self, resourceId: str) -> bool:
        """
        Check resource id is existing.
        
        Args:
        resourceId: Resource Id.
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/resources/exists/{resourceId}"

        # Execute request
        response = self._request("get", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def move_resource(self, resourceId: str, body: 'MoveResourceDc') -> 'ExtendedCatalogResourceDc':
        """
        Rename resource with given id.
        
        Args:
        resourceId: Resource id to rename.
        body: Request body data
        
        Returns:
            'ExtendedCatalogResourceDc': Response data
        """
        # Build path
        path = f"/resources/move/{resourceId}"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.ExtendedCatalogResourceDc)
        return adapter.validate_json(response.content)

    def create_directory(self, body: 'CreateDirectoryDc') -> 'ExtendedCatalogResourceDc':
        """
        Create directory.
        
        Args:
        body: Request body data
        
        Returns:
            'ExtendedCatalogResourceDc': Response data
        """
        path = "/resources/directory"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.ExtendedCatalogResourceDc)
        return adapter.validate_json(response.content)

    def create_file(self, resourceId: Optional[str] = None, fileName: Optional[str] = None, url: Optional[str] = None, file: Optional[bytes] = None, description: Optional[str] = None, tags: Optional[List[str]] = None, icon: Optional[str] = None, InheritAcl: Optional[bool] = None) -> 'ExtendedCatalogResourceDc':
        """
        Create new file.
        
        Args:
        resourceId: File resource id.
        fileName: Name of the uploading file.
        url: Url to upload file.
        file: Id of the tile in the session static storage.
        description: Description of the file.
        tags: A set of tags.
        icon: File icon.
        InheritAcl: True if acl inherited from parent.
        
        Returns:
            'ExtendedCatalogResourceDc': Response data
        """
        path = "/resources/file"

        # Build data for multipart/form-data
        data = {}
        if resourceId is not None:
            data["resourceId"] = resourceId
        if fileName is not None:
            data["fileName"] = fileName
        if url is not None:
            data["url"] = url
        if description is not None:
            data["description"] = description
        if tags is not None:
            data["tags"] = tags
        if icon is not None:
            data["icon"] = icon
        if InheritAcl is not None:
            data["InheritAcl"] = InheritAcl
        files = {}
        if file is not None:
            import mimetypes
            # Determine Content-Type by file name
            file_name = data.get('fileName', 'file')
            content_type = mimetypes.guess_type(file_name)[0] or 'application/octet-stream'
            files["file"] = (file_name, file, content_type)

        # Execute request
        response = self._request("patch", path, data=data, files=files if files else None)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.ExtendedCatalogResourceDc)
        return adapter.validate_json(response.content)

    def create_file_1(self, resourceId: Optional[str] = None, fileName: Optional[str] = None, url: Optional[str] = None, file: Optional[bytes] = None, rewrite: Optional[bool] = None, description: Optional[str] = None, parentId: Optional[str] = None, owner: Optional[str] = None, isTemporary: Optional[bool] = None, tags: Optional[List[str]] = None, icon: Optional[str] = None, isSystem: Optional[bool] = None, InheritAcl: Optional[bool] = None) -> 'ExtendedCatalogResourceDc':
        """
        Create new file.
        
        Args:
        resourceId: File resource id.
        fileName: Name of the uploading file.
        url: Url to upload file.
        file: Id of the tile in the session static storage.
        rewrite: Rewrite flag If true - rewrite file if exists. If false - return error.
        description: Description of the file.
        parentId: Id of the parent resource.
        owner: Owner of the file.
        isTemporary: Check if file is temporary.
        tags: A set of tags.
        icon: File icon.
        isSystem: Check if resource is system.
        InheritAcl: True if acl inherited from parent.
        
        Returns:
            'ExtendedCatalogResourceDc': Response data
        """
        path = "/resources/file"

        # Build data for multipart/form-data
        data = {}
        if resourceId is not None:
            data["resourceId"] = resourceId
        if fileName is not None:
            data["fileName"] = fileName
        if url is not None:
            data["url"] = url
        if rewrite is not None:
            data["rewrite"] = rewrite
        if description is not None:
            data["description"] = description
        if parentId is not None:
            data["parentId"] = parentId
        if owner is not None:
            data["owner"] = owner
        if isTemporary is not None:
            data["isTemporary"] = isTemporary
        if tags is not None:
            data["tags"] = tags
        if icon is not None:
            data["icon"] = icon
        if isSystem is not None:
            data["isSystem"] = isSystem
        if InheritAcl is not None:
            data["InheritAcl"] = InheritAcl
        files = {}
        if file is not None:
            import mimetypes
            # Determine Content-Type by file name
            file_name = data.get('fileName', 'file')
            content_type = mimetypes.guess_type(file_name)[0] or 'application/octet-stream'
            files["file"] = (file_name, file, content_type)

        # Execute request
        response = self._request("post", path, data=data, files=files if files else None)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.ExtendedCatalogResourceDc)
        return adapter.validate_json(response.content)

    def get_permissions(self, resourceId: str) -> 'AccessControlListDc':
        """
        Set permissions to the resource.
        
        Args:
        resourceId: Resource ID.
        
        Returns:
            'AccessControlListDc': Response data
        """
        # Build path
        path = f"/resources/{resourceId}/permissions"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.AccessControlListDc)
        return adapter.validate_json(response.content)

    def set_permissions_1(self, resourceId: str, body: 'AccessControlListDc') -> bool:
        """
        Set permissions to the resource.
        
        Args:
        resourceId: Resource id.
        body: Request body data
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/resources/{resourceId}/permissions"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("put", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def get_permissions_v2(self, resourceId: str) -> 'AccessControlListDc':
        """
        Set permissions to the resource.
        
        Args:
        resourceId: Resource ID.
        
        Returns:
            'AccessControlListDc': Response data
        """
        # Build path
        path = f"/resources/permissions/{resourceId}"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.AccessControlListDc)
        return adapter.validate_json(response.content)

    def set_permissions(self, body: List['ResourceAclDc']) -> bool:
        """
        Set permissions to the resource.
        
        Args:
        body: Request body data
        
        Returns:
            bool: Response data
        """
        path = "/resources/permissions"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("put", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def get_file(self, resourceId: str) -> bytes:
        """
        Download file.
        
        Args:
        resourceId: Resource id.
        
        Returns:
            bytes: Response data
        """
        # Build path
        path = f"/resources/file/{resourceId}"

        # Execute request
        response = self._request("get", path)

        return response.content

    def clean_resources(self) -> bool:
        """
        Clean user resources.
        
        Returns:
            bool: Response data
        """
        path = "/resources/clean"

        # Execute request
        response = self._request("post", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def copy_resources(self, body: List['CopyResourceDc']) -> List['CopyResourceResultDc']:
        """
        Copy a set of resources.
        
        Args:
        body: Request body data
        
        Returns:
            List['CopyResourceResultDc']: Response data
        """
        path = "/resources/copy"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(List[schemas.CopyResourceResultDc])
        return adapter.validate_json(response.content)

    def extract_zip_archive(self, body: 'ZipExtractRequestDc') -> bool:
        """
        Extract zip archive.
        
        Args:
        body: Request body data
        
        Returns:
            bool: Response data
        """
        path = "/resources/zip/extract"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'



from typing import Optional

class CatalogSyncClient(BaseClient):
    """Client for CatalogSync operations"""

    def git_connect(self, body: 'ConnectRequestDc') -> 'ConnectResponseDc':
        """
        Connect resource to git repository.
        
        Args:
        body: Request body data
        
        Returns:
            'ConnectResponseDc': Response data
        """
        path = "/resources/sync/git-connect"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.ConnectResponseDc)
        return adapter.validate_json(response.content)

    def git_pull(self, resourceId: str) -> 'PullResponse':
        """
        Pull resource data from git repository.
        
        Args:
        resourceId: Resource id to pull.
        
        Returns:
            'PullResponse': Response data
        """
        # Build path
        path = f"/resources/sync/git-pull/{resourceId}"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.PullResponse)
        return adapter.validate_json(response.content)

    def git_push(self, body: 'PushRequestDc') -> 'PushResponse':
        """
        Push resource data to a Git repository.
        
        Args:
        body: Request body data
        
        Returns:
            'PushResponse': Response data
        """
        path = "/resources/sync/git-push"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.PushResponse)
        return adapter.validate_json(response.content)

    def git_status(self, resourceId: str) -> 'StatusResponseDc':
        """
        Get resource git repository status.
        
        Args:
        resourceId: Resource id to get status.
        
        Returns:
            'StatusResponseDc': Response data
        """
        # Build path
        path = f"/resources/sync/git-status/{resourceId}"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.StatusResponseDc)
        return adapter.validate_json(response.content)

    def git_versions(self, resourceId: str, limit: Optional[int] = None) -> 'VersionsResponse':
        """
        Get resource git repository versions.
        
        Args:
        resourceId: Resource id to get versions.
        limit: Limit of versions to get.
        
        Returns:
            'VersionsResponse': Response data
        """
        # Build path
        path = f"/resources/sync/git-versions/{resourceId}"

        # Build request parameters
        params = {}
        if limit is not None:
            params["limit"] = limit

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.VersionsResponse)
        return adapter.validate_json(response.content)

    def git_rollback(self, body: 'RollbackRequestDc') -> 'RollbackResponse':
        """
        Rollback resource data to a Git repository.
        
        Args:
        body: Request body data
        
        Returns:
            'RollbackResponse': Response data
        """
        path = "/resources/sync/git-rollback"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.RollbackResponse)
        return adapter.validate_json(response.content)

    def git_disconnect(self, resourceId: str) -> bool:
        """
        Disconnect resource from git repository.
        
        Args:
        resourceId: Resource id to disconnect.
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/resources/sync/git-disconnect/{resourceId}"

        # Execute request
        response = self._request("delete", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'



from typing import Optional

class ClientSettingsClient(BaseClient):
    """Client for ClientSettings operations"""

    def get_configurations_list(self, offset: Optional[int] = None, limit: Optional[int] = None) -> 'PagedList_ConfigDc':
        """
        Get client configurations.
        
        Args:
        offset: Offset.
        limit: Limit (default 10).
        
        Returns:
            'PagedList_ConfigDc': Response data
        """
        path = "/settings/config"

        # Build request parameters
        params = {}
        if offset is not None:
            params["offset"] = offset
        if limit is not None:
            params["limit"] = limit

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.PagedList_ConfigDc)
        return adapter.validate_json(response.content)

    def get_configuration(self, urlPath: str) -> str:
        """
        Get config for urlPath.
        
        Args:
        urlPath: URL path.
        
        Returns:
            str: Response data
        """
        path = "/settings"

        # Build request parameters
        params = {}
        if urlPath is not None:
            params["urlPath"] = urlPath

        # Execute request
        response = self._request("get", path, params=params)

        return response.text

    def set_configuration(self, urlPath: str, description: Optional[str] = None) -> bool:
        """
        Set config for urlPath.
        
        Args:
        urlPath: URL path.
        description: Description.
        
        Returns:
            bool: Response data
        """
        path = "/settings"

        # Build request parameters
        params = {}
        if urlPath is not None:
            params["urlPath"] = urlPath
        if description is not None:
            params["description"] = description

        # Execute request
        response = self._request("post", path, params=params)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def remove_configuration(self, urlPath: str) -> bool:
        """
        Remove config for urlPath.
        
        Args:
        urlPath: URL path.
        
        Returns:
            bool: Response data
        """
        path = "/settings"

        # Build request parameters
        params = {}
        if urlPath is not None:
            params["urlPath"] = urlPath

        # Execute request
        response = self._request("delete", path, params=params)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'



from typing import Optional, Union

class DataSourceClient(BaseClient):
    """Client for DataSource operations"""

    def test_connection(self, body: 'ArcGisDataSourceDc') -> bool:
        """
        Test ArcGIS data source connection.
        
        Args:
        body: Request body data
        
        Returns:
            bool: Response data
        """
        path = "/ds/arcgis/test-connection"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def create_arc_gis_data_source(self, body: 'ArcGisDataSourceDc') -> bool:
        """
        Create ArcGIS data source.
        
        Args:
        body: Request body data
        
        Returns:
            bool: Response data
        """
        path = "/ds/arcgis"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def update_arc_gis_data_source(self, body: 'ArcGisDataSourceDc') -> bool:
        """
        Update ArcGIS data source.
        
        Args:
        body: Request body data
        
        Returns:
            bool: Response data
        """
        path = "/ds/arcgis"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("patch", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def get_data_sources_list(self, owner: Optional[str] = None, offset: Optional[int] = None, limit: Optional[int] = None) -> 'PagedList_DataSourceInfoDc':
        """
        Returns list of the available data sources.
        
        Args:
        owner: Owner.
        offset: Objects limit per response.
        limit: Objects count have to skip. Default limit sets in 20 object.
        
        Returns:
            'PagedList_DataSourceInfoDc': Response data
        """
        path = "/ds"

        # Build request parameters
        params = {}
        if owner is not None:
            params["owner"] = owner
        if offset is not None:
            params["offset"] = offset
        if limit is not None:
            params["limit"] = limit

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.PagedList_DataSourceInfoDc)
        return adapter.validate_json(response.content)

    def create_data_source(self, body: 'PostgresDataSourceDc') -> bool:
        """
        Create postgresql data source.
        
        Args:
        body: Request body data
        
        Returns:
            bool: Response data
        """
        path = "/ds"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def update_data_source(self, body: 'PostgresDataSourceDc') -> bool:
        """
        Update postgresql data source.
        
        Args:
        body: Request body data
        
        Returns:
            bool: Response data
        """
        path = "/ds"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("patch", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def get_data_source(self, name: str) -> Union['ArcGisDataSourceInfoDc', 'MosRuDataSourceInfoDc', 'PostgresDataSourceInfoDc', 'S3DataSourceInfoDc', 'SparkDataSourceInfoDc']:
        """
        Get data source by name.
        
        Args:
        name: Data source name.
        
        Returns:
            Union['ArcGisDataSourceInfoDc', 'MosRuDataSourceInfoDc', 'PostgresDataSourceInfoDc', 'S3DataSourceInfoDc', 'SparkDataSourceInfoDc']: Response data
        """
        # Build path
        path = f"/ds/{name}"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(Union[schemas.ArcGisDataSourceInfoDc, schemas.MosRuDataSourceInfoDc, schemas.PostgresDataSourceInfoDc, schemas.S3DataSourceInfoDc, schemas.SparkDataSourceInfoDc])
        return adapter.validate_json(response.content)

    def remove_data_source(self, name: str) -> bool:
        """
        Remove data source by name.
        
        Args:
        name: Data source name.
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/ds/{name}"

        # Execute request
        response = self._request("delete", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def test_connection_1(self, body: 'MosRuDataSourceDc') -> bool:
        """
        Test data.mos.ru data source connection.
        
        Args:
        body: Request body data
        
        Returns:
            bool: Response data
        """
        path = "/ds/dataMosRu/test-connection"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def create_mos_ru_data_source(self, body: 'MosRuDataSourceDc') -> bool:
        """
        Create data.mos.ru data source.
        
        Args:
        body: Request body data
        
        Returns:
            bool: Response data
        """
        path = "/ds/dataMosRu"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def update_mos_ru_data_source(self, body: 'MosRuDataSourceDc') -> bool:
        """
        Update data.mos.ru data source.
        
        Args:
        body: Request body data
        
        Returns:
            bool: Response data
        """
        path = "/ds/dataMosRu"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("patch", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def test_connection_2(self, body: 'PostgresDataSourceDc') -> bool:
        """
        Test PostgreSQL data source connection.
        
        Args:
        body: Request body data
        
        Returns:
            bool: Response data
        """
        path = "/ds/test-connection"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def test_connection_3(self, body: 'S3DataSourceDc') -> bool:
        """
        Test S3 data source connection.
        
        Args:
        body: Request body data
        
        Returns:
            bool: Response data
        """
        path = "/ds/s3/test-connection"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def create_s3_data_source(self, body: 'S3DataSourceDc') -> bool:
        """
        Create S3 data source.
        
        Args:
        body: Request body data
        
        Returns:
            bool: Response data
        """
        path = "/ds/s3"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def update_s3_data_source(self, body: 'S3DataSourceDc') -> bool:
        """
        Update S3 data source.
        
        Args:
        body: Request body data
        
        Returns:
            bool: Response data
        """
        path = "/ds/s3"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("patch", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def create_spark_data_source(self, body: 'SparkDataSourceDc') -> bool:
        """
        Create spark data source.
        
        Args:
        body: Request body data
        
        Returns:
            bool: Response data
        """
        path = "/ds/spark"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def update_spark_data_source(self, body: 'SparkDataSourceDc') -> bool:
        """
        Update spark data source.
        
        Args:
        body: Request body data
        
        Returns:
            bool: Response data
        """
        path = "/ds/spark"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("patch", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def create_arc_gis_data_source_1(self, body: 'WmsDataSourceDc') -> bool:
        """
        Create WMS data source.
        
        Args:
        body: Request body data
        
        Returns:
            bool: Response data
        """
        path = "/ds/wms"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def update_arc_gis_data_source_1(self, body: 'WmsDataSourceDc') -> bool:
        """
        Update WMS data source.
        
        Args:
        body: Request body data
        
        Returns:
            bool: Response data
        """
        path = "/ds/wms"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("patch", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'



from typing import Dict, Optional, Union
from datetime import datetime

class EqlClient(BaseClient):
    """Client for Eql operations"""

    def get_paged_query_result(self, body: 'EqlRequestDc', saveInHistory: Optional[bool] = None) -> 'PagedFeaturesListDc':
        """
        Perform resources set acl access batch operation.
        
        Args:
        saveInHistory: Can be saved in history.
        body: Request body data
        
        Returns:
            'PagedFeaturesListDc': Response data
        """
        path = "/eql/query"

        # Build request parameters
        params = {}
        if saveInHistory is not None:
            params["saveInHistory"] = saveInHistory

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, params=params, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.PagedFeaturesListDc)
        return adapter.validate_json(response.content)

    def get_query_description(self, body: 'EqlRequestDc') -> List[Union['CalculatedAttributeConfigurationDc', 'GeometryAttributeConfigurationDc', 'StringAttributeConfigurationDc', 'AttributeConfigurationDc']]:
        """
        Get EQL result columns definitions.
        
        Args:
        body: Request body data
        
        Returns:
            List[Union['CalculatedAttributeConfigurationDc', 'GeometryAttributeConfigurationDc', 'StringAttributeConfigurationDc', 'AttributeConfigurationDc']]: Response data
        """
        path = "/eql/description"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(List[Union[schemas.CalculatedAttributeConfigurationDc, schemas.GeometryAttributeConfigurationDc, schemas.StringAttributeConfigurationDc, schemas.AttributeConfigurationDc]])
        return adapter.validate_json(response.content)

    def get_query_dependencies(self, body: 'EqlRequestDc') -> 'EqlDependenciesDc':
        """
        Get EQL result dependencies.
        
        Args:
        body: Request body data
        
        Returns:
            'EqlDependenciesDc': Response data
        """
        path = "/eql/dependencies"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.EqlDependenciesDc)
        return adapter.validate_json(response.content)

    def get_query_resource_references(self, body: 'EqlRequestDc') -> 'EqlResourceReferencesDc':
        """
        Get EQL resource references.
        
        Args:
        body: Request body data
        
        Returns:
            'EqlResourceReferencesDc': Response data
        """
        path = "/eql/references"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.EqlResourceReferencesDc)
        return adapter.validate_json(response.content)

    def get_vector_tile(self, z: int, x: int, y: int, eql: Optional[str] = None) -> bool:
        """
        Get vector tile by query.
        
        Args:
        z: Zoom level.
        x: X tile coordinate.
        y: Y tile coordinate.
        eql: Query id.
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/eql/vt/{z}/{x}/{y}.pbf"

        # Build request parameters
        params = {}
        if eql is not None:
            params["eql"] = eql

        # Execute request
        response = self._request("get", path, params=params)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def get_query_history(self, dtStart: Optional[datetime] = None, dtEnd: Optional[datetime] = None, limit: Optional[int] = None, offset: Optional[int] = None, owner: Optional[str] = None) -> 'PagedList_QueryHistoryDc':
        """
        Get EQL requests history.
        
        Args:
        dtStart: Date and time start.
        dtEnd: Date and time end.
        limit: Limit.
        offset: Offset.
        owner: Request initiator username.
        
        Returns:
            'PagedList_QueryHistoryDc': Response data
        """
        path = "/eql/query/history"

        # Build request parameters
        params = {}
        if dtStart is not None:
            params["dtStart"] = dtStart
        if dtEnd is not None:
            params["dtEnd"] = dtEnd
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if owner is not None:
            params["owner"] = owner

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.PagedList_QueryHistoryDc)
        return adapter.validate_json(response.content)

    def set_layer_parameter_value(self, layerName: Optional[str] = None, paramName: Optional[str] = None, value: Optional[str] = None) -> bool:
        """
        Set EQL layer parameter.
        
        Args:
        layerName: Layer name.
        paramName: Layer parameter name.
        value: Layer parameter value.
        
        Returns:
            bool: Response data
        """
        path = "/eql/setParam"

        # Build request parameters
        params = {}
        if layerName is not None:
            params["layerName"] = layerName
        if paramName is not None:
            params["paramName"] = paramName
        if value is not None:
            params["value"] = value

        # Execute request
        response = self._request("post", path, params=params)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def set_layer_parameters(self, body: Dict[str, Any], layerName: Optional[str] = None) -> bool:
        """
        Set EQL layer parameters.
        
        Args:
        layerName: Layer name.
        body: Request body data
        
        Returns:
            bool: Response data
        """
        path = "/eql/setParams"

        # Build request parameters
        params = {}
        if layerName is not None:
            params["layerName"] = layerName

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, params=params, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def get_layer_parameters(self, layerName: Optional[str] = None, paramName: Optional[str] = None) -> bool:
        """
        Get EQL parameter.
        
        Args:
        layerName: Layer name.
        paramName: Layer parameter name.
        
        Returns:
            bool: Response data
        """
        path = "/eql/getParam"

        # Build request parameters
        params = {}
        if layerName is not None:
            params["layerName"] = layerName
        if paramName is not None:
            params["paramName"] = paramName

        # Execute request
        response = self._request("get", path, params=params)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def get_layer_parameters_1(self, layerName: Optional[str] = None) -> Dict[str, Any]:
        """
        Get all EQL parameters.
        
        Args:
        layerName: Layer name.
        
        Returns:
            Dict[str, Any]: Response data
        """
        path = "/eql/getParams"

        # Build request parameters
        params = {}
        if layerName is not None:
            params["layerName"] = layerName

        # Execute request
        response = self._request("get", path, params=params)

        return response.json()

    def remove_layer_parameter_value(self, layerName: Optional[str] = None, paramName: Optional[str] = None) -> bool:
        """
        Remove EQL layer parameter.
        
        Args:
        layerName: Layer name.
        paramName: Layer parameter name.
        
        Returns:
            bool: Response data
        """
        path = "/eql/removeParam"

        # Build request parameters
        params = {}
        if layerName is not None:
            params["layerName"] = layerName
        if paramName is not None:
            params["paramName"] = paramName

        # Execute request
        response = self._request("delete", path, params=params)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def get_availiable_layer_parameters(self, layerName: Optional[str] = None, paramName: Optional[str] = None) -> 'AvailiableValuesDc':
        """
        Get availiable layer parameters values.
        
        Args:
        layerName: Layer name.
        paramName: Only specified parameter name.
        
        Returns:
            'AvailiableValuesDc': Response data
        """
        path = "/eql/getAvailiableParams"

        # Build request parameters
        params = {}
        if layerName is not None:
            params["layerName"] = layerName
        if paramName is not None:
            params["paramName"] = paramName

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.AvailiableValuesDc)
        return adapter.validate_json(response.content)

    def get(self, id: str) -> 'EqlRequestDc':
        """
        Returns the query by its id.
        
        Args:
        id: Id of the query.
        
        Returns:
            'EqlRequestDc': Response data
        """
        # Build path
        path = f"/eql/query/{id}"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.EqlRequestDc)
        return adapter.validate_json(response.content)

    def update(self, id: str, body: 'EqlRequestDc') -> bool:
        """
        Replaces a query and gives it a new id.
        
        Args:
        id: Id of the query to replace.
        body: Request body data
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/eql/query/{id}"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def create(self, body: 'EqlRequestDc') -> str:
        """
        Creates a new query.
        
        Args:
        body: Request body data
        
        Returns:
            str: Response data
        """
        path = "/eql/query/save"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        return response.text



from typing import Optional

class ExternalProvidersClient(BaseClient):
    """Client for ExternalProviders operations"""

    def facebook_login(self) -> bool:
        """
        The external login by facebook.
        
        Returns:
            bool: Response data
        """
        path = "/account/external/login/facebook"

        # Execute request
        response = self._request("get", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def google_login(self) -> bool:
        """
        The external login by google.
        
        Returns:
            bool: Response data
        """
        path = "/account/external/login/google"

        # Execute request
        response = self._request("get", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def vk_login(self) -> bool:
        """
        The external login by vk.
        
        Returns:
            bool: Response data
        """
        path = "/account/external/login/vk"

        # Execute request
        response = self._request("get", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def yandex_login(self) -> bool:
        """
        The external login by yandex.
        
        Returns:
            bool: Response data
        """
        path = "/account/external/login/yandex"

        # Execute request
        response = self._request("get", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def login_callback(self) -> 'LoginResultDc':
        """
        The external login callback.
        
        Returns:
            'LoginResultDc': Response data
        """
        path = "/account/external/login/callback"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.LoginResultDc)
        return adapter.validate_json(response.content)

    def unbind_facebook(self) -> bool:
        """
        Unbind external login from current user account (facebook).
        
        Returns:
            bool: Response data
        """
        path = "/account/external/unbind/facebook"

        # Execute request
        response = self._request("delete", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def unbind_google(self) -> bool:
        """
        Unbind external login from current user account (google).
        
        Returns:
            bool: Response data
        """
        path = "/account/external/unbind/google"

        # Execute request
        response = self._request("delete", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def unbind_vk(self) -> bool:
        """
        Unbind external login from current user account (vk).
        
        Returns:
            bool: Response data
        """
        path = "/account/external/unbind/vk"

        # Execute request
        response = self._request("delete", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def unbind_yandex(self) -> bool:
        """
        Unbind external login from current user account (yandex).
        
        Returns:
            bool: Response data
        """
        path = "/account/external/unbind/yandex"

        # Execute request
        response = self._request("delete", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def bind_facebook(self, redirect: Optional[str] = None) -> bool:
        """
        Bind external login from current user account (facebook).
        
        Args:
        redirect: Redirect URL.
        
        Returns:
            bool: Response data
        """
        path = "/account/external/bind/facebook"

        # Build request parameters
        params = {}
        if redirect is not None:
            params["redirect"] = redirect

        # Execute request
        response = self._request("get", path, params=params)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def bind_google(self, redirect: Optional[str] = None) -> bool:
        """
        Bind external login from current user account (google).
        
        Args:
        redirect: Redirect URL.
        
        Returns:
            bool: Response data
        """
        path = "/account/external/bind/google"

        # Build request parameters
        params = {}
        if redirect is not None:
            params["redirect"] = redirect

        # Execute request
        response = self._request("get", path, params=params)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def bind_vk(self, redirect: Optional[str] = None) -> bool:
        """
        Bind external login from current user account (vk).
        
        Args:
        redirect: Redirect URL.
        
        Returns:
            bool: Response data
        """
        path = "/account/external/bind/vk"

        # Build request parameters
        params = {}
        if redirect is not None:
            params["redirect"] = redirect

        # Execute request
        response = self._request("get", path, params=params)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def bind_yandex(self, redirect: Optional[str] = None) -> bool:
        """
        Bind external login from current user account (yandex).
        
        Args:
        redirect: Redirect URL.
        
        Returns:
            bool: Response data
        """
        path = "/account/external/bind/yandex"

        # Build request parameters
        params = {}
        if redirect is not None:
            params["redirect"] = redirect

        # Execute request
        response = self._request("get", path, params=params)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def bind_callback(self, redirect: Optional[str] = None) -> bool:
        """
        Callback for bind external login to current user account.
        
        Args:
        redirect: Redirect URL.
        
        Returns:
            bool: Response data
        """
        path = "/account/external/bind/callback"

        # Build request parameters
        params = {}
        if redirect is not None:
            params["redirect"] = redirect

        # Execute request
        response = self._request("get", path, params=params)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'



from typing import List, Optional

class FeedbackClient(BaseClient):
    """Client for Feedback operations"""

    def increase_resources_limit(self, body: 'IncreaseResourcesLimitDc') -> List[str]:
        """
        Increase resources limit request.
        
        Args:
        body: Request body data
        
        Returns:
            List[str]: Response data
        """
        path = "/feedback/limits"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(List[str])
        return adapter.validate_json(response.content)

    def request_full_access(self) -> List[str]:
        """
        Request full access.
        
        Returns:
            List[str]: Response data
        """
        path = "/feedback/fullAccess"

        # Execute request
        response = self._request("post", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(List[str])
        return adapter.validate_json(response.content)

    def feedback(self, Name: Optional[str] = None, Phone: Optional[str] = None, Email: Optional[str] = None, Message: Optional[str] = None, Attachments: Optional[List[bytes]] = None) -> List[str]:
        """
        Feedback request.
        
        Args:
        Name: Name.
        Phone: Phone number.
        Email: Email address.
        Message: Message text.
        Attachments: Attachments.
        
        Returns:
            List[str]: Response data
        """
        path = "/feedback"

        # Build request parameters
        params = {}
        if Name is not None:
            params["Name"] = Name
        if Phone is not None:
            params["Phone"] = Phone
        if Email is not None:
            params["Email"] = Email
        if Message is not None:
            params["Message"] = Message

        # Build data for multipart/form-data
        data = {}
        if Attachments is not None:
            data["Attachments"] = Attachments

        # Execute request
        response = self._request("post", path, params=params, data=data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(List[str])
        return adapter.validate_json(response.content)





class FiltersServiceClient(BaseClient):
    """Client for FiltersService operations"""

    def get(self, id: str) -> 'FilterResponseDc':
        """
        Returns the filter by its id.
        
        Args:
        id: Id of the filter.
        
        Returns:
            'FilterResponseDc': Response data
        """
        # Build path
        path = f"/filters/{id}"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.FilterResponseDc)
        return adapter.validate_json(response.content)

    def update(self, id: str, body: 'FilterDc') -> 'FilterResponseDc':
        """
        Replaces a filter and gives it a new id.
        
        Args:
        id: Id of the filter to replace.
        body: Request body data
        
        Returns:
            'FilterResponseDc': Response data
        """
        # Build path
        path = f"/filters/{id}"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.FilterResponseDc)
        return adapter.validate_json(response.content)

    def create(self, body: 'FilterDc') -> 'FilterResponseDc':
        """
        Creates a new filter.
        
        Args:
        body: Request body data
        
        Returns:
            'FilterResponseDc': Response data
        """
        path = "/filters"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.FilterResponseDc)
        return adapter.validate_json(response.content)



from typing import List, Optional

class GeocodeServiceClient(BaseClient):
    """Client for GeocodeService operations"""

    def geocode(self, providerName: str, address: Optional[str] = None, srId: Optional[int] = None, bboxPoints: Optional[List[float]] = None) -> 'PagedFeaturesListDc':
        """
        Returns geocode geometry.
        
        Args:
        providerName: Geocode provider name to use.
        address: Input address.
        srId: Spatial reference.
        bboxPoints: Bounging box from left top corner to right bottom corner.
        
        Returns:
            'PagedFeaturesListDc': Response data
        """
        # Build path
        path = f"/geocode/{providerName}"

        # Build request parameters
        params = {}
        if address is not None:
            params["address"] = address
        if srId is not None:
            params["srId"] = srId
        if bboxPoints is not None:
            params["bboxPoints"] = bboxPoints

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.PagedFeaturesListDc)
        return adapter.validate_json(response.content)

    def geocode_by_point(self, providerName: str, pointGeometry: Optional[List[float]] = None, srId: Optional[int] = None, bboxPoints: Optional[List[float]] = None) -> 'PagedFeaturesListDc':
        """
        Returns geocode address from point geometry.
        
        Args:
        providerName: Geocode provider name to use.
        pointGeometry: Input point geometry.
        srId: Input point and bounging box sr.
        bboxPoints: Bounging box from left top corner to right bottom corner.
        
        Returns:
            'PagedFeaturesListDc': Response data
        """
        # Build path
        path = f"/geocode/{providerName}/geocodeByPoint"

        # Build request parameters
        params = {}
        if pointGeometry is not None:
            params["pointGeometry"] = pointGeometry
        if srId is not None:
            params["srId"] = srId
        if bboxPoints is not None:
            params["bboxPoints"] = bboxPoints

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.PagedFeaturesListDc)
        return adapter.validate_json(response.content)

    def suggest(self, providerName: str, address: Optional[str] = None, srId: Optional[int] = None, bboxPoints: Optional[List[float]] = None) -> List['GeocodeSuggestResultDc']:
        """
        Returns geocode suggest.
        
        Args:
        providerName: Geocode provider name to use.
        address: Input address.
        srId: Bounging box spatial reference.
        bboxPoints: Bounging box from left top corner to right bottom corner.
        
        Returns:
            List['GeocodeSuggestResultDc']: Response data
        """
        # Build path
        path = f"/geocode/{providerName}/suggest"

        # Build request parameters
        params = {}
        if address is not None:
            params["address"] = address
        if srId is not None:
            params["srId"] = srId
        if bboxPoints is not None:
            params["bboxPoints"] = bboxPoints

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(List[schemas.GeocodeSuggestResultDc])
        return adapter.validate_json(response.content)



from typing import Dict, List, Optional, Union

class ImportServiceClient(BaseClient):
    """Client for ImportService operations"""

    def get_data_schema(self, resourceId: Optional[str] = None, csvDelimiter: Optional[str] = None, limit: Optional[int] = None, offset: Optional[int] = None) -> 'ImportDataSchemaDc':
        """
        Using a file uploaded to the file upload service, reads the headers of the file and returns the information about data schema of all layers in that file, available for import.
        
        Args:
        resourceId: Resource id.
        csvDelimiter: CSV columns delimiter.
        limit: Returned elements limit.
        offset: Returned elements offset.
        
        Returns:
            'ImportDataSchemaDc': Response data
        """
        path = "/import/dataSchema"

        # Build request parameters
        params = {}
        if resourceId is not None:
            params["resourceId"] = resourceId
        if csvDelimiter is not None:
            params["csvDelimiter"] = csvDelimiter
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.ImportDataSchemaDc)
        return adapter.validate_json(response.content)

    def get_features_count(self, body: 'ImportFileFeaturesCountDc') -> int:
        """
        Returns the features count of the given file in temporary static storage.
        
        Args:
        body: Request body data
        
        Returns:
            int: Response data
        """
        path = "/import/count"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        return response.json()

    def read_part(self, FileId: str, LayerName: Optional[str] = None, Condition: Optional[str] = None, Offset: Optional[int] = None, Count: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Returns the features of the given file in temporary static storage.
        
        Args:
        LayerName: Name of the layer.
        FileId: Id of the file in the temporary static storage.
        Condition: Condition.
        Offset: Offset.
        Count: Count.
        
        Returns:
            List[Dict[str, Any]]: Response data
        """
        path = "/import/read"

        # Build request parameters
        params = {}
        if LayerName is not None:
            params["LayerName"] = LayerName
        if FileId is not None:
            params["FileId"] = FileId
        if Condition is not None:
            params["Condition"] = Condition
        if Offset is not None:
            params["Offset"] = Offset
        if Count is not None:
            params["Count"] = Count

        # Execute request
        response = self._request("get", path, params=params)

        return response.json()

    def get_external_wms_layers(self, url: Optional[str] = None) -> List['ExternalLayerInfoDc']:
        """
        Get list of external WMS layers.
        
        Args:
        url: WMS service url.
        
        Returns:
            List['ExternalLayerInfoDc']: Response data
        """
        path = "/import/wms"

        # Build request parameters
        params = {}
        if url is not None:
            params["url"] = url

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(List[schemas.ExternalLayerInfoDc])
        return adapter.validate_json(response.content)

    def get_external_pbf_layers(self, url: Optional[str] = None) -> List['ExternalLayerInfoDc']:
        """
        Get list of external PBF layers.
        
        Args:
        url: PBF service url.
        
        Returns:
            List['ExternalLayerInfoDc']: Response data
        """
        path = "/import/pbf"

        # Build request parameters
        params = {}
        if url is not None:
            params["url"] = url

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(List[schemas.ExternalLayerInfoDc])
        return adapter.validate_json(response.content)

    def get_external_pbf_features(self, url: Optional[str] = None, layerName: Optional[str] = None, offset: Optional[int] = None, limit: Optional[int] = None, withGeom: Optional[bool] = None, attributes: Optional[List[str]] = None) -> 'PagedFeaturesListDc':
        """
        Get features list in external PBF layer.
        
        Args:
        url: PBF service url.
        layerName: PBF layer name.
        offset: Features count have to skip.
        limit: Features limit per response.
        withGeom: If set to true, the geometry will not be returned for features.
        attributes: Comma separated list of attributes to be returned. If not set, all attributes are returned.
        
        Returns:
            'PagedFeaturesListDc': Response data
        """
        path = "/import/pbf/features"

        # Build request parameters
        params = {}
        if url is not None:
            params["url"] = url
        if layerName is not None:
            params["layerName"] = layerName
        if offset is not None:
            params["offset"] = offset
        if limit is not None:
            params["limit"] = limit
        if withGeom is not None:
            params["withGeom"] = withGeom
        if attributes is not None:
            params["attributes"] = attributes

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.PagedFeaturesListDc)
        return adapter.validate_json(response.content)

    def get_external_arcgis_fslayers(self, url: Optional[str] = None) -> List['ExternalLayerInfoDc']:
        """
        Get list of external ArcGis FeatureServer layers.
        
        Args:
        url: Arcgis FeatureServer url.
        
        Returns:
            List['ExternalLayerInfoDc']: Response data
        """
        path = "/import/arcgisfeatureservice"

        # Build request parameters
        params = {}
        if url is not None:
            params["url"] = url

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(List[schemas.ExternalLayerInfoDc])
        return adapter.validate_json(response.content)

    def get_external_arc_gis_layers(self, url: Optional[str] = None) -> List['ExternalLayerInfoDc']:
        """
        Get list of external ArcGis MapServer layers.
        
        Args:
        url: ArcGis map service url.
        
        Returns:
            List['ExternalLayerInfoDc']: Response data
        """
        path = "/import/arcgismapservice"

        # Build request parameters
        params = {}
        if url is not None:
            params["url"] = url

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(List[schemas.ExternalLayerInfoDc])
        return adapter.validate_json(response.content)

    def get_raster_attributes(self, fileName: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse raster attributes from file name.
        
        Args:
        fileName: File name in the temporary static storage.
        
        Returns:
            Dict[str, Any]: Response data
        """
        path = "/import/rasterAttributes"

        # Build request parameters
        params = {}
        if fileName is not None:
            params["fileName"] = fileName

        # Execute request
        response = self._request("get", path, params=params)

        return response.json()

    def get_raster_meta(self, resourceId: Optional[str] = None) -> List[Union['NetCdfMetaDc', 'RasterMetaDc']]:
        """
        Get raster meta data.
        
        Args:
        resourceId: Raster resource id..
        
        Returns:
            List[Union['NetCdfMetaDc', 'RasterMetaDc']]: Response data
        """
        path = "/import/rasterMeta"

        # Build request parameters
        params = {}
        if resourceId is not None:
            params["resourceId"] = resourceId

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(List[Union[schemas.NetCdfMetaDc, schemas.RasterMetaDc]])
        return adapter.validate_json(response.content)



from typing import List, Optional, Union

class LayersClient(BaseClient):
    """Client for Layers operations"""

    def get_bulk_features(self, body: List['GetBulkFeaturesParametersDc']) -> List['PagedBulkFeaturesListDc']:
        """
        Returns list of the layer features.
        
        Args:
        body: Request body data
        
        Returns:
            List['PagedBulkFeaturesListDc']: Response data
        """
        path = "/bulk/layers/features/query"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(List[schemas.PagedBulkFeaturesListDc])
        return adapter.validate_json(response.content)

    def get_bulk_extents(self, body: List['GetBulkExtentsDc'], srId: Optional[int] = None) -> 'BulkExtentsDc':
        """
        Returns list of the layer extents with overall extent.
        
        Args:
        srId: Spatial reference to return the extent in.
        body: Request body data
        
        Returns:
            'BulkExtentsDc': Response data
        """
        path = "/bulk/layers/extent"

        # Build request parameters
        params = {}
        if srId is not None:
            params["srId"] = srId

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, params=params, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.BulkExtentsDc)
        return adapter.validate_json(response.content)

    def get_filtered_features_count(self, body: List['GetBulkFilteredFeaturesCountDc']) -> 'BulkFilteredFeaturesCountDc':
        """
        Returns list of features count according layer filter.
        
        Args:
        body: Request body data
        
        Returns:
            'BulkFilteredFeaturesCountDc': Response data
        """
        path = "/bulk/layers/features/count"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.BulkFilteredFeaturesCountDc)
        return adapter.validate_json(response.content)

    def get_layer_info_async(self, name: str) -> Union['RemoteTileServiceInfoDc', 'PythonServiceInfoDc', 'ExtendedProjectInfoDcV2', 'PbfServiceInfoDc', 'QueryLayerServiceInfoDc', 'TileCatalogServiceInfoDc', 'ProxyServiceInfoDc', 'ExtendedProjectInfoDc', 'FailedServiceInfoDc', 'DetailedTableInfoDc', 'UpdateTableDc', 'ServiceInfoDc', 'ProjectInfoDcV2']:
        """
        Returns the layer information.
        
        Args:
        name: The full name of the layer.
        
        Returns:
            Union['RemoteTileServiceInfoDc', 'PythonServiceInfoDc', 'ExtendedProjectInfoDcV2', 'PbfServiceInfoDc', 'QueryLayerServiceInfoDc', 'TileCatalogServiceInfoDc', 'ProxyServiceInfoDc', 'ExtendedProjectInfoDc', 'FailedServiceInfoDc', 'DetailedTableInfoDc', 'UpdateTableDc', 'ServiceInfoDc', 'ProjectInfoDcV2']: Response data
        """
        # Build path
        path = f"/layers/{name}"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(Union[schemas.RemoteTileServiceInfoDc, schemas.PythonServiceInfoDc, schemas.ExtendedProjectInfoDcV2, schemas.PbfServiceInfoDc, schemas.QueryLayerServiceInfoDc, schemas.TileCatalogServiceInfoDc, schemas.ProxyServiceInfoDc, schemas.ExtendedProjectInfoDc, schemas.FailedServiceInfoDc, schemas.DetailedTableInfoDc, schemas.UpdateTableDc, schemas.ServiceInfoDc, schemas.ProjectInfoDcV2])
        return adapter.validate_json(response.content)

    def patch_query_layer_service(self, name: str, body: Union['PbfServiceConfigurationDc', 'PythonServiceConfigurationDc', 'LinearServiceConfigurationDc', 'PostgresTileCatalogServiceConfigurationDc', 'QueryLayerServiceConfigurationDc', 'RemoteTileServiceConfigurationDc', 'RouteServiceConfigurationDc', 'ProxyServiceConfigurationDc']) -> Union['RemoteTileServiceInfoDc', 'PythonServiceInfoDc', 'ExtendedProjectInfoDcV2', 'PbfServiceInfoDc', 'QueryLayerServiceInfoDc', 'TileCatalogServiceInfoDc', 'ProxyServiceInfoDc', 'ExtendedProjectInfoDc', 'FailedServiceInfoDc', 'DetailedTableInfoDc', 'UpdateTableDc', 'ServiceInfoDc', 'ProjectInfoDcV2']:
        """
        Patch EQL-based Query Layer Service.
        
        Args:
        name: System name of the layer.
        body: Request body data
        
        Returns:
            Union['RemoteTileServiceInfoDc', 'PythonServiceInfoDc', 'ExtendedProjectInfoDcV2', 'PbfServiceInfoDc', 'QueryLayerServiceInfoDc', 'TileCatalogServiceInfoDc', 'ProxyServiceInfoDc', 'ExtendedProjectInfoDc', 'FailedServiceInfoDc', 'DetailedTableInfoDc', 'UpdateTableDc', 'ServiceInfoDc', 'ProjectInfoDcV2']: Response data
        """
        # Build path
        path = f"/layers/{name}"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("patch", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(Union[schemas.RemoteTileServiceInfoDc, schemas.PythonServiceInfoDc, schemas.ExtendedProjectInfoDcV2, schemas.PbfServiceInfoDc, schemas.QueryLayerServiceInfoDc, schemas.TileCatalogServiceInfoDc, schemas.ProxyServiceInfoDc, schemas.ExtendedProjectInfoDc, schemas.FailedServiceInfoDc, schemas.DetailedTableInfoDc, schemas.UpdateTableDc, schemas.ServiceInfoDc, schemas.ProjectInfoDcV2])
        return adapter.validate_json(response.content)

    def get_layers_info_async(self, layerNames: Optional[List[str]] = None, projectNames: Optional[List[str]] = None) -> List[Union['RemoteTileServiceInfoDc', 'PythonServiceInfoDc', 'ExtendedProjectInfoDcV2', 'PbfServiceInfoDc', 'QueryLayerServiceInfoDc', 'TileCatalogServiceInfoDc', 'ProxyServiceInfoDc', 'ExtendedProjectInfoDc', 'FailedServiceInfoDc', 'DetailedTableInfoDc', 'UpdateTableDc', 'ServiceInfoDc', 'ProjectInfoDcV2']]:
        """
        Returns the layers information.
        
        Args:
        layerNames: Name array of the layers.
        projectNames: ProjectName array with layers.
        
        Returns:
            List[Union['RemoteTileServiceInfoDc', 'PythonServiceInfoDc', 'ExtendedProjectInfoDcV2', 'PbfServiceInfoDc', 'QueryLayerServiceInfoDc', 'TileCatalogServiceInfoDc', 'ProxyServiceInfoDc', 'ExtendedProjectInfoDc', 'FailedServiceInfoDc', 'DetailedTableInfoDc', 'UpdateTableDc', 'ServiceInfoDc', 'ProjectInfoDcV2']]: Response data
        """
        path = "/layers/batchInfo"

        # Build request parameters
        params = {}
        if layerNames is not None:
            params["layerNames"] = layerNames
        if projectNames is not None:
            params["projectNames"] = projectNames

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(List[Union[schemas.RemoteTileServiceInfoDc, schemas.PythonServiceInfoDc, schemas.ExtendedProjectInfoDcV2, schemas.PbfServiceInfoDc, schemas.QueryLayerServiceInfoDc, schemas.TileCatalogServiceInfoDc, schemas.ProxyServiceInfoDc, schemas.ExtendedProjectInfoDc, schemas.FailedServiceInfoDc, schemas.DetailedTableInfoDc, schemas.UpdateTableDc, schemas.ServiceInfoDc, schemas.ProjectInfoDcV2]])
        return adapter.validate_json(response.content)

    def publish_service_async(self, body: 'PublishLayerInfoDc') -> Union['RemoteTileServiceInfoDc', 'PythonServiceInfoDc', 'ExtendedProjectInfoDcV2', 'PbfServiceInfoDc', 'QueryLayerServiceInfoDc', 'TileCatalogServiceInfoDc', 'ProxyServiceInfoDc', 'ExtendedProjectInfoDc', 'FailedServiceInfoDc', 'DetailedTableInfoDc', 'UpdateTableDc', 'ServiceInfoDc', 'ProjectInfoDcV2']:
        """
        Publishes a service using the specified layer configuration parameters.
        
        Args:
        body: Request body data
        
        Returns:
            Union['RemoteTileServiceInfoDc', 'PythonServiceInfoDc', 'ExtendedProjectInfoDcV2', 'PbfServiceInfoDc', 'QueryLayerServiceInfoDc', 'TileCatalogServiceInfoDc', 'ProxyServiceInfoDc', 'ExtendedProjectInfoDc', 'FailedServiceInfoDc', 'DetailedTableInfoDc', 'UpdateTableDc', 'ServiceInfoDc', 'ProjectInfoDcV2']: Response data
        """
        path = "/layers"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(Union[schemas.RemoteTileServiceInfoDc, schemas.PythonServiceInfoDc, schemas.ExtendedProjectInfoDcV2, schemas.PbfServiceInfoDc, schemas.QueryLayerServiceInfoDc, schemas.TileCatalogServiceInfoDc, schemas.ProxyServiceInfoDc, schemas.ExtendedProjectInfoDc, schemas.FailedServiceInfoDc, schemas.DetailedTableInfoDc, schemas.UpdateTableDc, schemas.ServiceInfoDc, schemas.ProjectInfoDcV2])
        return adapter.validate_json(response.content)

    def patch_query_layer_service_1(self, name: str, body: List['Operation']) -> List['Operation']:
        """
        Patch EQL-based Query Layer Service.
        
        Args:
        name: System name of the layer.
        body: Request body data
        
        Returns:
            List['Operation']: Response data
        """
        # Build path
        path = f"/layers/{name}/v2"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("patch", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(List[schemas.Operation])
        return adapter.validate_json(response.content)

    def reload_service_async(self, name: str) -> Union['RemoteTileServiceInfoDc', 'PythonServiceInfoDc', 'ExtendedProjectInfoDcV2', 'PbfServiceInfoDc', 'QueryLayerServiceInfoDc', 'TileCatalogServiceInfoDc', 'ProxyServiceInfoDc', 'ExtendedProjectInfoDc', 'FailedServiceInfoDc', 'DetailedTableInfoDc', 'UpdateTableDc', 'ServiceInfoDc', 'ProjectInfoDcV2']:
        """
        Initialize a new instance of service by given name.
        
        Args:
        name: Name of service.
        
        Returns:
            Union['RemoteTileServiceInfoDc', 'PythonServiceInfoDc', 'ExtendedProjectInfoDcV2', 'PbfServiceInfoDc', 'QueryLayerServiceInfoDc', 'TileCatalogServiceInfoDc', 'ProxyServiceInfoDc', 'ExtendedProjectInfoDc', 'FailedServiceInfoDc', 'DetailedTableInfoDc', 'UpdateTableDc', 'ServiceInfoDc', 'ProjectInfoDcV2']: Response data
        """
        # Build path
        path = f"/layers/{name}/reload"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(Union[schemas.RemoteTileServiceInfoDc, schemas.PythonServiceInfoDc, schemas.ExtendedProjectInfoDcV2, schemas.PbfServiceInfoDc, schemas.QueryLayerServiceInfoDc, schemas.TileCatalogServiceInfoDc, schemas.ProxyServiceInfoDc, schemas.ExtendedProjectInfoDc, schemas.FailedServiceInfoDc, schemas.DetailedTableInfoDc, schemas.UpdateTableDc, schemas.ServiceInfoDc, schemas.ProjectInfoDcV2])
        return adapter.validate_json(response.content)

    def get_features(self, name: str, body: 'GetFeaturesParametersDc') -> 'PagedFeaturesListDc':
        """
        Returns list of the layer features.
        
        Args:
        name: Name of feature service.
        body: Request body data
        
        Returns:
            'PagedFeaturesListDc': Response data
        """
        # Build path
        path = f"/layers/{name}/features/query"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.PagedFeaturesListDc)
        return adapter.validate_json(response.content)

    def get_features_1(self, name: str, ewktGeometry: Optional[str] = None, query: Optional[str] = None, dataFilterId: Optional[str] = None, offset: Optional[int] = None, limit: Optional[int] = None, srId: Optional[int] = None, sort: Optional[List[str]] = None, ids: Optional[List[str]] = None, withGeom: Optional[bool] = None, attributes: Optional[List[str]] = None) -> 'PagedFeaturesListDc':
        """
        Returns list of the layer features.
        
        Args:
        name: Full name of the layer.
        ewktGeometry: Click geometry.
        query: Sets features filtering query.
        dataFilterId: Id of override data filter to apply to the layer. If not set, the default filter is used.
        offset: Features count have to skip.
        limit: Features limit per response.
        srId: Spatial reference of returned features.
        sort: Comma separated list of attributes by which to sort the resulting feature list. If the attribute name is preceded with the \"-\" sign, sorting by this attribute will be in descending order.
        ids: Comma separated list of features ids.
        withGeom: If set to true, the geometry will not be returned for features.
        attributes: Comma separated list of attributes to be returned. If not set, all attributes are returned.
        
        Returns:
            'PagedFeaturesListDc': Response data
        """
        # Build path
        path = f"/layers/{name}/features"

        # Build request parameters
        params = {}
        if ewktGeometry is not None:
            params["ewktGeometry"] = ewktGeometry
        if query is not None:
            params["query"] = query
        if dataFilterId is not None:
            params["dataFilterId"] = dataFilterId
        if offset is not None:
            params["offset"] = offset
        if limit is not None:
            params["limit"] = limit
        if srId is not None:
            params["srId"] = srId
        if sort is not None:
            params["sort"] = sort
        if ids is not None:
            params["ids"] = ids
        if withGeom is not None:
            params["withGeom"] = withGeom
        if attributes is not None:
            params["attributes"] = attributes

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.PagedFeaturesListDc)
        return adapter.validate_json(response.content)

    def delete_feature(self, name: str, id: Optional[str] = None) -> 'LayerUpdateInfoDc':
        """
        Deletes feature by id.
        
        Args:
        id: Feature id.
        name: Full name of the layer.
        
        Returns:
            'LayerUpdateInfoDc': Response data
        """
        # Build path
        path = f"/layers/{name}/features"

        # Build request parameters
        params = {}
        if id is not None:
            params["id"] = id

        # Execute request
        response = self._request("delete", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.LayerUpdateInfoDc)
        return adapter.validate_json(response.content)

    def create_features(self, name: str, body: List['FeatureDc'], allowAdditionalAttributes: Optional[bool] = None) -> 'LayerUpdateInfoDc':
        """
        Creates features list of type.SPCore.Connectors.Connectors.Base.Models.Features.FeatureDc.
        
        Args:
        name: Full name of the layer.
        allowAdditionalAttributes: Allow additional atributes.
        body: Request body data
        
        Returns:
            'LayerUpdateInfoDc': Response data
        """
        # Build path
        path = f"/layers/{name}/features"

        # Build request parameters
        params = {}
        if allowAdditionalAttributes is not None:
            params["allowAdditionalAttributes"] = allowAdditionalAttributes

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, params=params, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.LayerUpdateInfoDc)
        return adapter.validate_json(response.content)

    def update_feature(self, name: str, body: List['UpdateFeatureDc']) -> 'LayerUpdateInfoDc':
        """
        Updates features list SPCore.Connectors.Connectors.Base.Models.Features.FeatureDc.
        
        Args:
        name: Full name of the layer.
        body: Request body data
        
        Returns:
            'LayerUpdateInfoDc': Response data
        """
        # Build path
        path = f"/layers/{name}/features"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("patch", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.LayerUpdateInfoDc)
        return adapter.validate_json(response.content)

    def get_by_id_async(self, name: str, id: str, srId: Optional[int] = None) -> 'FeatureDc':
        """
        Gets feature by id.
        
        Args:
        name: Full name of the layer.
        id: Feature id.
        srId: Spatial reference of returned features.
        
        Returns:
            'FeatureDc': Response data
        """
        # Build path
        path = f"/layers/{name}/features/{id}"

        # Build request parameters
        params = {}
        if srId is not None:
            params["srId"] = srId

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.FeatureDc)
        return adapter.validate_json(response.content)

    def get_tiles_layer_image(self, name: str, x: int, y: int, z: int, ids: Optional[List[int]] = None, dataFilterId: Optional[str] = None) -> bytes:
        """
        Render tile with input indexes.
        
        Args:
        name: Full name of the layer.
        x: X.
        y: Y.
        z: Z.
        ids: Tile sets to render.
        dataFilterId: Id of override data filter to apply to the layer. If not set, the default filter is used.
        
        Returns:
            bytes: Response data
        """
        # Build path
        path = f"/layers/{name}/tile/{z}/{x}/{y}"

        # Build request parameters
        params = {}
        if ids is not None:
            params["ids"] = ids
        if dataFilterId is not None:
            params["dataFilterId"] = dataFilterId

        # Execute request
        response = self._request("get", path, params=params)

        return response.content

    def get_tiles_layer_image_1(self, name: str, x: int, y: int, z: int, format: str, ids: Optional[List[int]] = None, dataFilterId: Optional[str] = None) -> bytes:
        """
        Render tile with input indexes.
        
        Args:
        name: Full name of the layer.
        x: X.
        y: Y.
        z: Z.
        format: Specifies the format of the returned tile.
        ids: Tile sets to render.
        dataFilterId: Id of override data filter to apply to the layer. If not set, the default filter is used.
        
        Returns:
            bytes: Response data
        """
        # Build path
        path = f"/layers/{name}/tile/{z}/{x}/{y}.{format}"

        # Build request parameters
        params = {}
        if ids is not None:
            params["ids"] = ids
        if dataFilterId is not None:
            params["dataFilterId"] = dataFilterId

        # Execute request
        response = self._request("get", path, params=params)

        return response.content

    def get_tiles_layer_image_with_format_and_dpi(self, name: str, x: int, y: int, z: int, dpi: float, format: str, ids: Optional[List[int]] = None, dataFilterId: Optional[str] = None) -> bytes:
        """
        Render tile with input indexes.
        
        Args:
        name: Full name of the layer.
        x: X.
        y: Y.
        z: Z.
        dpi: Image dpi.
        format: Specifies the format of the returned tile.
        ids: Tile sets to render.
        dataFilterId: Id of override data filter to apply to the layer. If not set, the default filter is used.
        
        Returns:
            bytes: Response data
        """
        # Build path
        path = f"/layers/{name}/tile/{z}/{x}/{y}@{dpi}x.{format}"

        # Build request parameters
        params = {}
        if ids is not None:
            params["ids"] = ids
        if dataFilterId is not None:
            params["dataFilterId"] = dataFilterId

        # Execute request
        response = self._request("get", path, params=params)

        return response.content

    def get_layer_extent(self, name: str, condition: Optional[str] = None, srId: Optional[int] = None) -> 'EnvelopeDc':
        """
        Returns the extent of the layer.
        
        Args:
        name: Full name of the layer.
        condition: If set, only the features that satisfy the condition will be considered when calculating the extent.
        srId: Spatial reference to return the extent in.
        
        Returns:
            'EnvelopeDc': Response data
        """
        # Build path
        path = f"/layers/{name}/extent"

        # Build request parameters
        params = {}
        if condition is not None:
            params["condition"] = condition
        if srId is not None:
            params["srId"] = srId

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.EnvelopeDc)
        return adapter.validate_json(response.content)

    def delete_features(self, name: str, ids: Optional[List[str]] = None) -> 'LayerUpdateInfoDc':
        """
        Delete a list of features by given ids. Example: ids=1,2,3.
        
        Args:
        name: Full name of the layer.
        ids: Features ids.
        
        Returns:
            'LayerUpdateInfoDc': Response data
        """
        # Build path
        path = f"/layers/{name}/features/deleteByIds"

        # Build request parameters
        params = {}
        if ids is not None:
            params["ids"] = ids

        # Execute request
        response = self._request("delete", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.LayerUpdateInfoDc)
        return adapter.validate_json(response.content)

    def delete_by_condition(self, name: str, condition: Optional[str] = None) -> 'LayerUpdateInfoDc':
        """
        Delete a list of features by condition with exclude given ids.
        
        Args:
        condition: Filtering query.
        name: Full name of the layer.
        
        Returns:
            'LayerUpdateInfoDc': Response data
        """
        # Build path
        path = f"/layers/{name}/features/deleteByCondition"

        # Build request parameters
        params = {}
        if condition is not None:
            params["condition"] = condition

        # Execute request
        response = self._request("delete", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.LayerUpdateInfoDc)
        return adapter.validate_json(response.content)

    def classify(self, name: str, attribute: Optional[str] = None, classes: Optional[int] = None, precision: Optional[int] = None, type: Optional['ClassificationType'] = None) -> 'ClassifyDc':
        """
        Returns the classified attribute values that correspond to the given number of classes.
        
        Args:
        name: The name of the layer.
        attribute: The name of the attribute.
        classes: The number of classes.
        precision: Sets required values precision.
        type: Classification method.
        
        Returns:
            'ClassifyDc': Response data
        """
        # Build path
        path = f"/layers/{name}/classify"

        # Build request parameters
        params = {}
        if attribute is not None:
            params["attribute"] = attribute
        if classes is not None:
            params["classes"] = classes
        if precision is not None:
            params["precision"] = precision
        if type is not None:
            params["type"] = type

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.ClassifyDc)
        return adapter.validate_json(response.content)

    def distincts(self, name: str, attribute: Optional[str] = None, limit: Optional[int] = None, condition: Optional[str] = None, startsWith: Optional[str] = None, ignoreDefaultCondition: Optional[bool] = None) -> 'AttributeDistinctsDc':
        """
        Returns distinct attribute values and their count.
        
        Args:
        name: Full name of the layer.
        attribute: Attribute name.
        limit: Limit the number of returned values.
        condition: Condition to apply to the layer to filter the features.
        startsWith: Filter values by startWith string pattern.
        ignoreDefaultCondition: Ignore default layer condition.
        
        Returns:
            'AttributeDistinctsDc': Response data
        """
        # Build path
        path = f"/layers/{name}/distincts"

        # Build request parameters
        params = {}
        if attribute is not None:
            params["attribute"] = attribute
        if limit is not None:
            params["limit"] = limit
        if condition is not None:
            params["condition"] = condition
        if startsWith is not None:
            params["startsWith"] = startsWith
        if ignoreDefaultCondition is not None:
            params["ignoreDefaultCondition"] = ignoreDefaultCondition

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.AttributeDistinctsDc)
        return adapter.validate_json(response.content)

    def aggregate_attribute(self, name: str, aggregationAttributeName: Optional[str] = None, aggregationFunctionName: Optional['AggregationFunction'] = None, groups: Optional[List[str]] = None, sort: Optional[List[str]] = None, condition: Optional[str] = None) -> List['AggregationDataResultDc']:
        """
        Returns aggregated value of given attribute aggregationAttributeName within a given groups groups.
        
        Args:
        name: Name of the layer.
        aggregationAttributeName: Aggregation attribute name.
        aggregationFunctionName: Aggregation function name.
        groups: A list of attributes to group.
        sort: Comma separated list of attributes by which to sort the resulting values. If the attribute name is preceded with the \"-\" sign, sorting by this attribute will be in descending order.
        condition: Filter condition.
        
        Returns:
            List['AggregationDataResultDc']: Response data
        """
        # Build path
        path = f"/layers/{name}/aggregate-values"

        # Build request parameters
        params = {}
        if aggregationAttributeName is not None:
            params["aggregationAttributeName"] = aggregationAttributeName
        if aggregationFunctionName is not None:
            params["aggregationFunctionName"] = aggregationFunctionName
        if groups is not None:
            params["groups"] = groups
        if sort is not None:
            params["sort"] = sort
        if condition is not None:
            params["condition"] = condition

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(List[schemas.AggregationDataResultDc])
        return adapter.validate_json(response.content)

    def get_filtered_features_count_1(self, name: str, condition: Optional[str] = None) -> int:
        """
        Get features count according layer filter of the given name.
        
        Args:
        name: Layer name.
        condition: Condition to apply to the layer to filter the features.
        
        Returns:
            int: Response data
        """
        # Build path
        path = f"/layers/{name}/features/count"

        # Build request parameters
        params = {}
        if condition is not None:
            params["condition"] = condition

        # Execute request
        response = self._request("get", path, params=params)

        return response.json()

    def get_filtered_features_count_2(self, name: str, body: 'GetFilteredFeaturesCountDc') -> int:
        """
        Get features count according layer filter of the given name.
        
        Args:
        name: Layer name.
        body: Request body data
        
        Returns:
            int: Response data
        """
        # Build path
        path = f"/layers/{name}/features/count"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        return response.json()

    def edit_attributes(self, name: str, body: 'EditAttributesInfoDc') -> 'LayerUpdateInfoDc':
        """
        Edit attributes with editInfo.
        
        Args:
        name: Name of the layer.
        body: Request body data
        
        Returns:
            'LayerUpdateInfoDc': Response data
        """
        # Build path
        path = f"/layers/{name}/features/edit-attributes"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.LayerUpdateInfoDc)
        return adapter.validate_json(response.content)

    def validate_expression(self, layerName: str, expression: Optional[str] = None) -> 'ExpressionValidationResultDc':
        """
        Validates the given EQL expression against the requested layer. If the expression is valid, it can be executed on the features in the layer to produce a value of some type. The type of the resulting value will be also returned in the validation result.
        
        Args:
        layerName: Layer name.
        expression: Expression to validate.
        
        Returns:
            'ExpressionValidationResultDc': Response data
        """
        # Build path
        path = f"/layers/{layerName}/validateExpression"

        # Build request parameters
        params = {}
        if expression is not None:
            params["expression"] = expression

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.ExpressionValidationResultDc)
        return adapter.validate_json(response.content)

    def get_raster_meta(self, name: str, id: int, min: Optional[float] = None, max: Optional[float] = None) -> List[Union['NetCdfMetaDc', 'RasterMetaDc']]:
        """
        Get raster metadata.
        
        Args:
        name: Layer name.
        id: Id of raster.
        min: Min value for build histogram.
        max: Max value for build histogram.
        
        Returns:
            List[Union['NetCdfMetaDc', 'RasterMetaDc']]: Response data
        """
        # Build path
        path = f"/layers/{name}/{id}/metadata"

        # Build request parameters
        params = {}
        if min is not None:
            params["min"] = min
        if max is not None:
            params["max"] = max

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(List[Union[schemas.NetCdfMetaDc, schemas.RasterMetaDc]])
        return adapter.validate_json(response.content)

    def is_exists_async(self, name: str) -> bool:
        """
        Check is resource exists.
        
        Args:
        name: Resource name.
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/layers/{name}/exists"

        # Execute request
        response = self._request("get", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def get_resource_dependencies(self, name: str) -> 'ResourceDependenciesDc':
        """
        Get resource dependencies.
        
        Args:
        name: The name of the resource.
        
        Returns:
            'ResourceDependenciesDc': Response data
        """
        # Build path
        path = f"/layers/{name}/dependencies"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.ResourceDependenciesDc)
        return adapter.validate_json(response.content)

    def get_resource_references(self, name: str) -> 'ResourceDependenciesDc':
        """
        Returns the resource dependency information.
        
        Args:
        name: The name of the layer.
        
        Returns:
            'ResourceDependenciesDc': Response data
        """
        # Build path
        path = f"/layers/{name}/references"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.ResourceDependenciesDc)
        return adapter.validate_json(response.content)



from typing import List, Optional

class ProjectsClient(BaseClient):
    """Client for Projects operations"""

    def create_project(self, body: 'ExtendedProjectInfoDc') -> 'ExtendedProjectInfoDc':
        """
        Creates a new project.
        
        Args:
        body: Request body data
        
        Returns:
            'ExtendedProjectInfoDc': Response data
        """
        path = "/projects"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.ExtendedProjectInfoDc)
        return adapter.validate_json(response.content)

    def update_project(self, name: str, body: 'ExtendedProjectInfoDc') -> 'ExtendedProjectInfoDc':
        """
        Update table.
        
        Args:
        name: The full name of the project.
        body: Request body data
        
        Returns:
            'ExtendedProjectInfoDc': Response data
        """
        # Build path
        path = f"/projects/{name}"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("patch", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.ExtendedProjectInfoDc)
        return adapter.validate_json(response.content)

    def get_project_info(self, name: str) -> 'ExtendedProjectInfoDc':
        """
        Returns the project and it's content information.
        
        Args:
        name: The name of the project.
        
        Returns:
            'ExtendedProjectInfoDc': Response data
        """
        # Build path
        path = f"/projects/{name}"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.ExtendedProjectInfoDc)
        return adapter.validate_json(response.content)

    def update_project_v2(self, name: str, body: List['Operation']) -> List['Operation']:
        """
        Update table.
        
        Args:
        name: The full name of the project.
        body: Request body data
        
        Returns:
            List['Operation']: Response data
        """
        # Build path
        path = f"/projects/{name}/v2"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("patch", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(List[schemas.Operation])
        return adapter.validate_json(response.content)

    def get_projects_info_async(self, projectNames: Optional[List[str]] = None) -> List['ExtendedProjectInfoDc']:
        """
        Returns the projects information.
        
        Args:
        projectNames: Project names.
        
        Returns:
            List['ExtendedProjectInfoDc']: Response data
        """
        path = "/projects/batchInfo"

        # Build request parameters
        params = {}
        if projectNames is not None:
            params["projectNames"] = projectNames

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(List[schemas.ExtendedProjectInfoDc])
        return adapter.validate_json(response.content)

    def get_project_envelope(self, name: str, srId: Optional[int] = None) -> 'EnvelopeDc':
        """
        Get project extent.
        
        Args:
        name: The name of the project.
        srId: Spatial reference to return the extent in.
        
        Returns:
            'EnvelopeDc': Response data
        """
        # Build path
        path = f"/projects/{name}/extent"

        # Build request parameters
        params = {}
        if srId is not None:
            params["srId"] = srId

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.EnvelopeDc)
        return adapter.validate_json(response.content)

    def get_project_layers_extended_info(self, name: str) -> 'ExtendedProjectLayersInfo':
        """
        Gets extended project info with layers info.
        
        Args:
        name: Name of the projects.
        
        Returns:
            'ExtendedProjectLayersInfo': Response data
        """
        # Build path
        path = f"/projects/{name}/extended-info"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.ExtendedProjectLayersInfo)
        return adapter.validate_json(response.content)

    def get_tiles_layer_image(self, name: str, x: int, y: int, z: int) -> bytes:
        """
        Render tile.
        
        Args:
        name: Full name of the project.
        x: X.
        y: Y.
        z: Z.
        
        Returns:
            bytes: Response data
        """
        # Build path
        path = f"/projects/{name}/tile/{z}/{x}/{y}"

        # Execute request
        response = self._request("get", path)

        return response.content

    def get_tiles_layer_image_with_format(self, name: str, x: int, y: int, z: int, format: str) -> bytes:
        """
        Render tile.
        
        Args:
        name: Full name of the project.
        x: X.
        y: Y.
        z: Z.
        format: Specifies the format of the returned tile.
        
        Returns:
            bytes: Response data
        """
        # Build path
        path = f"/projects/{name}/tile/{z}/{x}/{y}.{format}"

        # Execute request
        response = self._request("get", path)

        return response.content

    def get_tiles_layer_image_with_format_and_dpi(self, name: str, x: int, y: int, z: int, dpi: float, format: str) -> bytes:
        """
        Render tile.
        
        Args:
        name: Full name of the project.
        x: X.
        y: Y.
        z: Z.
        dpi: Image dpi.
        format: Specifies the format of the returned tile.
        
        Returns:
            bytes: Response data
        """
        # Build path
        path = f"/projects/{name}/tile/{z}/{x}/{y}@{dpi}x.{format}"

        # Execute request
        response = self._request("get", path)

        return response.content

    def is_exists_async(self, name: str) -> bool:
        """
        Check is resource exists.
        
        Args:
        name: Resource name.
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/projects/{name}/exists"

        # Execute request
        response = self._request("get", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def get_resource_dependencies(self, name: str) -> 'ResourceDependenciesDc':
        """
        Get resource dependencies.
        
        Args:
        name: The name of the resource.
        
        Returns:
            'ResourceDependenciesDc': Response data
        """
        # Build path
        path = f"/projects/{name}/dependencies"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.ResourceDependenciesDc)
        return adapter.validate_json(response.content)

    def get_resource_references(self, name: str) -> 'ResourceDependenciesDc':
        """
        Returns the resource dependency information.
        
        Args:
        name: The name of the layer.
        
        Returns:
            'ResourceDependenciesDc': Response data
        """
        # Build path
        path = f"/projects/{name}/references"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.ResourceDependenciesDc)
        return adapter.validate_json(response.content)



from typing import Optional

class PythonClient(BaseClient):
    """Client for Python operations"""

    def get_all_script_methods(self, resourceId: Optional[str] = None) -> 'PythonTaskMethodConfiguration':
        """
        Get all script method configurations.
        
        Args:
        resourceId: ResourceId.
        
        Returns:
            'PythonTaskMethodConfiguration': Response data
        """
        path = "/python/resource/scriptMethods"

        # Build request parameters
        params = {}
        if resourceId is not None:
            params["resourceId"] = resourceId

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.PythonTaskMethodConfiguration)
        return adapter.validate_json(response.content)

    def run_script(self, resourceId: Optional[str] = None, fileName: Optional[str] = None, methodName: Optional[str] = None) -> bool:
        """
        Run python script.
        
        Args:
        resourceId: Python resource id.
        fileName: File name.
        methodName: Method name.
        
        Returns:
            bool: Response data
        """
        path = "/python/resource/run"

        # Build request parameters
        params = {}
        if resourceId is not None:
            params["resourceId"] = resourceId
        if fileName is not None:
            params["fileName"] = fileName
        if methodName is not None:
            params["methodName"] = methodName

        # Execute request
        response = self._request("post", path, params=params)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'



from typing import Optional
from datetime import datetime

class QueryTokenAccessClient(BaseClient):
    """Client for QueryTokenAccess operations"""

    def get_tokens_list(self, username: str, onlyValid: Optional[bool] = None, limit: Optional[int] = None, offset: Optional[int] = None) -> 'PagedList_QueryTokenDc':
        # Build path
        path = f"/accessToken/list/{username}"

        # Build request parameters
        params = {}
        if onlyValid is not None:
            params["onlyValid"] = onlyValid
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.PagedList_QueryTokenDc)
        return adapter.validate_json(response.content)

    def create_token_async(self, username: str, validBefore: Optional[datetime] = None) -> str:
        # Build path
        path = f"/accessToken/{username}"

        # Build request parameters
        params = {}
        if validBefore is not None:
            params["validBefore"] = validBefore

        # Execute request
        response = self._request("put", path, params=params)

        return response.text

    def disable_token(self, token: str) -> bool:
        # Build path
        path = f"/accessToken/{token}/disable"

        # Execute request
        response = self._request("post", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def enable_token(self, token: str) -> bool:
        # Build path
        path = f"/accessToken/{token}/enable"

        # Execute request
        response = self._request("post", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def revoke_token(self, token: str) -> bool:
        # Build path
        path = f"/accessToken/{token}"

        # Execute request
        response = self._request("delete", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'



from typing import List, Optional

class RemoteTaskManagerClient(BaseClient):
    """Client for RemoteTaskManager operations"""

    def get(self, id: UUID) -> List['SubTasksDto']:
        """
        Shows SubTask in Task.
        
        Args:
        id: Id.
        
        Returns:
            List['SubTasksDto']: Response data
        """
        # Build path
        path = f"/scheduler/task/{id}/subtasks"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(List[schemas.SubTasksDto])
        return adapter.validate_json(response.content)

    def stop(self, id: UUID) -> UUID:
        """
        Stop the task.
        
        Args:
        id: Id.
        
        Returns:
            UUID: Response data
        """
        # Build path
        path = f"/scheduler/task/{id}/stop"

        # Execute request
        response = self._request("post", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(UUID)
        return adapter.validate_json(response.content)

    def create_task_prototype(self, body: 'TaskPrototypeDto') -> UUID:
        """
        Creates TaskPrototype.
        
        Args:
        body: Request body data
        
        Returns:
            UUID: Response data
        """
        path = "/scheduler"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(UUID)
        return adapter.validate_json(response.content)

    def get_task_prototypes(self, Username: Optional[str] = None, Skip: Optional[int] = None, Take: Optional[int] = None, OrderBy: Optional[str] = None, Desc: Optional[bool] = None) -> 'SearchResultsDto_TaskPrototypeDto':
        """
        Show TaskPrototypes for user.
        
        Args:
        Username: Username.
        Skip: Skip.
        Take: Take.
        OrderBy: OrderBy.
        Desc: Desc.
        
        Returns:
            'SearchResultsDto_TaskPrototypeDto': Response data
        """
        path = "/scheduler"

        # Build request parameters
        params = {}
        if Username is not None:
            params["Username"] = Username
        if Skip is not None:
            params["Skip"] = Skip
        if Take is not None:
            params["Take"] = Take
        if OrderBy is not None:
            params["OrderBy"] = OrderBy
        if Desc is not None:
            params["Desc"] = Desc

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.SearchResultsDto_TaskPrototypeDto)
        return adapter.validate_json(response.content)

    def update_task_prototype(self, id: UUID, body: 'UpdateTaskPrototypeDto') -> UUID:
        """
        Updates task prototype.
        
        Args:
        id: Id.
        body: Request body data
        
        Returns:
            UUID: Response data
        """
        # Build path
        path = f"/scheduler/{id}"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("put", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(UUID)
        return adapter.validate_json(response.content)

    def delete(self, id: UUID) -> UUID:
        """
        Delete task prototype.
        
        Args:
        id: Id of task prototype.
        
        Returns:
            UUID: Response data
        """
        # Build path
        path = f"/scheduler/{id}"

        # Execute request
        response = self._request("delete", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(UUID)
        return adapter.validate_json(response.content)

    def set_enable(self, id: UUID, enable: bool) -> UUID:
        """
        Enables task prototype.
        
        Args:
        id: Id of task prototype.
        enable: is it needs to be enabled.
        
        Returns:
            UUID: Response data
        """
        # Build path
        path = f"/scheduler/{id}/enable/{enable}"

        # Execute request
        response = self._request("post", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(UUID)
        return adapter.validate_json(response.content)

    def get_tasks_for_prototype(self, id: UUID, Status: Optional['RemoteTaskStatus'] = None, Skip: Optional[int] = None, Take: Optional[int] = None, OrderBy: Optional[str] = None, Desc: Optional[bool] = None) -> 'SearchResultsDto_TaskDto':
        """
        Shows Tasks that created for TaskPrototype.
        
        Args:
        id: Id.
        Status: Status.
        Skip: Skip.
        Take: Take.
        OrderBy: OrderBy.
        Desc: Desc.
        
        Returns:
            'SearchResultsDto_TaskDto': Response data
        """
        # Build path
        path = f"/scheduler/{id}/tasks"

        # Build request parameters
        params = {}
        if Status is not None:
            params["Status"] = Status
        if Skip is not None:
            params["Skip"] = Skip
        if Take is not None:
            params["Take"] = Take
        if OrderBy is not None:
            params["OrderBy"] = OrderBy
        if Desc is not None:
            params["Desc"] = Desc

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.SearchResultsDto_TaskDto)
        return adapter.validate_json(response.content)

    def start_task(self, id: UUID, taskId: UUID) -> 'CreatedTaskResultDto':
        """
        Starts new Task for TaskPrototype with task id definition.
        
        Args:
        id: Id of TaskPrototype.
        taskId: Id of new task.
        
        Returns:
            'CreatedTaskResultDto': Response data
        """
        # Build path
        path = f"/scheduler/{id}/start/{taskId}"

        # Execute request
        response = self._request("post", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.CreatedTaskResultDto)
        return adapter.validate_json(response.content)

    def start_task_1(self, id: UUID) -> 'CreatedTaskResultDto':
        """
        Starts new Task for TaskPrototype .
        
        Args:
        id: Id of TaskPrototype.
        
        Returns:
            'CreatedTaskResultDto': Response data
        """
        # Build path
        path = f"/scheduler/{id}/start"

        # Execute request
        response = self._request("post", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.CreatedTaskResultDto)
        return adapter.validate_json(response.content)

    def get_task_resource(self, id: str, updateDefault: Optional[bool] = None) -> 'TaskConfigurationDc':
        """
        Shows SubTask in Task.
        
        Args:
        id: Id.
        updateDefault: Update default configuration.
        
        Returns:
            'TaskConfigurationDc': Response data
        """
        # Build path
        path = f"/scheduler/taskresource/{id}"

        # Build request parameters
        params = {}
        if updateDefault is not None:
            params["updateDefault"] = updateDefault

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.TaskConfigurationDc)
        return adapter.validate_json(response.content)

    def update_python_task_resource(self, id: str, body: 'TaskResourceUpdateDto') -> bool:
        """
        Update task resource.
        
        Args:
        id: Resource id.
        body: Request body data
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/scheduler/taskresource/{id}"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("patch", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def create_task_resource(self, body: 'TaskResourceCreateDto') -> str:
        """
        Create task resource.
        
        Args:
        body: Request body data
        
        Returns:
            str: Response data
        """
        path = "/scheduler/taskresource"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        return response.text

    def get_1(self) -> List['ActiveWorkerDc']:
        """
        Shows active workers.
        
        Returns:
            List['ActiveWorkerDc']: Response data
        """
        path = "/scheduler/worker"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(List[schemas.ActiveWorkerDc])
        return adapter.validate_json(response.content)

    def post(self, body: 'WorkerStartMethodDto') -> bool:
        """
        Run method by HttpPost.
        
        Args:
        body: Request body data
        
        Returns:
            bool: Response data
        """
        path = "/scheduler/worker"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def get_worker(self, type: str) -> List['ActiveWorkerDc']:
        """
        Get worker info by type.
        
        Args:
        type: Worker type.
        
        Returns:
            List['ActiveWorkerDc']: Response data
        """
        # Build path
        path = f"/scheduler/worker/{type}"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(List[schemas.ActiveWorkerDc])
        return adapter.validate_json(response.content)



from typing import List, Optional

class SecurityServiceClient(BaseClient):
    """Client for SecurityService operations"""

    def set_policies(self, body: Dict[str, List['PolicyDc']]) -> bool:
        """
        Adds the given policies to the server policy list. If a policy with the same type and user role already exists, it replaces the existing policy with the new one.
        
        This method requires superuser permission.
        
        Args:
        body: Request body data
        
        Returns:
            bool: Response data
        """
        path = "/bulk/security/policies"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def find_user_by_name_by_roles(self, roles: Optional[List[str]] = None) -> List['SearchedUserDc']:
        """
        Get users list with given roles list.
        
        Args:
        roles: Roles.
        
        Returns:
            List['SearchedUserDc']: Response data
        """
        path = "/security/findUsersWithRoles"

        # Build request parameters
        params = {}
        if roles is not None:
            params["roles"] = roles

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(List[schemas.SearchedUserDc])
        return adapter.validate_json(response.content)

    def get_users_and_roles(self, filter: Optional[str] = None) -> List['UserOrRoleDc']:
        """
        Get users and roles list by filter.
        
        Args:
        filter: Name filter.
        
        Returns:
            List['UserOrRoleDc']: Response data
        """
        path = "/security/usersandroles"

        # Build request parameters
        params = {}
        if filter is not None:
            params["filter"] = filter

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(List[schemas.UserOrRoleDc])
        return adapter.validate_json(response.content)

    def find_user_by_name(self, filter: Optional[str] = None) -> List['SearchedUserDc']:
        """
        Returns the list of users found by username.
        
        Args:
        filter: String filter for the username.
        
        Returns:
            List['SearchedUserDc']: Response data
        """
        path = "/security/users"

        # Build request parameters
        params = {}
        if filter is not None:
            params["filter"] = filter

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(List[schemas.SearchedUserDc])
        return adapter.validate_json(response.content)

    def get_policy_list(self, type: Optional['PolicyType'] = None, roleName: Optional[str] = None) -> List['PolicyDc']:
        """
        Returns the list of server authorization policies of the given type.
        
        This method requires superuser permission.
        
        Args:
        type: Type of the policies.
        roleName: Use role the policy is applied to.
        
        Returns:
            List['PolicyDc']: Response data
        """
        path = "/security/policies"

        # Build request parameters
        params = {}
        if type is not None:
            params["type"] = type
        if roleName is not None:
            params["roleName"] = roleName

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(List[schemas.PolicyDc])
        return adapter.validate_json(response.content)

    def remove_policy(self, type: Optional['PolicyType'] = None, role: Optional[str] = None) -> bool:
        """
        Removes the policy of the given type with the given role. If no such policy is found, nothing is done, and OK response is returned.
        
        This method requires superuser permission.
        
        Args:
        type: Type of the policy.
        role: Use role the policy is applied to.
        
        Returns:
            bool: Response data
        """
        path = "/security/policies"

        # Build request parameters
        params = {}
        if type is not None:
            params["type"] = type
        if role is not None:
            params["role"] = role

        # Execute request
        response = self._request("delete", path, params=params)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def set_policy(self, body: 'PolicyDc') -> bool:
        """
        Adds the given policy to the server policy list. If a policy with the same type and user role already exists, it replaces the existing policy with the new one.
        
        This method requires superuser permission.
        
        Args:
        body: Request body data
        
        Returns:
            bool: Response data
        """
        path = "/security/policies"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def check_limits_for_user(self) -> 'WorkspaceLimitsDc':
        """
        Get limits of workspace.
        
        Returns:
            'WorkspaceLimitsDc': Response data
        """
        path = "/security/limits/user"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.WorkspaceLimitsDc)
        return adapter.validate_json(response.content)

    def check_limits_for_user_1(self, userName: str) -> 'WorkspaceLimitsDc':
        """
        Get limits of workspace.
        
        Args:
        userName: User name.
        
        Returns:
            'WorkspaceLimitsDc': Response data
        """
        # Build path
        path = f"/security/limits/user/{userName}"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.WorkspaceLimitsDc)
        return adapter.validate_json(response.content)

    def check_limits_for_role(self, roleName: str) -> 'WorkspaceLimitsDc':
        """
        Get limits of workspace.
        
        Args:
        roleName: Workspace.
        
        Returns:
            'WorkspaceLimitsDc': Response data
        """
        # Build path
        path = f"/security/limits/role/{roleName}"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.WorkspaceLimitsDc)
        return adapter.validate_json(response.content)

    def get_default_limits(self) -> 'WorkspaceLimitsDc':
        """
        Get default limits of workspace.
        
        Returns:
            'WorkspaceLimitsDc': Response data
        """
        path = "/security/limits/default"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.WorkspaceLimitsDc)
        return adapter.validate_json(response.content)



from typing import List

class SpatialReferencesClient(BaseClient):
    """Client for SpatialReferences operations"""

    def get_availiable_cs_async(self) -> List['SrInfo']:
        """
        Returns list of available spatial references.
        
        Returns:
            List['SrInfo']: Response data
        """
        path = "/srs/list"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(List[schemas.SrInfo])
        return adapter.validate_json(response.content)

    def get_proj4_representation_async(self, name: str) -> str:
        """
        Returns a WKT representation of spatial reference.
        
        Args:
        name: Spatial reference name.
        
        Returns:
            str: Response data
        """
        # Build path
        path = f"/srs/{name}/proj4"

        # Execute request
        response = self._request("get", path)

        return response.text

    def get_wkt_representation_async(self, name: str) -> str:
        """
        Returns a WKT representation of spatial reference.
        
        Args:
        name: Spatial reference name.
        
        Returns:
            str: Response data
        """
        # Build path
        path = f"/srs/{name}/wkt"

        # Execute request
        response = self._request("get", path)

        return response.text





class StatisticClient(BaseClient):
    """Client for Statistic operations"""

    def statistics_db(self, body: 'GetStatisticsDc') -> 'StatisticsDc':
        """
        Calculates statistics for layer attribute.
        
        Args:
        body: Request body data
        
        Returns:
            'StatisticsDc': Response data
        """
        path = "/statistics"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.StatisticsDc)
        return adapter.validate_json(response.content)

    def classify(self, body: 'GetClassifyDc') -> 'ClassifyDc':
        """
        Returns the classified attribute values that correspond to the given number of classes and given condition.
        
        Args:
        body: Request body data
        
        Returns:
            'ClassifyDc': Response data
        """
        path = "/statistics/classify"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.ClassifyDc)
        return adapter.validate_json(response.content)

    def sum_of_product(self, body: 'GetSumOfProductDc') -> 'StatisticsDc':
        """
        Sum of product.
        
        Args:
        body: Request body data
        
        Returns:
            'StatisticsDc': Response data
        """
        path = "/statistics/sumOfProduct"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.StatisticsDc)
        return adapter.validate_json(response.content)



from typing import Optional

class SymbolStorageClient(BaseClient):
    """Client for SymbolStorage operations"""

    def add_symbol_category(self, body: 'CreateSymbolCategoryDc') -> int:
        """
        Add symbol category.
        
        Args:
        body: Request body data
        
        Returns:
            int: Response data
        """
        path = "/symbols/category"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        return response.json()

    def update_symbol_category(self, id: int, body: 'UpdateSymbolCategoryDc') -> bool:
        """
        Update symbol category by id.
        
        Args:
        id: Id symbol category.
        body: Request body data
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/symbols/category/{id}"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("patch", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def get_symbol_category(self, id: int) -> 'SymbolCategoryInfoDc':
        """
        Get symbol category by id.
        
        Args:
        id: Id symbol category.
        
        Returns:
            'SymbolCategoryInfoDc': Response data
        """
        # Build path
        path = f"/symbols/category/{id}"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.SymbolCategoryInfoDc)
        return adapter.validate_json(response.content)

    def remove_symbol_category(self, id: int, cascade: Optional[bool] = None) -> bool:
        """
        Delete symbol category by id.
        
        Args:
        id: Id symbol category.
        cascade: Remove symbols in category.
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/symbols/category/{id}"

        # Build request parameters
        params = {}
        if cascade is not None:
            params["cascade"] = cascade

        # Execute request
        response = self._request("delete", path, params=params)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def get_symbol_categories(self, offset: Optional[int] = None, limit: Optional[int] = None) -> 'PagedList_SymbolCategoryInfoDc':
        """
        Get list of symbol categories.
        
        Args:
        offset: Offset.
        limit: Limit.
        
        Returns:
            'PagedList_SymbolCategoryInfoDc': Response data
        """
        path = "/symbols/category/list"

        # Build request parameters
        params = {}
        if offset is not None:
            params["offset"] = offset
        if limit is not None:
            params["limit"] = limit

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.PagedList_SymbolCategoryInfoDc)
        return adapter.validate_json(response.content)

    def get_category_permissions(self, id: int) -> 'AccessControlListDc':
        """
        Get symbol category permissions.
        
        Args:
        id: Symbol category id.
        
        Returns:
            'AccessControlListDc': Response data
        """
        # Build path
        path = f"/symbols/category/permissions/{id}"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.AccessControlListDc)
        return adapter.validate_json(response.content)

    def add_category_permissions(self, id: int, body: 'AccessControlListDc') -> 'AccessControlListDc':
        """
        Adds permissions for the symbol category, combining existing permissions with the given one.
        
        Args:
        id: Symbol category id.
        body: Request body data
        
        Returns:
            'AccessControlListDc': Response data
        """
        # Build path
        path = f"/symbols/category/permissions/{id}"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.AccessControlListDc)
        return adapter.validate_json(response.content)

    def change_category_permissions(self, id: int, body: 'AccessControlListDc') -> 'AccessControlListDc':
        """
        Replaces existing access control list for the symbol category with the given one.
        
        Args:
        id: Symbol category id.
        body: Request body data
        
        Returns:
            'AccessControlListDc': Response data
        """
        # Build path
        path = f"/symbols/category/permissions/{id}"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("patch", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.AccessControlListDc)
        return adapter.validate_json(response.content)

    def remove_category_permissions(self, id: int, role: str) -> 'AccessControlListDc':
        """
        Removes permissions for the symbol category for the given role.
        
        Args:
        id: Symbol category id.
        role: Role to remove.
        
        Returns:
            'AccessControlListDc': Response data
        """
        # Build path
        path = f"/symbols/category/permissions/{id}/{role}"

        # Execute request
        response = self._request("delete", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.AccessControlListDc)
        return adapter.validate_json(response.content)

    def add_symbol(self, body: 'CreateSymbolDc') -> int:
        """
        Add symbol.
        
        Args:
        body: Request body data
        
        Returns:
            int: Response data
        """
        path = "/symbols"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        return response.json()

    def update_symbol(self, id: int, body: 'UpdateSymbolDc') -> bool:
        """
        Update symbol by id.
        
        Args:
        id: Symbol id.
        body: Request body data
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/symbols/{id}"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("patch", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def get_symbol(self, id: int) -> 'SymbolInfoDc':
        """
        Get symbol by id.
        
        Args:
        id: Symbol id.
        
        Returns:
            'SymbolInfoDc': Response data
        """
        # Build path
        path = f"/symbols/{id}"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.SymbolInfoDc)
        return adapter.validate_json(response.content)

    def remove_symbol(self, id: int) -> bool:
        """
        Remove symbol by id.
        
        Args:
        id: Symbol id.
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/symbols/{id}"

        # Execute request
        response = self._request("delete", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def get_symbols_list(self, idCategory: Optional[int] = None, offset: Optional[int] = None, limit: Optional[int] = None) -> 'PagedList_SymbolInfoDc':
        """
        Get symbol list.
        
        Args:
        idCategory: Id symbol category.
        offset: Offset.
        limit: Limit.
        
        Returns:
            'PagedList_SymbolInfoDc': Response data
        """
        path = "/symbols/list"

        # Build request parameters
        params = {}
        if idCategory is not None:
            params["idCategory"] = idCategory
        if offset is not None:
            params["offset"] = offset
        if limit is not None:
            params["limit"] = limit

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.PagedList_SymbolInfoDc)
        return adapter.validate_json(response.content)

    def get_permissions(self, id: int) -> 'AccessControlListDc':
        """
        Get symbol permissions.
        
        Args:
        id: Symbol id.
        
        Returns:
            'AccessControlListDc': Response data
        """
        # Build path
        path = f"/symbols/permissions/{id}"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.AccessControlListDc)
        return adapter.validate_json(response.content)

    def add_permissions(self, id: int, body: 'AccessControlListDc') -> 'AccessControlListDc':
        """
        Adds permissions for the symbol, combining existing permissions with the given one.
        
        Args:
        id: Symbol id.
        body: Request body data
        
        Returns:
            'AccessControlListDc': Response data
        """
        # Build path
        path = f"/symbols/permissions/{id}"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.AccessControlListDc)
        return adapter.validate_json(response.content)

    def change_permissions(self, id: int, body: 'AccessControlListDc') -> 'AccessControlListDc':
        """
        Replaces existing access control list for the symbol with the given one.
        
        Args:
        id: Symbol id.
        body: Request body data
        
        Returns:
            'AccessControlListDc': Response data
        """
        # Build path
        path = f"/symbols/permissions/{id}"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("patch", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.AccessControlListDc)
        return adapter.validate_json(response.content)

    def remove_permissions(self, id: int, role: str) -> 'AccessControlListDc':
        """
        Removes permissions for the symbol for the given role.
        
        Args:
        id: Symbol id.
        role: Role to remove.
        
        Returns:
            'AccessControlListDc': Response data
        """
        # Build path
        path = f"/symbols/permissions/{id}/{role}"

        # Execute request
        response = self._request("delete", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.AccessControlListDc)
        return adapter.validate_json(response.content)



from typing import List, Optional

class TablesClient(BaseClient):
    """Client for Tables operations"""

    def create_table(self, body: 'DetailedTableInfoDc') -> 'DetailedTableInfoDc':
        """
        Creates a new table.
        
        Args:
        body: Request body data
        
        Returns:
            'DetailedTableInfoDc': Response data
        """
        path = "/tables"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.DetailedTableInfoDc)
        return adapter.validate_json(response.content)

    def update_table(self, name: str, body: 'UpdateTableDc') -> 'DetailedTableInfoDc':
        """
        Update exists table.
        
        Args:
        name: The full name of the table.
        body: Request body data
        
        Returns:
            'DetailedTableInfoDc': Response data
        """
        # Build path
        path = f"/tables/{name}"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("patch", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.DetailedTableInfoDc)
        return adapter.validate_json(response.content)

    def put_table(self, name: str, body: 'DetailedTableInfoDc') -> 'DetailedTableInfoDc':
        """
        Override exists table.
        
        Args:
        name: The full name of the table.
        body: Request body data
        
        Returns:
            'DetailedTableInfoDc': Response data
        """
        # Build path
        path = f"/tables/{name}"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("put", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.DetailedTableInfoDc)
        return adapter.validate_json(response.content)

    def get_table_info(self, name: str) -> 'DetailedTableInfoDc':
        """
        Returns the table information and schema.
        
        Args:
        name: The name of the table.
        
        Returns:
            'DetailedTableInfoDc': Response data
        """
        # Build path
        path = f"/tables/{name}"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.DetailedTableInfoDc)
        return adapter.validate_json(response.content)

    def get_tables_info_async(self, tableNames: Optional[List[str]] = None) -> List['DetailedTableInfoDc']:
        """
        Returns the tables information.
        
        Args:
        tableNames: Table names.
        
        Returns:
            List['DetailedTableInfoDc']: Response data
        """
        path = "/tables/batchInfo"

        # Build request parameters
        params = {}
        if tableNames is not None:
            params["tableNames"] = tableNames

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(List[schemas.DetailedTableInfoDc])
        return adapter.validate_json(response.content)

    def get_table_data(self, name: str, idField: Optional[str] = None, geometryField: Optional[str] = None, filter: Optional[str] = None, sort: Optional[List[str]] = None, limit: Optional[int] = None, offset: Optional[int] = None, includeGeometry: Optional[bool] = None, columns: Optional[List[str]] = None) -> 'PagedList_FeatureDc':
        """
        Retrieves the data from the table.
        
        Args:
        name: Name of the table.
        idField: Id field name.
        geometryField: Geometry field name.
        filter: String filter for the all text column (uses % and _ wild cards like SQL).
        sort: Comma separated list of attributes by which to sort the resulting feature list. If the attribute name is preceded with the \"-\" sign, sorting by this attribute will be in descending order.
        limit: Max number of rows to return.
        offset: The first row index to return.
        includeGeometry: Include column with geometry.
        columns: Columns to select.
        
        Returns:
            'PagedList_FeatureDc': Response data
        """
        # Build path
        path = f"/tables/{name}/data"

        # Build request parameters
        params = {}
        if idField is not None:
            params["idField"] = idField
        if geometryField is not None:
            params["geometryField"] = geometryField
        if filter is not None:
            params["filter"] = filter
        if sort is not None:
            params["sort"] = sort
        if limit is not None:
            params["limit"] = limit
        if offset is not None:
            params["offset"] = offset
        if includeGeometry is not None:
            params["includeGeometry"] = includeGeometry
        if columns is not None:
            params["columns"] = columns

        # Execute request
        response = self._request("get", path, params=params)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.PagedList_FeatureDc)
        return adapter.validate_json(response.content)

    def write_table_data(self, name: str, body: List[Dict[str, Any]]) -> bool:
        """
        Adds the data to the table.
        
        Args:
        name: Name of the table.
        body: Request body data
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/tables/{name}/data"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def update_table_data(self, name: str, body: List[Dict[str, Any]], idColumn: Optional[str] = None) -> bool:
        """
        Updates the data in the table.
        
        Args:
        name: Name of the table.
        idColumn: Id column name.
        body: Request body data
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/tables/{name}/data"

        # Build request parameters
        params = {}
        if idColumn is not None:
            params["idColumn"] = idColumn

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("patch", path, params=params, json=json_data)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def delete_table_data(self, name: str, idColumn: Optional[str] = None, ids: Optional[List[str]] = None) -> bool:
        """
        Delete data rows from the table.
        
        Args:
        name: Name of the table.
        idColumn: Id column name.
        ids: Ids of rows to delete.
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/tables/{name}/data"

        # Build request parameters
        params = {}
        if idColumn is not None:
            params["idColumn"] = idColumn
        if ids is not None:
            params["ids"] = ids

        # Execute request
        response = self._request("delete", path, params=params)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def map_table(self, body: 'MapTableInfoDc', dataProvider: Optional[str] = None, type: Optional[str] = None) -> 'DetailedTableInfoDc':
        """
        Map table to exists table.
        
        Args:
        dataProvider: Name of the remote data provider. Allows to map table from foreign db.
        type: Type of the resource. Default type os Table.
        body: Request body data
        
        Returns:
            'DetailedTableInfoDc': Response data
        """
        path = "/tables/map-table"

        # Build request parameters
        params = {}
        if dataProvider is not None:
            params["dataProvider"] = dataProvider
        if type is not None:
            params["type"] = type

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, params=params, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.DetailedTableInfoDc)
        return adapter.validate_json(response.content)

    def unmap_table_async(self, name: str) -> bool:
        """
        Unmap datasource from table.
        
        Args:
        name: Name of the datasource.
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/tables/map-table/{name}"

        # Execute request
        response = self._request("delete", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def create_view_from_query_layer(self, body: 'CreateViewFromQueryLayerDc') -> 'DetailedTableInfoDc':
        """
        Creates a new view from query layer.
        
        Args:
        body: Request body data
        
        Returns:
            'DetailedTableInfoDc': Response data
        """
        path = "/tables/fromLayer"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.DetailedTableInfoDc)
        return adapter.validate_json(response.content)

    def create_view_from_query(self, body: 'CreateViewFromQueryDc') -> 'DetailedTableInfoDc':
        """
        Creates a new view from query.
        
        Args:
        body: Request body data
        
        Returns:
            'DetailedTableInfoDc': Response data
        """
        path = "/tables/fromQuery"

        # Execute request
        def serialize_body(body):
            if isinstance(body, list):
                return [item.model_dump(by_alias=True, exclude_unset=True) if hasattr(item, 'model_dump') else item for item in body]
            elif hasattr(body, 'model_dump'):
                return body.model_dump(by_alias=True, exclude_unset=True)
            else:
                return body
        json_data = serialize_body(body)
        response = self._request("post", path, json=json_data)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.DetailedTableInfoDc)
        return adapter.validate_json(response.content)

    def is_exists_async(self, name: str) -> bool:
        """
        Check is resource exists.
        
        Args:
        name: Resource name.
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/tables/{name}/exists"

        # Execute request
        response = self._request("get", path)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def get_resource_dependencies(self, name: str) -> 'ResourceDependenciesDc':
        """
        Get resource dependencies.
        
        Args:
        name: The name of the resource.
        
        Returns:
            'ResourceDependenciesDc': Response data
        """
        # Build path
        path = f"/tables/{name}/dependencies"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.ResourceDependenciesDc)
        return adapter.validate_json(response.content)

    def get_resource_references(self, name: str) -> 'ResourceDependenciesDc':
        """
        Returns the resource dependency information.
        
        Args:
        name: The name of the layer.
        
        Returns:
            'ResourceDependenciesDc': Response data
        """
        # Build path
        path = f"/tables/{name}/references"

        # Execute request
        response = self._request("get", path)

        from pydantic import TypeAdapter
        from . import schemas
        adapter = TypeAdapter(schemas.ResourceDependenciesDc)
        return adapter.validate_json(response.content)



from typing import Optional

class VectorTileServiceClient(BaseClient):
    """Client for VectorTileService operations"""

    def get_vector_tile(self, name: str, z: int, x: int, y: int, condition: Optional[str] = None, dataFilterId: Optional[str] = None, attributes: Optional[List[str]] = None) -> bool:
        """
        Get vector tile from visible project layers or single layer.
        
        Args:
        name: Project or layer name.
        z: Zoom level.
        x: X tile coordinate.
        y: Y tile coordinate.
        condition: Condition.
        dataFilterId: Id of override data filter to apply to the layer. If not set, the default filter is used.
        attributes: List of included feature attribute names.
        
        Returns:
            bool: Response data
        """
        # Build path
        path = f"/vt/{name}/{z}/{x}/{y}.pbf"

        # Build request parameters
        params = {}
        if condition is not None:
            params["condition"] = condition
        if dataFilterId is not None:
            params["dataFilterId"] = dataFilterId
        if attributes is not None:
            params["attributes"] = attributes

        # Execute request
        response = self._request("get", path, params=params)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'



from typing import Optional

class WfsServerClient(BaseClient):
    """Client for WfsServer operations"""

    def get_capabilities(self, Service: Optional[str] = None, AcceptVersions: Optional[List[str]] = None, Sections: Optional[List[str]] = None, AcceptFormats: Optional[List[str]] = None) -> bool:
        """
        Returns get capabilities of wfs service.
        
        Args:
        Service: Name of the service.
        AcceptVersions: When omitted, server shall return latest supported version.
        Sections: When omitted or not supported by server, server shall return complete service metadata (Capabilities) document.
        AcceptFormats: When omitted or not supported by server, server shall return service metadata document using the MIME type \"text/xml\".
        
        Returns:
            bool: Response data
        """
        path = "/wfs"

        # Build request parameters
        params = {}
        if Service is not None:
            params["Service"] = Service
        if AcceptVersions is not None:
            params["AcceptVersions"] = AcceptVersions
        if Sections is not None:
            params["Sections"] = Sections
        if AcceptFormats is not None:
            params["AcceptFormats"] = AcceptFormats

        # Execute request
        response = self._request("get", path, params=params)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def get_shared_capabilities(self, Service: Optional[str] = None, AcceptVersions: Optional[List[str]] = None, Sections: Optional[List[str]] = None, AcceptFormats: Optional[List[str]] = None) -> bool:
        """
        Returns get capabilities of wfs service.
        
        Args:
        Service: Name of the service.
        AcceptVersions: When omitted, server shall return latest supported version.
        Sections: When omitted or not supported by server, server shall return complete service metadata (Capabilities) document.
        AcceptFormats: When omitted or not supported by server, server shall return service metadata document using the MIME type \"text/xml\".
        
        Returns:
            bool: Response data
        """
        path = "/shared/wfs"

        # Build request parameters
        params = {}
        if Service is not None:
            params["Service"] = Service
        if AcceptVersions is not None:
            params["AcceptVersions"] = AcceptVersions
        if Sections is not None:
            params["Sections"] = Sections
        if AcceptFormats is not None:
            params["AcceptFormats"] = AcceptFormats

        # Execute request
        response = self._request("get", path, params=params)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'

    def get_public_capabilities(self, Service: Optional[str] = None, AcceptVersions: Optional[List[str]] = None, Sections: Optional[List[str]] = None, AcceptFormats: Optional[List[str]] = None) -> bool:
        """
        Returns get capabilities of wfs service.
        
        Args:
        Service: Name of the service.
        AcceptVersions: When omitted, server shall return latest supported version.
        Sections: When omitted or not supported by server, server shall return complete service metadata (Capabilities) document.
        AcceptFormats: When omitted or not supported by server, server shall return service metadata document using the MIME type \"text/xml\".
        
        Returns:
            bool: Response data
        """
        path = "/public/wfs"

        # Build request parameters
        params = {}
        if Service is not None:
            params["Service"] = Service
        if AcceptVersions is not None:
            params["AcceptVersions"] = AcceptVersions
        if Sections is not None:
            params["Sections"] = Sections
        if AcceptFormats is not None:
            params["AcceptFormats"] = AcceptFormats

        # Execute request
        response = self._request("get", path, params=params)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'



from typing import Optional

class WmtsClient(BaseClient):
    """Client for Wmts operations"""

    def process_request_async(self, layer: Optional[str] = None, version: Optional[str] = None, request: Optional[str] = None, tileMatrix: Optional[str] = None, tileRow: Optional[int] = None, tileCol: Optional[int] = None) -> bool:
        """
        WMTS Protocol endpoint.
        
        Args:
        layer: Layer name.
        version: wmts version.
        request: Request type.
        tileMatrix: Tile matrix.
        tileRow: Tile row.
        tileCol: Tile col.
        
        Returns:
            bool: Response data
        """
        path = "/wmts"

        # Build request parameters
        params = {}
        if layer is not None:
            params["layer"] = layer
        if version is not None:
            params["version"] = version
        if request is not None:
            params["request"] = request
        if tileMatrix is not None:
            params["tileMatrix"] = tileMatrix
        if tileRow is not None:
            params["tileRow"] = tileRow
        if tileCol is not None:
            params["tileCol"] = tileCol

        # Execute request
        response = self._request("get", path, params=params)

        # Parse boolean response from server. We only reach
        # here on a 2xx (non-2xx already raised), so an empty
        # body means success-without-payload -> True.
        text = response.text.strip()
        if not text:
            return True
        try:
            return response.json()  # Should return True/False from server
        except Exception:
            return text.lower() == 'true'



class APIClient(BaseClient):
    """Synchronous main API client combining all specialized clients."""

    def __init__(self, base_url: str = "http://evergis", timeout: float = 120.0, connect_timeout: float = 10.0, read_timeout: Optional[float] = None, sb_token: Optional[str] = None):
        """Initializes synchronous main API client.

        Args:
            base_url: Base API URL (default: http://evergis)
            timeout: General request timeout in seconds (default: 120)
            connect_timeout: Connection timeout in seconds (default: 10)
            read_timeout: Read timeout in seconds (if None, uses timeout)
            sb_token: Authentication token
        """
        super().__init__(base_url, timeout, connect_timeout, read_timeout, sb_token)

        # All sub-clients share the same httpx client instance
        # This ensures set_bearer_token() propagates to all sub-clients
        self.account = AccountClient(base_url, timeout, connect_timeout, read_timeout, sb_token, _shared_client=self.client)
        self.accountpreview = AccountPreviewClient(base_url, timeout, connect_timeout, read_timeout, sb_token, _shared_client=self.client)
        self.bulkoperations = BulkOperationsClient(base_url, timeout, connect_timeout, read_timeout, sb_token, _shared_client=self.client)
        self.catalog = CatalogClient(base_url, timeout, connect_timeout, read_timeout, sb_token, _shared_client=self.client)
        self.catalogsync = CatalogSyncClient(base_url, timeout, connect_timeout, read_timeout, sb_token, _shared_client=self.client)
        self.clientsettings = ClientSettingsClient(base_url, timeout, connect_timeout, read_timeout, sb_token, _shared_client=self.client)
        self.datasource = DataSourceClient(base_url, timeout, connect_timeout, read_timeout, sb_token, _shared_client=self.client)
        self.eql = EqlClient(base_url, timeout, connect_timeout, read_timeout, sb_token, _shared_client=self.client)
        self.externalproviders = ExternalProvidersClient(base_url, timeout, connect_timeout, read_timeout, sb_token, _shared_client=self.client)
        self.feedback = FeedbackClient(base_url, timeout, connect_timeout, read_timeout, sb_token, _shared_client=self.client)
        self.filtersservice = FiltersServiceClient(base_url, timeout, connect_timeout, read_timeout, sb_token, _shared_client=self.client)
        self.geocodeservice = GeocodeServiceClient(base_url, timeout, connect_timeout, read_timeout, sb_token, _shared_client=self.client)
        self.importservice = ImportServiceClient(base_url, timeout, connect_timeout, read_timeout, sb_token, _shared_client=self.client)
        self.layers = LayersClient(base_url, timeout, connect_timeout, read_timeout, sb_token, _shared_client=self.client)
        self.projects = ProjectsClient(base_url, timeout, connect_timeout, read_timeout, sb_token, _shared_client=self.client)
        self.python = PythonClient(base_url, timeout, connect_timeout, read_timeout, sb_token, _shared_client=self.client)
        self.querytokenaccess = QueryTokenAccessClient(base_url, timeout, connect_timeout, read_timeout, sb_token, _shared_client=self.client)
        self.remotetaskmanager = RemoteTaskManagerClient(base_url, timeout, connect_timeout, read_timeout, sb_token, _shared_client=self.client)
        self.securityservice = SecurityServiceClient(base_url, timeout, connect_timeout, read_timeout, sb_token, _shared_client=self.client)
        self.spatialreferences = SpatialReferencesClient(base_url, timeout, connect_timeout, read_timeout, sb_token, _shared_client=self.client)
        self.statistic = StatisticClient(base_url, timeout, connect_timeout, read_timeout, sb_token, _shared_client=self.client)
        self.symbolstorage = SymbolStorageClient(base_url, timeout, connect_timeout, read_timeout, sb_token, _shared_client=self.client)
        self.tables = TablesClient(base_url, timeout, connect_timeout, read_timeout, sb_token, _shared_client=self.client)
        self.vectortileservice = VectorTileServiceClient(base_url, timeout, connect_timeout, read_timeout, sb_token, _shared_client=self.client)
        self.wfsserver = WfsServerClient(base_url, timeout, connect_timeout, read_timeout, sb_token, _shared_client=self.client)
        self.wmts = WmtsClient(base_url, timeout, connect_timeout, read_timeout, sb_token, _shared_client=self.client)


__all__ = [
    "APIClient",
    "AccountClient",
    "AccountPreviewClient",
    "BaseClient",
    "BulkOperationsClient",
    "CatalogClient",
    "CatalogSyncClient",
    "ClientSettingsClient",
    "DataSourceClient",
    "EqlClient",
    "ExternalProvidersClient",
    "FeedbackClient",
    "FiltersServiceClient",
    "GeocodeServiceClient",
    "ImportServiceClient",
    "LayersClient",
    "ProjectsClient",
    "PythonClient",
    "QueryTokenAccessClient",
    "RemoteTaskManagerClient",
    "SecurityServiceClient",
    "SpatialReferencesClient",
    "StatisticClient",
    "SymbolStorageClient",
    "TablesClient",
    "VectorTileServiceClient",
    "WfsServerClient",
    "WmtsClient",
]