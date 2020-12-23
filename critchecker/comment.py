""" Functions and dataclasses that handle DA comments. """

import collections
import dataclasses
import json
import re
import typing

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
        edited_at: The comment's edited time, if any.
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
    edited_at: str = None
    author_id: int = None
    author: str = None
    body: str = None
    words: int = None

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
            self.edited_at = comment["edited"]
            self.author_id = comment["user"]["userId"]
            self.author = comment["user"]["username"]

            structure = comment["textContent"]["html"]

            blocks = json.loads(structure["markup"])["blocks"]
            self.body = "\n".join([block["text"] for block in blocks])

            features = json.loads(structure["features"])
            for feature in features:
                if feature["type"] == "WORD_COUNT_FEATURE":
                    self.words = feature["data"]["words"]
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


def extract_ids_from_url(url: str) -> dict[int, int, int]:
    """
    Obtain the IDs from a comment URL.

    Args:
        url: The URL to a comment.

    Returns:
        The extracted type ID, deviation ID and comment ID as ints.

    Raises:
        ValueError: If the comment URL is invalid.
    """

    split_url = url.split("/")

    try:
        return {
            "type_id": int(split_url[-3]),
            "deviation_id": int(split_url[-2]),
            "comment_id": int(split_url[-1])
        }
    except (IndexError, ValueError) as exception:
        raise ValueError(f"'{url}': invalid comment URL") from exception


def fetch(deviation_id: int, type_id: int, comment_id: int) -> typing.Optional[Comment]:
    """
    Fetch a single comment to a deviation.

    Args:
        deviation_id: The parent deviation's ID.
        type_id: The parent deviation's type ID.
        comment_id: The comment ID.

    Returns:
        A single comment or None.

    Raises:
        FetchingError: If an error occurs while fetching the comment
            data.
        ValueError: If DA returns invalid comment data.
    """

    # TODO: Once PEP-604 is implemented, use the new union syntax.

    # pylint: disable=unsubscriptable-object
    # See https://github.com/PyCQA/pylint/issues/3882.

    depth = 0
    for comment in yield_all(deviation_id, type_id, depth):
        if comment.id == comment_id:
            return comment

    return None


def fetch_page(deviation_id: int, type_id: int, depth: int, offset: int) -> CommentPage:
    """
    Fetch a page of comments to a deviation, newest comments first.

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

    # Assume we're most interested in newest comments.
    params = {
        "typeid": type_id,
        "itemid": deviation_id,
        "maxdepth": depth,
        "offset": offset,
        "order": "newest",
        "limit": 50
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
        FetchingError: If an error occurs while fetching the comment
            page data.
        ValueError: If DA returns invalid comment page data.
    """

    offset = 0

    while True:
        commentpage = fetch_page(deviation_id, type_id, depth, offset)

        yield from commentpage.comments

        if not commentpage.has_more:
            break

        offset = commentpage.next_offset


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


def extract_comment_urls(comment: str) -> set[str]:
    """
    Extract all the comment URLs in a comment, without duplicates..

    Args:
        comment: The comment to extract comment URLs from.

    Returns:
        The extracted and deduplicated comment URLs.
    """

    pattern = r"https://www\.deviantart\.com/comments/\d+/\d+/\d+"

    return set(re.findall(pattern, comment))
