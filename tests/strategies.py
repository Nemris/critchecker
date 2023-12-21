""" Common module for Hypothesis test strategies. """

import json
import string

from hypothesis import assume
from hypothesis.strategies import booleans
from hypothesis.strategies import composite
from hypothesis.strategies import datetimes
from hypothesis.strategies import integers
from hypothesis.strategies import just
from hypothesis.strategies import lists
from hypothesis.strategies import none
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
    random_url = "/".join(
        [
            "https://",
            "/".join(
                draw(lists(text(min_size=1), min_size=1)),
            ),
        ]
    )

    return random_url


@composite
def mixed_urls(draw):
    """
    Strategy to generate mixed DA comment and random URLs.

    Mixed URLs contain the \"https://\" prefix, and are joined by
    newlines.
    """
    urls = "\n".join(
        draw(lists(random_urls() | comment_urls(), max_size=3)),
    )

    return urls


@composite
def usernames(draw):
    """
    Strategy to generate DA usernames.

    Usernames have a minimum length of three characters and contain
    ASCII characters, digits and hyphens, the latter never at the
    beginning or end of the string.
    """
    charset = string.ascii_letters + string.digits + "-"

    username = draw(text(alphabet=charset, min_size=3))

    assume(not username.startswith("-") and not username.endswith("-"))

    return username


@composite
def comment_bodies(draw):
    """
    Strategy to generate DA comment bodies.

    Bodies are non-empty, contain text and may contain mixed URLs.
    """
    comment_body = " ".join(
        draw(lists(text(min_size=1) | mixed_urls(), min_size=1)),
    )

    return comment_body


@composite
def deviation_categories(draw):
    """
    Strategy to generate DA deviation categories.

    Categories contain lowercase ASCII characters and hyphens, the
    latter never at the beginning or end of the string.
    """
    charset = string.ascii_lowercase + "-"

    category = draw(text(alphabet=charset, min_size=1))

    assume(not category.startswith("-") and not category.endswith("-"))

    return category


@composite
def deviation_names(draw):
    """
    Strategy to generate DA deviation names.

    Deviation names contain an ASCII string with a trailing hyphen,
    followed by a numeric ID greater than zero.
    """
    charset = string.ascii_letters + string.digits + "-"

    name = "-".join(
        [
            draw(text(alphabet=charset, min_size=1)),
            str(draw(ids())),
        ]
    )

    return name


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
    Strategy to generate DA comment JSONs of mixed types.
    """
    comment = {
        "commentId": draw(ids()),
        "typeId": draw(ids()),
        "itemId": draw(ids()),
        "posted": draw(timestamps()),
        "edited": draw(none() | timestamps()),
        "user": {"username": draw(usernames())},
        "textContent": {
            "html": {
                "type": draw(just("draft") | text()),
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
def comment_pages(draw):
    """
    Strategy to generate DA comment page JSONs.

    Comment pages contain zero or more comments, a boolean flag that
    signals the presence of future pages and a positive integer offset.
    """
    # Generating comments is expensive - cap it.
    comment_page = {
        "hasMore": draw(booleans()),
        "nextOffset": draw(none() | integers(1)),
        "thread": draw(lists(comments(), max_size=2)),
    }

    assume(
        (comment_page["hasMore"] and comment_page["nextOffset"] is not None)
        or (not comment_page["hasMore"] and comment_page["nextOffset"] is None)
    )

    return comment_page


@composite
def database_rows(draw):
    """
    Strategy to generate database rows.
    """
    row = {
        "crit_posted_at": draw(timestamps()),
        "crit_edited_at": draw(timestamps()),
        "crit_author": draw(usernames()),
        "crit_words": draw(integers()),
        "block_posted_at": draw(timestamps()),
        "block_edited_at": draw(timestamps()),
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
    # Generating database rows is expensive - cap it.
    database = draw(lists(database_rows(), min_size=1, max_size=2))

    return database


@composite
def markups_with_csrf_token(draw):
    """
    Strategy to generate HTML markup containing CSRF tokens.
    """
    charset = string.ascii_letters + string.digits + "-."

    token = json.dumps(
        {"csrf": draw(text(alphabet=charset, min_size=1))},
        separators=(",", ":"),
    )

    markup = "".join(["<script>", token, "</script>"])

    return markup
