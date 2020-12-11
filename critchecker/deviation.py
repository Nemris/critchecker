""" Functions that handle DA deviations. """

import re


def extract_id(url: str) -> str:
    """
    Extract the ID from a deviation URL.

    Args:
        url: The URL to a deviation.

    Returns:
        The deviation ID.

    Raises:
        ValueError: If no deviation ID is found.
    """

    pattern = r"https://www\.deviantart\.com/[A-Za-z0-9\-]+/[a-z\-]+/.+-(\d+)$"

    try:
        return re.search(pattern, url).group(1)
    except AttributeError as exception:
        raise ValueError(f"'{url}': invalid deviation URL") from exception


def extract_category(url: str) -> str:
    """
    Extract the category from a deviation URL.

    Args:
        url: The URL to a deviation.

    Returns:
        The deviation category.

    Raises:
        ValueError: If no deviation category is found.
    """

    pattern = r"https://www\.deviantart\.com/[A-Za-z0-9\-]+/([a-z\-]+)/.+-\d+$"

    try:
        return re.search(pattern, url).group(1)
    except AttributeError as exception:
        raise ValueError(f"'{url}': invalid deviation URL") from exception
