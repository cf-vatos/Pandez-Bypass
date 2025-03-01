from typing import List, Dict, Any

import time
import random
import requests

from Helper import logger, DiscordConfig


class Utils:
    @staticmethod
    def get_tokens(formatting: bool) -> List[str]:
        """
        Reads the 'tokens.txt' file and returns a list of tokens.
        """
        try:
            with open("tokens.txt", "r", encoding="utf-8") as file:
                tokens = [
                    (
                        token.split(":")[2].strip()
                        if formatting and ":" in token
                        else token.strip()
                    )
                    for token in file.readlines()
                ]
            return tokens
        except FileNotFoundError:
            return []

    @staticmethod
    def get_random_token(max_attempts=10):
        """
        Fetches a random token from Utils and validates it by making requests to Discord API.
        """
        tokens = Utils.get_tokens(formatting=True)

        if not tokens:
            return None

        for _ in range(max_attempts):
            token = random.choice(tokens)

            user_response = requests.get(
                "https://discord.com/api/v9/users/@me",
                headers={"Authorization": token},
            )

            if user_response.status_code == 200:
                settings_response = requests.get(
                    "https://discord.com/api/v9/users/@me/settings",
                    headers={"Authorization": token},
                )

                if settings_response.status_code == 200:
                    return token
                else:
                    pass
            else:
                pass

        return None

    @staticmethod
    def api_request(session, endpoint: str, **kwargs) -> requests.Response:
        """Make authenticated API request"""
        config = DiscordConfig
        url = f"{config.base_url}{config.api_version}/{endpoint}"

        try:
            response = session.post(url, **kwargs)
            try:
                response.raise_for_status()
            except:
                pass
            return response
        except requests.exceptions.HTTPError as e:
            logger.error(f"API request failed: {e}")
            if e.response.status_code == 429:
                retry_after = e.response.json().get("retry_after", 5)
                logger.info(
                    f"Rate limited - retrying after {retry_after} seconds"
                )
                time.sleep(retry_after)
                return Utils.api_request(session, endpoint, **kwargs)
            raise

    @staticmethod
    def _is_captcha_message(
        captcha: str, message: Dict[str, Any], title: str, description: str
    ) -> bool:
        """Check if message contains captcha request"""
        embeds = message.get("embeds", [])
        if not embeds:
            return False

        embed = embeds[0]
        if captcha == "pandez":
            return title in embed.get("title", "") or description in embed.get(
                "description", ""
            )

        if captcha == "wick":
            title_match = any(
                field["name"]
                for field in embed.get("fields", [])
                if title in field["name"]
            )
            description_match = any(
                field["value"]
                for field in embed.get("fields", [])
                if description in field["value"]
            )

            return title_match or description_match

    @staticmethod
    def _parse_captcha_details(message: Dict[str, Any]) -> Dict[str, Any]:
        """Extract captcha details from the message."""
        embed = message["embeds"][0]
        captcha_image_url = embed.get("image", {}).get("url", "")
        captcha_options = []

        for component in message.get("components", []):
            for sub_component in component.get("components", []):
                if sub_component.get("custom_id") == "captcha":
                    captcha_options = [
                        {"value": option["value"], "label": option["label"]}
                        for option in sub_component.get("options", [])
                    ]
                    break

        return {
            "image_url": captcha_image_url,
            "options": captcha_options,
            "message_id": message.get("id"),
            "channel_id": message.get("channel_id"),
        }

    @staticmethod
    def _generate_nonce(length: int = 19) -> str:
        return "".join(str(random.randint(1, 9)) for _ in range(length))
