""" Functions and dataclasses that handle DA comments. """

import dataclasses


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
