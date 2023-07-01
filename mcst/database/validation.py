import re


def is_valid_username(username: str) -> bool:
    """
        Checks whether an username is valid, according to Minecraft's standard rules.

        This does not take into account special/rare legacy usernames.
    """

    pattern = r"^[a-zA-Z0-9_]{1,16}$"

    return bool(re.match(pattern, username))
