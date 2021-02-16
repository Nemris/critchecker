""" Functions that handle DA deviations. """

import dataclasses
import re


class DeviationError(Exception):
    """ Common base class for exceptions related to deviations. """


class BadDeviationError(DeviationError):
    """ The API returned malformed deviation data. """


@dataclasses.dataclass
class Deviation():
    """
    A deviation.

    Args:
        deviation: The dict representation of a deviation, as returned
            by the DA Eclipse API.
        author: The deviation author's username.
    """

    deviation: dataclasses.InitVar[dict]
    author: str = None

    def __post_init__(self, deviation: dict) -> None:
        """
        Initialize the instance attributes by parsing deviation.

        Args:
            deviation: The dict representation of a deviation, as
                returned by the DA Eclipse API.

        Raises:
            BadDeviationError: If a required key is missing from
                deviation.
        """

        try:
            self.author = deviation["author"]["username"]
        except KeyError as exception:
            raise BadDeviationError("bad deviation data") from exception


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
        "journal": 1
    }

    return type_ids.get(category, 0)
