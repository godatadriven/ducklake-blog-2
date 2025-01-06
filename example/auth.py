import subprocess
from enum import Enum

import requests
from pydantic import BaseModel, Field
import warnings
from urllib3.exceptions import InsecureRequestWarning


warnings.simplefilter('ignore', InsecureRequestWarning)

class RequestError(Exception):
    """Custom exception for failed requests."""
    pass


def check_response(response: requests.Response) -> dict:
    """Generalized function to check the response status and return the JSON data if successful."""
    if response.status_code in [200, 201]:
        return response.json()
    else:
        raise RequestError(f"Request failed with status code {response.status_code}: {response.text}")


class OAuthTokenExchangeRequest(BaseModel):
    grant_type: str = Field(..., description="The grant type for the token exchange request.")
    subject_token: str = Field(..., description="The security token that represents the identity of the party on behalf of whom the request is being made.")
    subject_token_type: str = Field(..., description="The type of the subject token.")
    scope: str | None = Field(None, description="The authorization scope for the token exchange request.")
    requested_token_type: str | None= Field(None, description="The type of the requested token.")
    actor_token: str | None = Field(None, description="The security token that represents the identity of the acting party.")
    actor_token_type: str | None = Field(None, description="The type of the actor token.")


def get_admin_token(token_file:str) -> str | None:
    """Retrieves the admin token from the token.txt file."""
    # Command to retrieve the token
    command = ["cat", token_file]

    # Execute the command and capture the output
    result = subprocess.run(command, capture_output=True, text=True)

    # Check if the command was successful
    if result.returncode == 0:
        # Return the token
        return result.stdout.strip()
    else:
        print("Failed to retrieve token:", result.stderr)
        return None

def request_token(request_data: OAuthTokenExchangeRequest, url: str) -> str:
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    response = requests.post(url, data=request_data.dict(), headers=headers)
    return check_response(response)['access_token']


class TokenType(str, Enum):
    AUTHORIZATION_CODE = "authorization_code"
    CLIENT_CREDENTIALS = "client_credentials"
    PASSWORD = "password"
    REFRESH_TOKEN = "refresh_token"
    TOKEN_EXCHANGE = "token-exchange"

def get_bearer_token(url: str, token: str, token_type: TokenType, scope: str) -> str:
    """Gets a bearer token with specified scope using the token exchange endpoint."""
    request_data = OAuthTokenExchangeRequest(
        grant_type=f'urn:ietf:params:oauth:grant-type:token-exchange',
        subject_token=token,
        subject_token_type=f'urn:ietf:params:oauth:token-type:{token_type.value}',
        scope=scope,
        requested_token_type='urn:ietf:params:oauth:token-type:access_token',
    )
    return request_token(request_data, url)


