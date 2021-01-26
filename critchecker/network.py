""" Functions that handle network requests. """

import aiohttp


class FetchingError(Exception):
    """ A generic error occurred while fetching data. """


class BadJSONError(FetchingError):
    """ The API returned bad JSON data. """


class ConnectionTimedOutError(FetchingError):
    """ Connection timed out. """


class Session(aiohttp.ClientSession):
    """ Wrapper for aiohttp.ClientSession. Use as a context manager. """


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
        async with session.get(url, **kwargs) as response:
            response.raise_for_status()
            return await response.json()
    except aiohttp.ContentTypeError as exception:
        raise BadJSONError(exception.message) from exception
    except aiohttp.ClientResponseError as exception:
        raise FetchingError(exception.message) from exception
    except aiohttp.ServerTimeoutError as exception:
        raise ConnectionTimedOutError(exception) from exception
    except (
        aiohttp.ClientConnectionError,
        aiohttp.ClientError
    ) as exception:
        raise FetchingError(exception) from exception
