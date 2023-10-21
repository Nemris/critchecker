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
    except AttributeError as exc:
        raise ValueError(f"'{url}': invalid deviation URL") from exc


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
    except AttributeError as exc:
        raise ValueError(f"'{url}': invalid deviation URL") from exc


def typeid_of(category: str) -> int:
    """
    Return a type ID matching the deviation category, or zero.

    Args:
        category: The deviation category.

    Returns:
        The type ID matching a deviation category, or zero.
    """

    # Currently implementing art and journals only.
    type_ids = {
        "art": 1,
        "journal": 1,
    }

    return type_ids.get(category, 0)
