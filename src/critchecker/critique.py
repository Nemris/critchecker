"""Facilities that handle critiques."""

import dataclasses

from sundown import comment


@dataclasses.dataclass
class Batch:
    """
    A batch of critique URLs contained in a Critmas journal comment.

    Args:
        url: The URL of the journal comment.
        crit_urls: Deduplicated set of comment URLs found in the
            comment.
    """

    url: comment.URL
    crit_urls: set[comment.URL]
