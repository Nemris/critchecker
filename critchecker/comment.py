""" Functions and dataclasses that handle DA comments. """

import dataclasses
import json
import re

from critchecker import client


class CommentError(Exception):
    """Common base class for exceptions related to comments."""


class NoSuchCommentError(CommentError):
    """The requested comment does not exist."""


class CommentPageFetchingError(CommentError):
    """An error occurred while fetching comment page data."""


class InvalidCommentTypeError(CommentError):
    """The comment's type is not supported."""


class BadCommentError(CommentError):
    """The API returned malformed comment data."""


class BadCommentPageError(CommentError):
    """The API returned malformed comment page data."""


@dataclasses.dataclass
class Comment:
    """
    A comment in a thread.

    Args:
        data: The JSON representation of a comment.
        url: The URL to the comment.
        posted_at: The datetime the comment was posted at.
        edited_at: The datetime the comment was edited at, if any.
        author: The comment's author.
        body: The comment's body.
        words: The comment's length in words.
    """

    data: dataclasses.InitVar[dict]
    url: str = None
    posted_at: str = None
    edited_at: str | None = None
    author: str = None
    body: str = None
    words: int = None

    @staticmethod
    def _assemble_url(deviation_id: int, type_id: int, comment_id: int) -> str:
        """
        Assemble the URL to a comment.

        Args:
            deviation_id: The parent deviation's ID.
            type_id: The parent deviation's type ID.
            comment_id: The comment ID.

        Returns:
            The URL to the comment.
        """
        return "/".join(
            [
                "https://www.deviantart.com/comments",
                str(type_id),
                str(deviation_id),
                str(comment_id),
            ]
        )

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
        kind = data["textContent"]["html"]["type"]
        if kind != "draft":
            raise InvalidCommentTypeError(f"{kind!r}: invalid comment type")

        try:
            self.url = self._assemble_url(
                data["itemId"], data["typeId"], data["commentId"]
            )
            self.posted_at = data["posted"]
            self.edited_at = data["edited"]
            self.author = data["user"]["username"]
            self.body = self._assemble_body(data)
            self.words = self._get_length(data)
        except KeyError as exc:
            raise BadCommentError("invalid comment data") from exc


@dataclasses.dataclass
class CommentPage:
    """
    A page of comments.

    Args:
        commentpage: The dict representation of a comment page, as
            returned by the DA Eclipse API.
        has_more: Whether a following comment page exists.
        next_offset: The offset of the next comment page, if any.
        comments: The comments contained in the page.
    """

    commentpage: dataclasses.InitVar[dict]
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

    def __post_init__(self, commentpage: dict) -> None:
        """
        Initialize the instance attributes by parsing commentpage.

        Args:
            commentpage: The dict representation of a comment page, as
                returned by the DA Eclipse API.

        Raises:
            BadCommentPageError: If a required key is missing from
                comment or instantiating a Comment fails.
        """
        try:
            self.has_more = commentpage["hasMore"]
            self.next_offset = commentpage["nextOffset"]
            thread = commentpage["thread"]
        except KeyError as exc:
            raise BadCommentPageError("malformed comment page data") from exc

        self.comments = self._get_comments(thread)


def extract_ids_from_url(url: str) -> tuple[int, int, int]:
    """
    Obtain the IDs from a comment URL.

    Args:
        url: The URL to a comment.

    Returns:
        A tuple of the extracted type ID, deviation ID and comment ID
            as ints, in order.

    Raises:
        ValueError: If the comment URL is invalid.
    """
    try:
        return tuple(int(num) for num in url.split("/")[-3:])
    except (IndexError, ValueError) as exc:
        raise ValueError(f"'{url}': invalid comment URL") from exc


async def fetch_page(
    deviation_id: int, type_id: int, depth: int, offset: int, da_client: client.Client
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
        da_client: A client that interfaces with DeviantArt.

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
        commentpage = await da_client.query_api(api_url, params)
    except client.ClientError as exc:
        raise CommentPageFetchingError(exc) from exc

    return CommentPage(commentpage)


async def fetch_pages(
    deviation_id: int, type_id: int, depth: int, da_client: client.Client
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
        da_client: A client that interfaces with DeviantArt.

    Yields:
        The next comment page.

    Raises:
        BadCommentPageError: If instantiating the CommentPage fails.
        CommentPageFetchingError: If an error occurs while fetching
            comment page data.
    """
    offset = 0
    while True:
        # Let exceptions bubble up.
        commentpage = await fetch_page(deviation_id, type_id, depth, offset, da_client)

        yield commentpage

        if not commentpage.has_more:
            break

        offset = commentpage.next_offset


async def fetch(url: str, da_client: client.Client) -> Comment:
    """
    Asynchronously fetch a single comment to a deviation.

    Args:
        url: The URL to a comment.
        da_client: A client that interfaces with DeviantArt.

    Returns:
        A single comment.

    Raises:
        BadCommentPageError: If instantiating the CommentPage fails.
        NoSuchCommentError: If the requested comment is not found.
    """
    type_id, deviation_id, _ = extract_ids_from_url(url)

    # Let exceptions bubble up.
    depth = 0
    async for commentpage in fetch_pages(deviation_id, type_id, depth, da_client):
        for comment in commentpage.comments:
            if comment.url == url:
                return comment

    # Reaching this point means no matching comment was found.
    raise NoSuchCommentError(f"'{url}': comment not found")


def is_url_valid(url: str) -> bool:
    """
    Check if the URL is a valid comment URL.

    Args:
        url: The URL to check.

    Returns:
        True if the URL is a valid comment URL, False otherwise.
    """
    pattern = r"https://www\.deviantart\.com/comments/\d+/\d+/\d+"

    return bool(re.match(pattern, url))


def extract_comment_urls(comment: str) -> list[str]:
    """
    Extract all the comment URLs in a comment, without duplicates.

    Args:
        comment: The comment to extract comment URLs from.

    Returns:
        The extracted and deduplicated comment URLs.
    """
    pattern = r"https://www\.deviantart\.com/comments/\d+/\d+/\d+"

    return list(dict.fromkeys(re.findall(pattern, comment)))
