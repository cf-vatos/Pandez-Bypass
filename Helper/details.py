from __future__     import annotations
from typing         import Optional, Tuple, Dict, Any, List
from dataclasses    import dataclass

import re
import json

from curl_cffi import requests
from requestcord import HeaderGenerator

from Helper import logger


@dataclass(frozen=True)
class DiscordEntityIDs:
    guild_id: int
    channel_id: int
    message_id: int
    author_id: int
    custom_id: str


class InvalidMessageLinkError(ValueError):
    """Raised when an invalid Discord message link is provided"""

    pass


class APIRequestError(Exception):
    """Base class for API request exceptions"""

    pass


class MessageDetails:
    def __init__(self, message_link: str, token: str):
        self._session = requests.Session(impersonate="chrome110")
        self._token = token
        self._message_link = message_link
        self._ids = self._validate_and_extract_ids()
        self._button_data = self._retrieve_button_metadata()

    def _validate_and_extract_ids(self) -> Tuple[int, int, int]:
        """Validate message link structure and extract entity IDs"""
        if match := re.search(
            r"discord\.com/channels/(\d+)/(\d+)/(\d+)", self._message_link
        ):
            return tuple(map(int, match.groups()))
        raise InvalidMessageLinkError("Invalid Discord message URL structure")

    def _generate_headers(self) -> Dict[str, str]:
        """Generate authenticated headers for API requests"""
        return HeaderGenerator().generate_headers(token=self._token)

    def _fetch_message_data(self) -> List[Dict[str, Any]]:
        """Retrieve message data from Discord API"""
        url = f"https://discord.com/api/v9/channels/{self._ids[1]}/messages"
        params = {"limit": 1, "around": self._ids[2]}

        try:
            response = self._session.get(
                url, headers=self._generate_headers(), params=params
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestsError as e:
            logger.error(f"Network error fetching message data: {str(e)}")
            raise APIRequestError("Failed to retrieve message data") from e
        except json.JSONDecodeError as e:
            logger.error("Invalid JSON response from API")
            raise APIRequestError("Malformed API response") from e

    def _parse_button_components(
        self, components: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Recursively search for button components in message structure"""
        for component in components:
            if component.get("type") == 1:
                if found := self._parse_button_components(
                    component.get("components", [])
                ):
                    return found
            elif component.get("type") == 2:
                if custom_id := component.get("custom_id"):
                    return custom_id
        return None

    def _retrieve_button_metadata(self) -> Tuple[int, str]:
        """Extract author ID and button custom ID from message data"""
        messages = self._fetch_message_data()

        if not messages:
            logger.error("No messages found in API response")
            raise APIRequestError("Empty message data received")

        message = messages[0]
        author_id = message.get("author", {}).get("id")

        if not author_id:
            logger.error("Message author information missing")
            raise ValueError("Could not determine message author")

        if custom_id := self._parse_button_components(
            message.get("components", [])
        ):
            return (int(author_id), custom_id)

        logger.error("No valid button components found in message")
        raise ValueError("Target message contains no clickable buttons")

    @property
    def entity_ids(self) -> DiscordEntityIDs:
        """Return structured information"""
        return DiscordEntityIDs(
            guild_id=self._ids[0],
            channel_id=self._ids[1],
            message_id=self._ids[2],
            author_id=self._button_data[0],
            custom_id=self._button_data[1],
        )
