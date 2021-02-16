""" Functions that handle DA deviations. """

import dataclasses
import re

from critchecker import network


class DeviationError(Exception):
    """ Common base class for exceptions related to deviations. """


class DeviationFetchingError(DeviationError):
    """ An error occurred while fetching deviation data. """


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


async def fetch_metadata(deviation_id: int, session: network.Session) -> Deviation:
    """
    Asynchronously fetch a deviation's metadata.

    Args:
        deviation_id: The deviation's ID.
        session: A session to use for requesting data.

    Returns:
        The deviation's metadata.

    Raises:
        BadDeviationError: If instantiating the Deviation fails.
        DeviationFetchingError: If an error happens while fetching
            deviation data.
    """

    api_url = "https://www.deviantart.com/_napi/shared_api/deviation/fetch"

    # We support only art here. Curiously, the API considers journals
    # a subset of art, possibly because they share the type ID.
    params = {
        "deviationid": deviation_id,
        "type": "art"
    }

    try:
        deviation = await network.fetch_json(api_url, session, params=params)
    except network.FetchingError as exception:
        raise DeviationFetchingError(exception) from exception

    return Deviation(deviation)
