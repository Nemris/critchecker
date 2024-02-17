""" Functions and dataclasses that handle DA comments. """

from __future__ import annotations

import dataclasses
from datetime import datetime
import json
import re

from critchecker.client import Client, ClientError


COMMENT_URL_PATTERN = re.compile(
    r"https://www\.deviantart\.com/comments/(\d+)/(\d+)/(\d+)"
)


class CommentError(Exception):
    """Common base class for exceptions related to comments."""


class CommentPageFetchingError(CommentError):
    """An error occurred while fetching comment page data."""


class InvalidCommentTypeError(CommentError):
    """The comment's type is not supported."""


class BadCommentError(CommentError):
    """The API returned malformed comment data."""


class BadCommentPageError(CommentError):
    """The API returned malformed comment page data."""


@dataclasses.dataclass(frozen=True)
class URL:
    """
    A URL to a comment.

    Args:
        deviation_id: The parent deviation's ID.
        deviation_type: The parent deviation's type ID.
        comment_id: The comment's ID.
    """

    deviation_id: str
    deviation_type: str
    comment_id: str

    def __str__(self) -> str:
        return "/".join(
            [
                "https://www.deviantart.com/comments",
                self.deviation_type,
                self.deviation_id,
                self.comment_id,
            ]
        )

    @classmethod
    def from_str(cls, string: str) -> URL:
        """
        Build a URL from a string representation of a comment URL.

        Args:
            string: The string representation of a comment URL.

        Returns:
            An instance of URL pointing to a comment.

        Raises:
            ValueError: If the string isn't a valid comment URL.
        """
        try:
            deviation_type, deviation_id, comment_id = COMMENT_URL_PATTERN.match(
                string
            ).groups()
        except AttributeError as exc:
            raise ValueError(f"{string!r}: invalid comment URL") from exc
        return cls(deviation_id, deviation_type, comment_id)


@dataclasses.dataclass
class Comment:
    """
    A comment in a thread.

    Args:
        data: The JSON representation of a comment.
        url: The URL to the comment.
        timestamp: The date and time the comment was posted.
        author: The comment's author.
        body: The comment's body.
        words: The comment's length in words.
    """

    data: dataclasses.InitVar[dict]
    url: URL = None
    timestamp: datetime = None
    author: str = None
    body: str = None
    words: int = None

    @staticmethod
    def _assemble_body(data: dict) -> str:
        """
        Assemble the body of a comment from JSON data.

        Args:
            data: The JSON representation of a comment.

        Returns:
            The comment's body.

        Raises:
            KeyError: If the JSON data is invalid.
        """
        blocks = json.loads(data["textContent"]["html"]["markup"])["blocks"]
        return "\n".join([block["text"] for block in blocks])

    @staticmethod
    def _get_length(data: dict) -> int:
        """
        Retrieve a comment's length in words.

        Args:
            data: The JSON representation of a comment.

        Returns:
            The comment's length in words.

        Raises:
            KeyError: If the JSON data is invalid.
        """
        features = json.loads(data["textContent"]["html"]["features"])
        return next(
            feat["data"]["words"]
            for feat in features
            if feat["type"] == "WORD_COUNT_FEATURE"
        )

    def __post_init__(self, data: dict) -> None:
        """
        Initialize self from JSON data.

        Args:
            data: Representation of a comment and related metadata,
                returned by the Eclipse API.

        Raises:
            InvalidCommentTypeError: If the comment type is not supported.
            BadCommentError: If the JSON data is invalid.
        """
        if (kind := data["textContent"]["html"]["type"]) != "draft":
            raise InvalidCommentTypeError(f"{kind!r}: invalid comment type")

        try:
            self.url = URL(
                str(data["itemId"]), str(data["typeId"]), str(data["commentId"])
            )
            self.timestamp = datetime.fromisoformat(data["posted"])
            self.author = data["user"]["username"]
            self.body = self._assemble_body(data)
            self.words = self._get_length(data)
        except (KeyError, ValueError) as exc:
            raise BadCommentError("invalid comment data") from exc

    def get_unique_comment_urls(self) -> list[URL]:
        """
        Extract the unique comment URLs contained in this comment.

        Returns:
            The unique comment URLs.
        """
        return [
            URL(ids[1], ids[0], ids[2])
            for ids in set(COMMENT_URL_PATTERN.findall(self.body))
        ]


@dataclasses.dataclass
class CommentPage:
    """
    A page of comments.

    Args:
        page: The dict representation of a comment page, as
            returned by the DA Eclipse API.
        has_more: Whether a following comment page exists.
        next_offset: The offset of the next comment page, if any.
        comments: The comments contained in the page.
    """

    page: dataclasses.InitVar[dict]
    has_more: bool = None
    next_offset: int = None
    comments: list[Comment] = None

    @staticmethod
    def _get_comments(thread: dict) -> list[Comment]:
        """
        Obtain all comments of type Draft in a thread.

        Args:
            thread: Thread of comments in a page.

        Returns:
            The Draft comments in the thread.

        Raises:
            BadCommentPageError: If any comment is malformed.
        """
        comments = []
        for comment in thread:
            try:
                comments.append(Comment(comment))
            except InvalidCommentTypeError:
                # We only expect Draft comments, skip this comment.
                pass
            except BadCommentError as exc:
                raise BadCommentPageError("malformed comment page data") from exc

        return comments

    def __post_init__(self, page: dict) -> None:
        """
        Initialize the instance attributes by parsing page.

        Args:
            page: The dict representation of a comment page, as
                returned by the DA Eclipse API.

        Raises:
            BadCommentPageError: If a required key is missing from
                comment or instantiating a Comment fails.
        """
        try:
            self.has_more = page["hasMore"]
            self.next_offset = page["nextOffset"]
            thread = page["thread"]
        except KeyError as exc:
            raise BadCommentPageError("malformed comment page data") from exc

        self.comments = self._get_comments(thread)


async def fetch_page(
    deviation_id: int, type_id: int, depth: int, offset: int, client: Client
) -> CommentPage:
    """
    Asynchronously fetch a page of comments to a deviation.

    The comments are ordered from newest to oldest, and a page's
    maximum size is 50 comments.

    Args:
        deviation_id: The parent deviation's ID.
        type_id: The parent deviation's type ID.
        depth: The amount of allowed replies to a comment. A depth of
            zero returns only the topmost comments.
        offset: The starting offset of the comment page.
        client: A client that interfaces with DeviantArt.

    Returns:
        A page of comments.

    Raises:
        BadCommentPageError: If instantiating the CommentPage fails.
        CommentPageFetchingError: If an error occurs while fetching
            comment page data.
    """
    api_url = "https://www.deviantart.com/_napi/shared_api/comments/thread"
    params = {
        "itemid": deviation_id,
        "typeid": type_id,
        "order": "newest",
        "maxdepth": depth,
        "offset": offset,
        "limit": 50,
    }

    try:
        page = await client.query_api(api_url, params)
    except ClientError as exc:
        raise CommentPageFetchingError(exc) from exc

    return CommentPage(page)


async def fetch_pages(
    deviation_id: int, type_id: int, depth: int, client: Client
) -> CommentPage:
    """
    Asynchronously fetch all the pages of comments to a deviation.

    Unfortunately, fetching a comment page depends on knowing the next
    offset, so there's currently no way to fetch more pages in
    parallel.

    Args:
        deviation_id: The parent deviation's ID.
        type_id: The parent deviation's type ID.
        depth: The amount of allowed replies to a comment. A depth of
            zero returns only the topmost comments.
        client: A client that interfaces with DeviantArt.

    Yields:
        The next comment page.

    Raises:
        BadCommentPageError: If instantiating the CommentPage fails.
        CommentPageFetchingError: If an error occurs while fetching
            comment page data.
    """
    offset = 0
    while page := await fetch_page(deviation_id, type_id, depth, offset, client):
        yield page

        if not page.has_more:
            break
        offset = page.next_offset
