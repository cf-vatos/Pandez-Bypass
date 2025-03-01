from abc        import ABC, abstractmethod
from io         import  BytesIO

import base64
import time
import json

from PIL        import Image

import requests
from colorama   import Fore

from Helper     import logger

class CaptchaSolver(ABC):
    @abstractmethod
    def solve(self, image_url: str) -> str:
        pass

config = json.load(open("config.json"))

class TwoCaptchaSolver(CaptchaSolver):
    def __init__(self, api_key: str = config["api_key"]):
        self.api_key = api_key
        self.base_url = "https://api.2captcha.com"

    def _encode_image(self, image_url: str) -> str:
        response = requests.get(image_url)
        response.raise_for_status()
        
        with Image.open(BytesIO(response.content)) as img:
            with BytesIO() as buffer:
                img.save(buffer, format="PNG")
                return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def _create_task(self, base64_image: str) -> str:
        payload = {
            "clientKey": self.api_key,
            "task": {
                "type": "ImageToTextTask",
                "body": base64_image,
                "minLength": 1,
                "maxLength": 6,
                "comment": "Enter the numbers above."
            }
        }
        response = requests.post(f"{self.base_url}/createTask", json=payload)
        response.raise_for_status()
        return response.json()["taskId"]

    def solve(self, image_url: str) -> str:
        start_time = time.time()
        base64_image = self._encode_image(image_url)
        task_id = self._create_task(base64_image)

        while True:
            time.sleep(1)
            result = requests.post(
                f"{self.base_url}/getTaskResult",
                json={"clientKey": self.api_key, "taskId": task_id}
            ).json()
            
            if result["status"] == "ready":
                end_time = time.time()
                logger.info(f"Captcha Solved in {Fore.RESET}{end_time - start_time:.2f}s")
                return result["solution"]["text"]
            if result["status"] != "processing":
                raise ValueError("CAPTCHA solving failed")

