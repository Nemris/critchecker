""" Facilities that handle critiques. """

import dataclasses

from critchecker.comment import URL


@dataclasses.dataclass
class Batch:
    """
    A batch of critique URLs contained in a Critmas journal comment.

    Args:
        url: The URL of the journal comment.
        crit_urls: Deduplicated set of comment URLs contained in the
            comment's body.
    """

    url: URL
    crit_urls: set[URL]
