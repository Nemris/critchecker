""" Functions that handle DA deviations. """

from __future__ import annotations

import dataclasses
import re


# This pattern extracts the artist, deviation type and ID.
DEVIATION_URL_PATTERN = re.compile(
    r"www\.deviantart\.com/([A-Za-z0-9\-]+)/([a-z\-]+)/(?:.+-)?(\d+)$"
)


@dataclasses.dataclass
class Deviation:
    """
    A single deviation.

    Args:
        artist: The deviation artist.
        category: The deviation category.
        id: The deviation ID.
    """

    artist: str
    category: str
    id: int  # pylint: disable=invalid-name

    @classmethod
    def from_url(cls, url: str) -> Deviation:
        """
        Build a Deviation from a deviation URL.

        Args:
            url: The string representation of a deviation URL.

        Returns:
            An instance of Deviation.

        Raises:
            ValueError: If url is not a valid deviation URL.
        """
        try:
            artist, category, id_ = DEVIATION_URL_PATTERN.search(url).groups()
        except AttributeError as exc:
            raise ValueError(f"{url!r}: invalid deviation URL") from exc

        return cls(artist, category, id_)

    @property
    def type_id(self) -> int:
        """The deviation's type ID."""
        # Consider only these categories for the time being.
        mapping = {
            "art": 1,
            "journal": 1,
        }

        return mapping.get(self.category, 0)
