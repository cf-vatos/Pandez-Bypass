from Helper         import logger
from Helper.utils   import Utils

from Helper.captcha import CaptchaSolver, TwoCaptchaSolver


class PandezCaptcha:
    def __init__(self, ws_manager, session, packed_ids, session_id):
        self.session = session
        self.ws_manager = ws_manager
        self.captcha_solver: CaptchaSolver = TwoCaptchaSolver()
        self.guild_id = packed_ids.guild_id
        self.channel_id = packed_ids.channel_id
        self.application_id = packed_ids.author_id
        self.session_id = session_id

    def handle_pandez_captcha(self) -> None:
        """Handle Pandez captcha type by clicking buttons and solving captcha."""
        logger.info("Handling Pandez captcha...")

        while True:
            event = self.ws_manager.receive_event()
            if event.get("t") in ["MESSAGE_CREATE", "MESSAGE_UPDATE"]:
                message = event.get("d", {})

                if Utils._is_captcha_message(
                    "pandez",
                    message,
                    "3 - Are you human?",
                    "To continue, you must prove you are human.",
                ):
                    captcha_details = Utils._parse_captcha_details(message)
                    logger.info(
                        f"Captcha URL detected: {captcha_details['image_url'].split('?')[0]}"
                    )

                    solution = self.captcha_solver.solve(
                        captcha_details["image_url"]
                    )
                    logger.info(f"Captcha solution: {solution}")
                    message_id = message.get("id")
                    self._click_pandez_buttons(solution, message_id)
                    logger.info("Captcha bypass completed successfully")
                    return

                embed = message.get("embeds", [])[0]
                if "Generating captcha image. Please wait..." in embed.get(
                    "description", ""
                ):
                    continue

                components = message.get("components", [])
                continue_custom_id = None

                for action_row in components:
                    for component in action_row.get("components", []):
                        if component.get("label") == "Continue":
                            continue_custom_id = component.get("custom_id")
                            break

                if continue_custom_id:
                    message_id = message.get("id")
                    self._click_button(
                        button_value=continue_custom_id, message_id=message_id
                    )
                else:
                    logger.info(
                        "No 'Continue' button found. Waiting for next event."
                    )

    def _click_pandez_buttons(self, solution: str, message_id: str):
        number_list = list(solution)

        for number in number_list:
            self._click_button(button_value=number, message_id=message_id)

        logger.info("All captcha digits clicked. Clicking confirm...")
        self._click_button(button_value="confirm", message_id=message_id)

    def _click_button(self, button_value: str, message_id: str) -> None:
        """Click a button by its value (i.e., 1-9 or 0)"""
        logger.info(f"Clicking button {button_value}")

        payload = {
            "type": 3,
            "nonce": Utils._generate_nonce(),
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
            "message_flags": 64,
            "message_id": message_id,
            "application_id": self.application_id,
            "session_id": self.session_id,
            "data": {
                "component_type": 2,
                "custom_id": button_value,
            },
        }
        Utils.api_request(self.session, "interactions", json=payload)
