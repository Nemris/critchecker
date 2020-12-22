""" Tests for critchecker.database. """

import dataclasses
import io
import string

from hypothesis import given
from hypothesis.strategies import composite
from hypothesis.strategies import dates
from hypothesis.strategies import integers
from hypothesis.strategies import lists
from hypothesis.strategies import none
from hypothesis.strategies import text

from critchecker import database


# pylint: disable=no-value-for-parameter


@composite
def url_strings(draw):
    """
    Hypothesis strategy to generate dummy strings of legal URLchars.

    A string must contain only ASCII characters, digits, slashes,
    hyphens, and colons.
    """

    # TODO: Replace when refactoring strategies.

    url = draw(
        text(
            alphabet=string.ascii_letters + string.digits + ":/-",
            min_size=1
        )
    )

    return url


@composite
def usernames(draw):
    """
    Hypothesis strategy to generate dummy usernames.

    A username must contain only lowercase ASCII letters, digits and
    hyphens.
    """

    # TODO: Replace when refactoring strategies.

    username = draw(
        text(
            alphabet=string.ascii_lowercase + string.digits + "-",
            min_size=3
        )
    )

    return username


@composite
def human_dates(draw):
    """
    Hypothesis strategy to generate human-readable dates.

    A date must be in the format YYYY-MM-DD.
    """

    date = draw(dates()).strftime("%Y-%m-%d")

    return date


@composite
def rows(draw):
    """
    Hypothesis strategy to generate dummy database Row()s.
    """

    row = {
        "crit_parent_id": draw(integers(1)),
        "crit_parent_type": draw(integers(1)),
        "crit_id": draw(integers(1)),
        "crit_posted_at": draw(human_dates()),
        "crit_edited_at": draw(human_dates()),
        "crit_author": draw(usernames()),
        "crit_words": draw(integers(1)),
        "crit_url": draw(url_strings())
    }

    return database.Row(**row)


@composite
def databases(draw):
    """
    Hypothesis strategy to generate dummy databases.

    A database is a list of Row() entries.
    """

    data = draw(lists(rows(), min_size=1))

    return data


@given(databases())
def test_rows_written_equal_to_database_len_plus_one(data):
    """
    Test that the number of rows written to a file is equal to
    len(data)+1.
    """

    with io.StringIO(newline="") as stream:
        result = database.dump(data, stream)

    assert result == len(data) + 1


@given(databases())
def test_written_database_same_as_original(data):
    """
    Test that writing and loading the database doesn't alter it.
    """

    with io.StringIO(newline="") as stream:
        database.dump(data, stream)
        stream.seek(0)
        result = database.load(stream)

    for index, row in enumerate(result):
        original = data[index]

        assert int(row.crit_parent_id) == original.crit_parent_id
        assert int(row.crit_parent_type) == original.crit_parent_type
        assert int(row.crit_id) == original.crit_id
        assert row.crit_posted_at == original.crit_posted_at
        assert row.crit_edited_at == original.crit_edited_at
        assert row.crit_author == original.crit_author
        assert int(row.crit_words) == original.crit_words
        assert row.crit_url == original.crit_url
