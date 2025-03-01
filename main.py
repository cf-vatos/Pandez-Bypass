from curl_cffi                  import requests
from requestcord                import HeaderGenerator
from requestcord                import Session as SessionID

from Helper                     import   DiscordConfig, logger
from Helper.captcha             import CaptchaSolver, TwoCaptchaSolver
from Helper.websocket_manager   import WebSocketManager
from Helper.details             import (
    MessageDetails,
    InvalidMessageLinkError,
    APIRequestError,
    DiscordEntityIDs,
)
from Helper.pandez              import PandezCaptcha
from Helper.utils               import Utils


class CaptchaDiscordBypass:
    def __init__(
        self,
        token: str,
        packed_ids: DiscordEntityIDs,
        config: DiscordConfig = DiscordConfig(),
        captcha_type: str = "pandez",
        captcha_solver: CaptchaSolver = TwoCaptchaSolver(),
    ):
        self.session = requests.Session(impersonate="chrome")
        self.token = token
        self.packed_ids = packed_ids
        self.guild_id = packed_ids.guild_id
        self.channel_id = packed_ids.channel_id
        self.message_id = packed_ids.message_id
        self.custom_id = packed_ids.custom_id
        self.application_id = packed_ids.author_id
        self.config = config
        self.captcha_solver = captcha_solver
        self.captcha_type = captcha_type
        self.headers = HeaderGenerator().generate_headers(token=token)
        self.session_id = SessionID().get_session(token=token)
        self.ws_manager = WebSocketManager(token, config)

        self.session.headers = self.headers

    def send_start_interaction(self, message_flags: int) -> None:
        """Send initial interaction"""
        payload = {
            "type": 3,
            "nonce": Utils._generate_nonce(),
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
            "message_flags": message_flags,
            "message_id": self.message_id,
            "application_id": self.application_id,
            "session_id": self.session_id,
            "data": {"component_type": 2, "custom_id": self.custom_id},
        }
        Utils.api_request(self.session, "interactions", json=payload)

    def bypass(self) -> None:
        """Main bypass workflow"""
        try:
            self.ws_manager.connect()
            self.send_start_interaction(message_flags=0)
            logger.info("Clicked Button")

            if self.captcha_type == "pandez":
                PandezCaptcha(
                    ws_manager=self.ws_manager,
                    session=self.session,
                    packed_ids=self.packed_ids,
                    session_id=self.session_id,
                ).handle_pandez_captcha()
                return
            if self.captcha_type == "wick":  # // Next Update
                pass

        except Exception as e:
            logger.error(f"Bypass failed: {e}")
            raise


def main() -> None:
    """Main function."""
    random_valid_token = Utils.get_random_token()
    tokens = Utils.get_tokens(formatting=True)
    logger.info("Getting Infos..")
    try:
        extractor = MessageDetails(
            message_link="YOUR_MESSAGE_LINK",
            token=random_valid_token,
        )
        details = extractor.entity_ids
        for token in tokens:
            logger.info("Starting to Bypass Pandez..")
            bypasser = CaptchaDiscordBypass(
                token=token,
                packed_ids=details,
                captcha_type="pandez",
                config=DiscordConfig(),
            )
            try:
                bypasser.bypass()
            except KeyboardInterrupt:
                logger.info("Bypass interrupted by user")

    except (InvalidMessageLinkError, APIRequestError, ValueError) as e:
        logger.error(f"Extraction failed: {str(e)}")
        exit(1)


if __name__ == "__main__":
    main()
