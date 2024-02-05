""" Tests for critchecker.database. """

import io

from hypothesis import given

from critchecker import database
from tests.strategies import databases


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
def test_total_crits_equals_valid_plus_deleted(data):
    """
    Test that the amount of total critiques in a database equals the
    amount of valid plus deleted ones.
    """
    data = [database.Row(**row) for row in data]

    result = database.measure_stats(data)

    assert result[0] == (result[1] + result[2])
