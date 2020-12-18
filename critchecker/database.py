""" Functions and dataclasses that handle Critmas reports. """

import dataclasses
import typing


@dataclasses.dataclass
class Row():  # pylint: disable=too-many-instance-attributes
    """
    A single row in a Critmas report.

    Args:
        crit_parent_id: The parent deviation's ID.
        crit_parent_type: The parent deviation's type ID.
        crit_id: The critique's ID.
        crit_posted_at: The critique's timestamp.
        crit_edited_at: The critique's edited timestamp, if any.
        crit_author: The critique's author.
        crit_words: The critique's length in words.
        crit_url: The critique's URL.
    """

    # pylint: disable=unsubscriptable-object

    crit_parent_id: int
    crit_parent_type: int
    crit_id: int
    crit_posted_at: str
    crit_edited_at: typing.Optional[str]
    crit_author: str
    crit_words: int
    crit_url: str
