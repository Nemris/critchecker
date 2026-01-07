"""Facilities that handle a cache of comments."""

from __future__ import annotations

from collections.abc import Iterable
import dataclasses

from sundown import comment


@dataclasses.dataclass
class Cache:
    """
    A cache mapping comments to their IDs, without duplicates.

    Args:
        entries: A mapping between comments and their IDs.
    """

    entries: dict[str, comment.Comment]

    @classmethod
    def from_comments(cls, comments: Iterable[comment.Comment]) -> Cache:
        """
        Build a Cache from an iterable of comments.

        Args:
            comments: An iterable containing comments.

        Returns:
            An instance of Cache that maps comment IDs to comments.
        """
        return cls({c.metadata.id: c for c in comments})

    def find_by_id(self, comment_id: str) -> comment.Comment | None:
        """
        Find the comment with the specified ID.

        Args:
            comment_id: The ID to look for.

        Returns:
            The comment matching comment_id, or None.
        """
        return self.entries.get(comment_id)
