import logging
from dataclasses import dataclass

from colorama import Fore

@dataclass
class DiscordConfig:
    api_version: str = "v9"
    gateway_version: int = 9
    base_url: str = "https://discord.com/api/"
    gateway_url: str = "wss://gateway.discord.gg/"

logging.basicConfig(
    level=logging.INFO,
    format=f"{Fore.CYAN}%(asctime)s {Fore.LIGHTBLACK_EX}%(levelname)s: {Fore.RESET}%(message)s",
    handlers=[
        logging.FileHandler("bypass.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)
