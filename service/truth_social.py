from dotenv import load_dotenv

from truthbrush.api import Api

load_dotenv()  # take environment variables from .env.


def compose_truth(username: str, password: str, token: str, message: str):
    """Compose Truth."""

    api = Api(
        username,
        password,
        token,
    )

    api.compose_truth(message)
