from typing     import Optional, Any, Dict
import websocket

import json
import time

from Helper      import DiscordConfig, logger

from requestcord import HeaderGenerator


class WebSocketManager:
    def __init__(self, token: str, config: DiscordConfig):
        self.token = token
        self.config = config
        self.ws: Optional[websocket.WebSocket] = None
        self.sequence: Optional[int] = None

    def connect(self) -> None:
        """Connect to Discord Gateway with exponential backoff"""
        url = f"{self.config.gateway_url}?encoding=json&v={self.config.gateway_version}"
        retry_delay = 1

        while True:
            try:
                self.ws = websocket.create_connection(url)
                self._identify()
                return
            except (websocket.WebSocketException, ConnectionError) as e:
                logger.error(f"Connection failed: {e}")
                time.sleep(retry_delay)
                retry_delay = min(retry_delay * 2, 30)

    def _identify(self) -> None:
        """Send identification payload"""
        payload = {
            "op": 2,
            "d": {
                "token": self.token,
                "capabilities": 8189,
                "properties": {
                    "os": "Windows",
                    "browser": "Chrome",
                    "device": "",
                    "system_locale": "it-IT",
                    "browser_user_agent": HeaderGenerator()._generate_ua_details()[
                        "user_agent"
                    ],
                    "browser_version": "114.0.0.0",
                    "os_version": "10",
                    "release_channel": "stable",
                },
                "presence": {
                    "status": "online",
                    "since": 0,
                    "activities": [],
                    "afk": False,
                },
            },
        }
        self.send_json(payload)

    def receive_event(self) -> Dict[str, Any]:
        """Receive and parse WebSocket event"""
        try:
            response = self.ws.recv()
            return json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse WebSocket message: {e}")
            return {}
        except websocket.WebSocketConnectionClosedException:
            logger.error("WebSocket connection closed")
            self.connect()
            return {}

    def send_json(self, payload: Dict[str, Any]) -> None:
        """Send JSON payload through WebSocket"""
        try:
            self.ws.send(json.dumps(payload))
        except websocket.WebSocketConnectionClosedException:
            logger.error("Connection closed while sending payload")
            self.connect()
            self.send_json(payload)
