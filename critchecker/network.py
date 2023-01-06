""" Functions that handle network requests. """

import asyncio
import json
import re

import aiohttp
import bs4


DEFAULT_HEADERS = {
    "Accept-Encoding": "gzip"
}


class FetchingError(Exception):
    """ A generic error occurred while fetching data. """


class BadJSONError(FetchingError):
    """ The API returned bad JSON data. """


class ConnectionTimedOutError(FetchingError):
    """ Connection timed out. """


# Aliasing to avoid importing aiohttp in other modules to get sessions.
Session = aiohttp.ClientSession


def prepare_session(headers: dict | None = None) -> Session:
    """
    Prepare a Session with certain headers.

    Args:
        headers: Headers to add to the session.

    Returns:
        A Session with the specified headers.
    """
    if headers is None:
        headers = DEFAULT_HEADERS

    return Session(headers=headers)


async def fetch(url: str, session: Session, **kwargs: dict) -> dict:
    """
    Asynchronously download and return the data found at the URL.

    Args:
        url: The URL to download data from.
        session: A session to use for requesting data.
        **kwargs: Optional keyword arguments to pass to session.get().

    Returns:
        The response body.

    Raises:
        ConnectionTimedOutError: If the connection times out.
        FetchingError: If a generic network error occurs.
    """

    try:
        async with session.get(url, **kwargs) as response:
            response.raise_for_status()
            return await response.text()
    except aiohttp.ClientResponseError as exception:
        raise FetchingError(exception.message) from exception
    except aiohttp.ServerTimeoutError as exception:
        raise ConnectionTimedOutError(exception) from exception
    except (
        aiohttp.ClientConnectionError,
        aiohttp.ClientError
    ) as exception:
        raise FetchingError(exception) from exception
    except asyncio.TimeoutError as exception:
        raise ConnectionTimedOutError(exception) from exception


def extract_csrf_token(markup: str) -> str:
    """
    Find and extract a CSRF token from HTML data.

    Args:
        markup: The HTML data to inspect.

    Returns:
        The CSRF token.

    Raises:
        ValueError: If no token is found.
    """

    pattern = re.compile(r"\s+window\.__CSRF_TOKEN__ = '(.+)';")

    soup = bs4.BeautifulSoup(markup, features="html.parser")
    tag = soup.find("script", string=pattern)

    try:
        return re.search(pattern, tag.string).group(1)
    except AttributeError as exception:
        raise ValueError("no CSRF token found") from exception


async def fetch_csrf_token(session: Session) -> str:
    """
    Asynchronously fetch and return the CSRF token for a session.

    Args:
        session: A session to use for requesting data.

    Returns:
        A CSRF token usable by the current session.

    Raises:
        ConnectionTimedOutError: If the connection times out.
        FetchingError: If a generic network error occurs.
    """

    url = "https://www.deviantart.com"

    return extract_csrf_token(await fetch(url, session))


async def fetch_json(url: str, session: Session, **kwargs: dict) -> dict:
    """
    Asynchronously download and return the JSON data found at the URL.

    Args:
        url: The URL to download data from.
        session: A session to use for requesting data.
        **kwargs: Optional keyword arguments to pass to session.get().

    Returns:
        The response body.

    Raises:
        BadJSONError: If the server replies with invalid JSON data.
        ConnectionTimedOutError: If the connection times out.
        FetchingError: If a generic network error occurs.
    """

    try:
        return json.loads(
            await fetch(url, session, **kwargs)
        )
    except json.JSONDecodeError as exception:
        raise BadJSONError("malformed JSON response") from exception
