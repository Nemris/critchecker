""" Functions and dataclasses that handle DA comments. """

import collections
import dataclasses
import re

import bs4
import requests


class FetchingError(Exception):
    """ A network or HTTP error occurred while fetching data. """


@dataclasses.dataclass
class Comment():  # pylint: disable=too-many-instance-attributes
    """
    A single comment in a thread.

    Args:
        comment: The dict representation of a comment, as returned by
            the DA Eclipse API.
        id: The comment ID.
        parent_id: The parent comment's ID, if any.
        type_id: The parent deviation's type ID.
        belongs_to: The parent deviation's ID.
        posted_at: The comment's timestamp.
        author_id: The comment author's user ID.
        author: The comment author's username.
        body: The comment's body.
    """

    comment: dataclasses.InitVar[dict]
    id: int = None  # pylint: disable=invalid-name
    parent_id: int = None
    type_id: int = None
    belongs_to: int = None
    posted_at: str = None
    author_id: int = None
    author: str = None
    body: str = None

    def __post_init__(self, comment: dict) -> None:
        """
        Initialize the instance attributes by parsing comment.

        Args:
            comment: The dict representation of a comment, as returned
                by the DA Eclipse API.

        Raises:
            ValueError: If a required key is missing from comment.
        """

        try:
            self.id = comment["commentId"]
            self.parent_id = comment["parentId"]
            self.type_id = comment["typeId"]
            self.belongs_to = comment["itemId"]
            self.posted_at = comment["posted"]
            self.author_id = comment["user"]["userId"]
            self.author = comment["user"]["username"]
            self.body = comment["textContent"]["html"]["markup"]
        except KeyError as exception:
            raise ValueError("malformed comment data") from exception


@dataclasses.dataclass
class CommentPage():
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

    def __post_init__(self, commentpage: dict) -> None:
        """
        Initialize the instance attributes by parsing commentpage.

        Args:
            commentpage: The dict representation of a comment page, as
                returned by the DA Eclipse API.

        Raises:
            ValueError: If a required key is missing from comment or
                instantiating a Comment fails.
        """

        try:
            self.has_more = commentpage["hasMore"]
            self.next_offset = commentpage["nextOffset"]
            self.comments = [Comment(comment) for comment in commentpage["thread"]]
        except (KeyError, ValueError) as exception:
            raise ValueError("malformed comment page data") from exception


def assemble_url(deviation_id: int, type_id: int, comment_id: int) -> str:
    """
    Assemble the URL to a comment.

    Args:
        deviation_id: The parent deviation's ID.
        type_id: The parent deviation's type ID.
        comment_id: The comment ID.

    Returns:
        The URL to the comment.
    """

    base_url = "https://www.deviantart.com"
    relative_url = "/".join([
        "comments",
        str(type_id),
        str(deviation_id),
        str(comment_id)
    ])

    return "/".join([base_url, relative_url])


def fetch_page(deviation_id: int, type_id: int, depth: int, offset: int) -> CommentPage:
    """
    Fetch a page of comments to a deviation.

    Args:
        deviation_id: The parent deviation's ID.
        type_id: The parent deviation's type ID.
        depth: The amount of replies to a comment. A depth of zero
            returns only the topmost comment.
        offset: The comment offset from where to fetch comments in
            blocks of 10 per page.

    Returns:
        A page of comments.

    Raises:
        FetchingError: If an error occurs while fetching the comment
            page data.
        ValueError: If DA returns invalid comment page data.
    """

    api_url = "https://www.deviantart.com/_napi/shared_api/comments/thread"
    params = {
        "typeid": type_id,
        "itemid": deviation_id,
        "maxdepth": depth,
        "offset": offset
    }

    try:
        response = requests.get(api_url, params=params, timeout=5)
        response.raise_for_status()
    except requests.exceptions.HTTPError as exception:
        raise FetchingError(f"HTTP error: '{exception}'") from exception
    except requests.exceptions.ConnectionError as exception:
        raise FetchingError(f"connection error: '{exception}'") from exception
    except requests.exceptions.Timeout as exception:
        raise FetchingError(f"connection timed out: '{exception}'") from exception
    except requests.exceptions.RequestException as exception:
        raise FetchingError(f"unknown error: '{exception}'") from exception

    return CommentPage(response.json())


def yield_all(deviation_id: int, type_id: int, depth: int) -> collections.abc.Iterator[Comment]:
    """
    Fetch all the comments to a deviation and yield them one by one.

    Args:
        deviation_id: The parent deviation's ID.
        type_id: The parent deviation's type ID.
        depth: The amount of replies to a comment. A depth of zero
            returns only the topmost comment.

    Yields:
        The next comment.

    Raises:
        ValueError: If an error happens while fetching or parsing
            comment page data.
    """

    offset = 0

    while True:
        try:
            commentpage = fetch_page(deviation_id, type_id, depth, offset)
        except (FetchingError, ValueError) as exception:
            raise ValueError(exception) from exception

        yield from commentpage.comments

        if not commentpage.has_more:
            break

        offset = commentpage.next_offset


def is_valid(url: str) -> bool:
    """
    Check if the URL is a valid comment URL.

    Args:
        url: The URL to check.

    Returns:
        True if the URL is a valid comment URL, False otherwise.
    """

    pattern = r"https://www\.deviantart\.com/comments/\d+/\d+/\d+"

    return bool(re.match(pattern, url))


def yield_links(comment: str) -> collections.abc.Iterator[str]:
    """
    Yield all the links in a comment, one by one.

    Args:
        comment: The comment to extract links from.

    Yields:
        The next link.
    """

    html = bs4.BeautifulSoup(comment, features="html.parser")

    yield from (tag.get("href") for tag in html.findAll("a"))
