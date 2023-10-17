""" Functions and dataclasses that handle DA comments. """

import dataclasses
import json
import re

import bs4

from critchecker import client


class CommentError(Exception):
    """ Common base class for exceptions related to comments. """


class NoSuchCommentError(CommentError):
    """ The requested comment does not exist. """


class CommentPageFetchingError(CommentError):
    """ An error occurred while fetching comment page data. """


class BadCommentError(CommentError):
    """ The API returned malformed comment data. """


class BadCommentPageError(CommentError):
    """ The API returned malformed comment page data. """


@dataclasses.dataclass
class Comment():  # pylint: disable=too-many-instance-attributes
    """
    A single comment in a thread.

    Args:
        comment: The dict representation of a comment, as returned by
            the DA Eclipse API.
        url: The comment's URL.
        parent_id: The parent comment's ID, if any.
        posted_at: The comment's timestamp.
        edited_at: The comment's edited time, if any.
        author: The comment author's username.
        body: The comment's body.
    """

    comment: dataclasses.InitVar[dict]
    url: str = None
    parent_id: int = None
    posted_at: str = None
    edited_at: str = None
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
            BadCommentError: If a required key is missing from comment.
        """

        # "Draft" comments have a word count ready, "writer" comments
        # must be parsed.

        try:
            self.url = assemble_url(
                comment["itemId"],
                comment["typeId"],
                comment["commentId"]
            )

            self.parent_id = comment["parentId"]
            self.posted_at = comment["posted"]
            self.edited_at = comment["edited"]
            self.author = comment["user"]["username"]

            structure = comment["textContent"]["html"]

            if structure["type"] == "writer":
                html = structure["markup"]

                self.body = markup_to_text(html)
                self.words = count_words(self.body)
            elif structure["type"] == "draft":
                blocks = json.loads(structure["markup"])["blocks"]
                self.body = "\n".join([block["text"] for block in blocks])

                features = json.loads(structure["features"])
                for feature in features:
                    if feature["type"] == "WORD_COUNT_FEATURE":
                        self.words = feature["data"]["words"]
        except KeyError as exc:
            raise BadCommentError("malformed comment data") from exc


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
            BadCommentPageError: If a required key is missing from
                comment or instantiating a Comment fails.
        """

        try:
            self.has_more = commentpage["hasMore"]
            self.next_offset = commentpage["nextOffset"]
            self.comments = [Comment(comment) for comment in commentpage["thread"]]
        except (KeyError, BadCommentError) as exc:
            raise BadCommentPageError("malformed comment page data") from exc


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
    deviation_id: int,
    type_id: int,
    depth: int,
    offset: int,
    da_client: client.Client
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
        "limit": 50
    }

    try:
        commentpage = await da_client.query_api(api_url, params)
    except client.ClientError as exc:
        raise CommentPageFetchingError(exc) from exc

    return CommentPage(commentpage)


async def fetch_pages(
    deviation_id: int,
    type_id: int,
    depth: int,
    da_client: client.Client
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
    Extract all the comment URLs in a comment, without duplicates..

    Args:
        comment: The comment to extract comment URLs from.

    Returns:
        The extracted and deduplicated comment URLs.
    """

    pattern = r"https://www\.deviantart\.com/comments/\d+/\d+/\d+"

    return list(dict.fromkeys(re.findall(pattern, comment)))


def markup_to_text(markup: str) -> str:
    """
    Remove all the HTML tags in a comment and replace \"<br>\" tags
    with newlines.

    Args:
        markup: The comment to clean, as HTML data.

    Returns:
        The comment stripped of HTML tags and with \"<br>\" tags
            replaced with newlines.
    """

    soup = bs4.BeautifulSoup(markup, features="html.parser")

    for tag in soup.find_all("br"):
        tag.replace_with("\n")

    return soup.get_text()


def count_words(comment: str) -> int:
    """
    Count how many words there are in a comment.

    Args:
        comment: The comment whose length to check.

    Returns:
        The number of words in the comment.
    """

    return len(comment.split())
