import json
import requests
from pydantic import BaseModel, StrictStr
from unitycatalog import client as uc

from auth import check_response


class Meta(BaseModel):
    resourceType: str
    created: str
    lastModified: str

class Photo(BaseModel):
    value: str

class Email(BaseModel):
    value: str

class User(BaseModel):
    id: str
    userName: str
    displayName: str
    emails: list[Email]
    active: bool
    meta: Meta
    schemas: list[str]
    photos: list[Photo]

def get_users(access_token, url: str) -> list[User] | None:
    """Retrieves existing users"""
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.get(url, headers=headers)
    users = check_response(response).get('Resources', [])
    return [User.model_validate(user) for user in users]


def get_user_by_username(username: str, access_token: str, url: str) -> User:
    """Retrieve a user by username."""
    users = {user.userName: user for user in get_users(access_token, url)}
    return users.get(username)



def get_user(access_token: str, user_id: str) -> User:
    """Gets the specified user."""
    url = f"http://uc:8080/api/1.0/unity-control/scim2/Users/{user_id}"
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/scim+json'
    }
    response = requests.get(url, headers=headers)
    return User.model_validate(check_response(response))


def get_or_create_user(access_token: str, username: str, display_name:str) -> User:
    """Create a user in Unity Catalog."""
    url = "http://uc:8080/api/1.0/unity-control/scim2/Users"

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    payload = {
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
        "userName": username,
        "displayName": display_name,
        "emails": [
            {
                "value": username,
                "primary": True
            }
        ],
    }

    response = requests.post(url, json=payload, headers=headers)
    if not isinstance(response.json(), dict) and int(json.loads(response.json())['status']) == 409:
        print(f"User {username} already exists")
        user =  get_user_by_username(username=username, access_token=access_token, url=url)
        if not user:
            raise ValueError(f"Existing user {username} not found")
        return user
    return User.model_validate(check_response(response))

async def grant(full_name: StrictStr, user: User, privileges: uc.Privilege, securable_type: uc.SecurableType,
                grants_api: uc.GrantsApi, headers: dict):
    update_permissions = uc.UpdatePermissions(
        changes=[uc.PermissionsChange(principal=user.userName, add=privileges, remove=[])]
    )
    return await grants_api.update(
        securable_type=securable_type,
        full_name=full_name,
        update_permissions=update_permissions,
        _headers=headers
    )
