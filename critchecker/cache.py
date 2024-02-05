""" Facilities that handle a cache of comments. """

from __future__ import annotations

from collections.abc import Iterable
import dataclasses

from critchecker.comment import Comment
from critchecker.comment import URL


@dataclasses.dataclass
class Cache:
    """
    A cache mapping unique deviation URLs to comments.

    Args:
        entries: A mapping between unique deviation URLs and comments.
    """

    entries: dict[URL, Comment]

    @classmethod
    def from_comments(cls, comments: Iterable[Comment]) -> Cache:
        """
        Build a Cache from an iterable of comments.

        Args:
            comments: An iterable containing comments.

        Returns:
            An instance of Cache that maps unique deviation URLs to
                comments.
        """
        return cls({comment.url: comment for comment in comments})

    def find_comment_by_url(self, url: URL) -> Comment | None:
        """
        Find the comment with the specified URL.

        Args:
            url: The URL to look for.

        Returns:
            The comment whose URL matches url, or None.
        """
        return self.entries.get(url)
