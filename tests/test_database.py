""" Tests for critchecker.database. """

import io

from hypothesis import given

from critchecker import database
from tests.strategies import databases


# pylint: disable=no-value-for-parameter


@given(databases())
def test_rows_written_equal_to_database_len_plus_one(data):
    """
    Test that the number of rows written to a file is equal to
    len(data)+1.
    """
    data = [database.Row(**row) for row in data]

    with io.StringIO(newline="") as stream:
        result = database.dump(data, stream)

    assert result == len(data) + 1


@given(databases())
def test_written_database_same_as_original(data):
    """
    Test that writing and loading the database doesn't alter it.
    """
    data = [database.Row(**row) for row in data]

    with io.StringIO(newline="") as stream:
        database.dump(data, stream)
        stream.seek(0)
        result = database.load(stream)

    assert result == data


@given(databases())
def test_finding_index_finds_first_row_with_same_crit_url(data):
    """
    Test that finding an index in a database finds the first row with a
    specific crit_url, irrespective of the other instance attributes.
    """
    data = [database.Row(**row) for row in data]

    url = data[-1].crit_url
    result = database.get_index_by_crit_url(url, data)

    assert data[result].crit_url == url


@given(databases())
def test_total_crits_equals_valid_plus_deleted(data):
    """
    Test that the amount of total critiques in a database equals the
    amount of valid plus deleted ones.
    """
    data = [database.Row(**row) for row in data]

    result = database.measure_stats(data)

    assert result[0] == (result[1] + result[2])
