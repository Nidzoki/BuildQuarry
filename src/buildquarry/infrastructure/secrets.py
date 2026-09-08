"""Local API-key storage."""

import os

import keyring

SERVICE_NAME = "BuildQuarry"
KEY_NAME = "gemini_api_key"


def get_api_key() -> str:
    return os.environ.get("GEMINI_API_KEY") or keyring.get_password(SERVICE_NAME, KEY_NAME) or ""


def save_api_key(api_key: str) -> None:
    keyring.set_password(SERVICE_NAME, KEY_NAME, api_key)


def delete_api_key() -> None:
    try:
        keyring.delete_password(SERVICE_NAME, KEY_NAME)
    except keyring.errors.PasswordDeleteError:
        pass
