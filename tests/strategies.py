""" Common module for Hypothesis test strategies. """

import json
import string

from hypothesis.strategies import booleans
from hypothesis.strategies import composite
from hypothesis.strategies import datetimes
from hypothesis.strategies import integers
from hypothesis.strategies import lists
from hypothesis.strategies import text


@composite
def ids(draw):
    """
    Strategy to generate IDs.

    IDs contain only integers greater than zero.
    """
    sample_id = draw(integers(1))

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
            str(draw(ids())),
            str(draw(ids())),
            str(draw(ids())),
        ]
    )

    return comment_url


@composite
def random_urls(draw):
    """
    Strategy to generate random URLs.

    Random URLs contain the \"https://\" prefix, followed by any other
    string.
    """
    alphabet = string.ascii_lowercase + string.digits
    random_url = "".join(
        [
            "https://",
            "/".join(
                draw(
                    lists(
                        text(alphabet=alphabet, min_size=1, max_size=5),
                        min_size=1,
                        max_size=5,
                    )
                ),
            ),
        ]
    )

    return random_url


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
def comment_bodies(draw):
    """
    Strategy to generate DA comment bodies.

    Bodies are non-empty and may contain text or mixed URLs.
    """
    # Artificially duplicate data to allow testing for deduplication.
    comment_body = " ".join(
        draw(
            lists(
                text(min_size=1, max_size=5) | comment_urls() | random_urls(),
                min_size=1,
                max_size=5,
            )
        )
        * 2,
    )

    return comment_body


@composite
def deviation_categories(draw):
    """
    Strategy to generate DA deviation categories.

    Categories contain lowercase ASCII characters and hyphens, the
    latter never at the beginning or end of the string.
    """
    alphabet = string.ascii_lowercase

    begin = draw(text(alphabet=alphabet, min_size=1, max_size=1))
    middle = draw(text(alphabet=alphabet + "-", min_size=1, max_size=5))
    end = draw(text(alphabet=alphabet, min_size=1, max_size=1))

    return "".join([begin, middle, end])


@composite
def deviation_names(draw):
    """
    Strategy to generate DA deviation names.

    Deviation names contain a numeric ID greater than zero, optionally
    preceded by an ASCII string with a trailing hyphen.
    """
    alphabet = string.ascii_letters + string.digits + "-"

    label = draw(text(alphabet=alphabet, max_size=15))
    dev_id = str(draw(ids()))

    if label:
        return "-".join([label, dev_id])
    return dev_id


@composite
def deviation_urls(draw):
    """
    Strategy to generate DA deviation URLs.

    Deviation URLs contain the \"https://www.deviantart.com\" prefix,
    followed by a username, a deviation category and a deviation name.
    """
    url = "/".join(
        [
            "https://www.deviantart.com",
            draw(usernames()),
            draw(deviation_categories()),
            draw(deviation_names()),
        ]
    )

    return url


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
def comments(draw):
    """
    Strategy to generate DA comment JSONs.
    """
    comment = {
        "commentId": draw(ids()),
        "typeId": draw(ids()),
        "itemId": draw(ids()),
        "posted": draw(timestamps()),
        "user": {"username": draw(usernames())},
        "textContent": {
            "html": {
                "type": "draft",
                "markup": json.dumps(
                    {
                        "blocks": [
                            {"text": draw(comment_bodies())},
                        ]
                    },
                ),
                "features": json.dumps(
                    [
                        {
                            "type": "WORD_COUNT_FEATURE",
                            "data": {"words": draw(integers(1))},
                        }
                    ]
                ),
            }
        },
    }

    return comment


@composite
def invalid_comments(draw):
    """
    Strategy to generate minimal DA comment JSONs of invalid type.
    """
    comment = {
        "textContent": {
            "html": {
                "type": draw(text(max_size=3)),
            }
        }
    }

    return comment


@composite
def comment_pages(draw):
    """
    Strategy to generate DA comment page JSONs.

    Comment pages contain zero or more comments, a boolean flag that
    signals the presence of future pages and a positive integer offset.
    """
    has_more = draw(booleans())
    next_offset = draw(integers(1)) if has_more else None

    comment_page = {
        "hasMore": has_more,
        "nextOffset": next_offset,
        "thread": draw(lists(invalid_comments() | comments(), max_size=2)),
    }

    return comment_page


@composite
def database_rows(draw):
    """
    Strategy to generate database rows.
    """
    row = {
        "crit_tstamp": draw(timestamps()),
        "crit_author": draw(usernames()),
        "crit_words": draw(integers()),
        "crit_url": draw(comment_urls()),
        "block_url": draw(comment_urls()),
    }

    return row


@composite
def databases(draw):
    """
    Strategy to generate databases.

    Databases are lists of rows.
    """
    # Artificially duplicate data for some tests.
    database = draw(lists(database_rows(), min_size=1, max_size=2)) * 2

    return database


@composite
def markups_with_csrf_token(draw):
    """
    Strategy to generate HTML markup containing CSRF tokens.
    """
    alphabet = string.ascii_letters + string.digits + "-."

    token = json.dumps(
        {"csrf": draw(text(alphabet=alphabet, min_size=1))},
        separators=(",", ":"),
    )

    markup = "".join(["<script>", token, "</script>"])

    return markup
