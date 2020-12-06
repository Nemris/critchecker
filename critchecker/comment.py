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
        type_id: The parent deviation"s type ID.
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
