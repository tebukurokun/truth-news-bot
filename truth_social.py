import os
from logging import getLogger, StreamHandler, DEBUG, FileHandler

from dotenv import load_dotenv

from truthbrush.api import Api

logger = getLogger(__name__)

handler = StreamHandler()
handler.setLevel(DEBUG)
handler2 = FileHandler(filename="/proc/1/fd/1")
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.addHandler(handler2)
logger.propagate = False

load_dotenv()  # take environment variables from .env.


def compose_truth(username: str, password: str, token: str, message: str):
    """Compose Truth."""

    api = Api(
        username,
        password,
        token,
    )

    api.compose_truth(message)
