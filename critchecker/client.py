""" Functions and classes that interface with DeviantArt. """

from __future__ import annotations

import json
import re
import types

import aiohttp
import bs4


class ClientError(Exception):
    """A generic error occurred while fetching data."""


class ResponseError(ClientError):
    """There was an error in the server's response."""


class ServerConnectionError(ClientError):
    """An error occurred while connecting to the server."""


class BadJSONError(ClientError):
    """The DeviantArt API returned invalid JSON."""


class Client:
    """A client that interfaces with DeviantArt."""

    def __init__(self) -> None:
        """Initialize an instance of Client."""
        self._session = aiohttp.ClientSession(headers={"Accept-Encoding": "gzip"})
        self._token = None

    async def __aenter__(self) -> Client:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: types.TracebackType | None,
    ) -> None:
        await self.close()

    async def _authenticate(self) -> None:
        """
        Authenticate self with DeviantArt by fetching a CSRF token.

        Raises:
            ClientError: If an error occurred while connecting to the
                server or the CSRF token couldn't be found.
        """
        # Use a 404 page to save data.
        url = "https://www.deviantart.com/_"

        # Not using self.get() because we'll receive an error 404.
        try:
            async with self._session.get(url) as resp:
                data = await resp.text()
        except ClientError as exc:
            # Authentication cannot proceed.
            raise exc

        try:
            self._token = extract_token(data)
        except ValueError as exc:
            raise ClientError(f"{url!r}: token not found") from exc

    @classmethod
    async def new(cls) -> Client:
        """
        Create a new authenticated Client.

        This method performs a network request.

        Returns:
            A new Client authenticated with DeviantArt.
        """
        client = cls()
        await client._authenticate()
        return client

    async def close(self) -> None:
        """Close the instance's underlying session."""
        await self._session.close()

    async def get(self, url: str, **kwargs) -> str:
        """
        Perform a GET request to url.

        Args:
            url: The URL to request.
            **kwargs: Optional keyword arguments to pass to
                aiohttp.ClientSession.get().

        Returns:
            The decoded server response payload.

        Raises:
            ClientResponseError: If there was an error in the server's
                response.
            ServerConnectionError: If an error occurred while
                connecting to the server.
        """
        try:
            async with self._session.get(url, **kwargs) as resp:
                resp.raise_for_status()
                return await resp.text()
        except aiohttp.ClientResponseError as exc:
            raise ResponseError(
                f"{exc.request_info.url}: {exc.status} {exc.message}"
            ) from exc
        except aiohttp.ClientConnectionError as exc:
            raise ServerConnectionError(exc) from exc

    async def query_api(self, url: str, params: dict) -> dict:
        """
        Query the DeviantArt API endpoint at url.

        Args:
            url: The URL of the API endpoont to query.
            params: Parameters to pass to the API via GET.

        Returns:
            The API's JSON response.

        Raises:
            ClientResponseError: If there was an error in the server's
                response.
            ServerConnectionError: If an error occurred while
                connecting to the server.
            BadJSONError: If the server returned malformed JSON data.
        """
        params["csrf_token"] = self._token
        try:
            return json.loads(await self.get(url, params=params))
        except json.decoder.JSONDecodeError as exc:
            raise BadJSONError("malformed JSON response") from exc


def extract_token(html: str) -> str:
    """
    Extract a CSRF token from HTML data.

    Args:
        html: The HTML data to parse.

    Returns:
        The token contained within the HTML data.

    Raises:
        ValueError: If no token can be found.
    """
    pattern = re.compile(r"\"csrf\":\"(.+?)\"")
    soup = bs4.BeautifulSoup(html, features="html.parser")

    try:
        return pattern.search(soup.find("script", string=pattern).text).group(1)
    except AttributeError as exc:
        raise ValueError("CSRF token not found") from exc
