""" Tests for critchecker.database. """

import datetime
import io
import string

from hypothesis import given
from hypothesis.strategies import composite
from hypothesis.strategies import datetimes
from hypothesis.strategies import integers
from hypothesis.strategies import lists
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
def timestamps(draw):
    """
    Hypothesis strategy to generate dummy DA timestamps.
    """

    timestamp = "-".join([
        draw(datetimes()).strftime("%Y-%m-%dT%H:%M:%S"),
        "0800"
    ])

    return timestamp


@composite
def human_dates(draw):
    """
    Hypothesis strategy to generate human-readable dates.

    A date must be in the format YYYY-MM-DD.
    """

    date = draw(datetimes()).strftime("%Y/%m/%d %H%:%M")

    return date


@composite
def rows(draw):
    """
    Hypothesis strategy to generate dummy database Row()s.
    """

    row = {
        "crit_posted_at": draw(human_dates()),
        "crit_edited_at": draw(human_dates()),
        "crit_author": draw(usernames()),
        "crit_words": draw(integers()),
        "block_posted_at": draw(human_dates()),
        "block_edited_at": draw(human_dates()),
        "crit_url": draw(url_strings()),
        "block_url": draw(url_strings())
    }

    return database.Row(**row)


@composite
def databases(draw):
    """
    Hypothesis strategy to generate dummy databases.

    A database is a list of Row() entries.
    """

    # Limit the size of generated databases for performance's sake.
    data = draw(lists(rows(), min_size=1, max_size=3))

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

    assert result == data


@given(timestamps())
def test_formatted_timestamp_not_empty(timestamp):
    """
    Test that formatting a timestamp doesn't return an empty string.
    """

    result = database.format_timestamp(timestamp)

    assert result != ""


@given(databases())
def test_finding_index_finds_first_row_with_same_crit_url(data):
    """
    Test that finding an index in a database finds the first row with a
    specific crit_url, irrespective of the other instance attributes.
    """

    url = data[-1].crit_url
    result = database.get_index_by_crit_url(url, data)

    assert data[result].crit_url == url


@given(human_dates())
def test_valid_timestamp_returns_datetime(timestamp):
    """
    Test that trying to convert a valid timestamp to a datetime always
    returns a datetime.datetime object.
    """

    result = database.timestamp_to_datetime(timestamp)

    assert isinstance(result, datetime.datetime)


@given(databases())
def test_total_crits_equals_valid_plus_deleted(data):
    """
    Test that the amount of total critiques in a database equals the
    amount of valid plus deleted ones.
    """

    result = database.measure_stats(data)

    assert result[0] == (result[1] + result[2])
