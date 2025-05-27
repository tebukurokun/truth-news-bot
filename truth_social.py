import os
from logging import getLogger, StreamHandler, DEBUG, FileHandler, Formatter

from dotenv import load_dotenv

from truthbrush.api import Api

logger = getLogger(__name__)

formatter = Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

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


if __name__ == '__main__':
    compose_truth(
        "test",
        os.getenv("TEST_TRUTHSOCIAL_USERNAME"),
        os.getenv("TEST_TRUTHSOCIAL_PASSWORD"),
        "test"
    )
