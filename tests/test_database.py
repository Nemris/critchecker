""" Tests for critchecker.database. """

from collections import Counter
import io

from hypothesis import given
from hypothesis.strategies import lists

from critchecker.database import Database, Row
from tests.strategies import database_rows


@given(lists(database_rows(), min_size=1, max_size=2))
def test_rows_written_equal_to_database_len_plus_one(rows):
    """
    Test that the number of rows written to a file is equal to
    len(data)+1.
    """
    rows = [Row(**row) for row in rows] * 2
    data = Database(rows)

    with io.StringIO(newline="") as stream:
        result = data.dump(stream)

    assert result == len(rows) + 1


@given(lists(database_rows(), min_size=1, max_size=2))
def test_total_crits_equals_valid_plus_deleted(rows):
    """
    Test that the amount of total critiques in a database equals the
    amount of valid plus deleted ones.
    """
    data = Database([Row(**row) for row in rows] * 2)

    assert data.total_critiques == data.valid_critiques + data.deleted_critiques


@given(lists(database_rows(), min_size=1, max_size=2))
def test_deduped_database_contains_no_duplicates(rows):
    """
    Test that deduplicating a database gets rid of duplicates.
    """
    data = Database([Row(**row) for row in rows] * 2)
    data.deduplicate()

    counts = Counter(row.crit_url for row in data.rows)
    assert all(val == 1 for val in counts.values())
