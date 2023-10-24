""" Functions that handle DA deviations. """

import dataclasses
import re


@dataclasses.dataclass
class Deviation:
    """
    A single deviation.

    Args:
        url: The URL pointing to the deviation.
    """

    url: str

    def _search_pattern(self, pattern: str) -> str:
        """
        Search for pattern in the URL to this deviation.

        Args:
            pattern: Pattern to search for, which will be appended to
                "www.deviantart.com".

        Returns:
            The region matching pattern.

        Raises:
            AttributeError: If no matches are found.
        """
        # Let's ignore the schema for now.
        base = r"www\.deviantart\.com"
        return re.search(f"{base}{pattern}", self.url).group(1)

    def __post_init__(self) -> None:
        """Validate this deviation by checking its URL."""
        try:
            _ = self.artist
            _ = self.category
            _ = self.id
        except AttributeError as exc:
            raise ValueError(f"{self.url!r}: invalid deviation URL") from exc

    @property
    def artist(self) -> str:
        """The deviation's artist."""
        pattern = r"/([A-Za-z0-9\-]+)/"
        return self._search_pattern(pattern)

    @property
    def category(self) -> str:
        """The deviation's category."""
        pattern = r"/.+/([a-z\-]+)/"
        return self._search_pattern(pattern)

    @property
    def id(self) -> int:  # pylint: disable=invalid-name
        """The deviation's ID."""
        pattern = r"/.+/.+/.+-(\d+)$"
        return int(self._search_pattern(pattern))

    @property
    def type_id(self) -> int:
        """The deviation's type ID."""
        # Consider only these categories for the time being.
        mapping = {
            "art": 1,
            "journal": 1,
        }

        return mapping.get(self.category, 0)
