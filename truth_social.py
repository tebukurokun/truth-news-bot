from truthbrush.api import Api
import json
import os
from dotenv import load_dotenv
from logging import getLogger, StreamHandler, DEBUG, FileHandler

logger = getLogger(__name__)
handler = StreamHandler()
handler.setLevel(DEBUG)
handler2 = FileHandler(filename = "/proc/1/fd/1")
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.addHandler(handler2)
logger.propagate = False

load_dotenv()  # take environment variables from .env.


# api = Api(
#     os.getenv("TRUTHSOCIAL_USERNAME"),
#     os.getenv("TRUTHSOCIAL_PASSWORD"),
#     os.getenv("TRUTHSOCIAL_TOKEN"),
# )


def compose_truth(username: str, password: str, message: str):
    """Compose Truth."""

    api = Api(
        username,
        password,
        os.getenv("TRUTHSOCIAL_TOKEN"),
    )
    logger.debug(json.dumps(api.compose_truth(message)))


if __name__ == '__main__':
    compose_truth(
        "test",
        os.getenv("TEST_TRUTHSOCIAL_USERNAME"),
        os.getenv("TEST_TRUTHSOCIAL_PASSWORD")
    )
