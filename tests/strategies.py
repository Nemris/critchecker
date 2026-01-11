"""Common module for Hypothesis test strategies."""

import string

from hypothesis.strategies import composite
from hypothesis.strategies import datetimes
from hypothesis.strategies import integers
from hypothesis.strategies import none
from hypothesis.strategies import text


@composite
def ids(draw):
    """
    Strategy to generate IDs.

    IDs contain only integers greater than zero.
    """
    sample_id = str(draw(integers(1)))

    return sample_id


@composite
def comment_urls(draw):
    """
    Strategy to generate DA comment URLs.

    Comment URLs contain the \"https://www.deviantart.com/comments\"
    prefix, followed by three numeric IDs greater than zero.
    """
    comment_url = "/".join(
        [
            "https://www.deviantart.com/comments",
            draw(ids()),
            draw(ids()),
            draw(ids()),
        ]
    )

    return comment_url


@composite
def usernames(draw):
    """
    Strategy to generate DA usernames.

    Usernames have a minimum length of three characters and contain
    ASCII characters, digits and hyphens, the latter never at the
    beginning or end of the string.
    """
    alphabet = string.ascii_letters + string.digits

    begin = draw(text(alphabet=alphabet, min_size=1, max_size=1))
    middle = draw(text(alphabet=alphabet + "-", min_size=1))
    end = draw(text(alphabet=alphabet, min_size=1, max_size=1))

    return "".join([begin, middle, end])


@composite
def timestamps(draw):
    """
    Strategy to generate DA timestamps.

    Timestamps are in the format YYYY-MM-DDTHH:MM:SS-0800.
    """
    timestamp = "".join(
        [
            draw(datetimes()).isoformat(timespec="seconds"),
            "-0800",
        ]
    )

    return timestamp


@composite
def database_rows(draw):
    """
    Strategy to generate database rows.
    """
    row = {
        "crit_tstamp": draw(none() | timestamps()),
        "crit_author": draw(none() | usernames()),
        "crit_words": draw(none() | integers()),
        "crit_url": draw(comment_urls()),
        "batch_url": draw(comment_urls()),
    }

    return row
