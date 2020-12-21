""" Tests for critchecker.database. """

from hypothesis.strategies import composite
from hypothesis.strategies import integers
from hypothesis.strategies import lists
from hypothesis.strategies import none
from hypothesis.strategies import text

from critchecker import database


# pylint: disable=no-value-for-parameter


@composite
def rows(draw):
    """
    Hypothesis strategy to generate dummy database Row()s.
    """

    row = {
        "crit_parent_id": draw(integers(1)),
        "crit_parent_type": draw(integers(1)),
        "crit_id": draw(integers(1)),
        "crit_posted_at": draw(text(min_size=1)),
        "crit_edited_at": draw(text(min_size=1) | none()),
        "crit_author": draw(text(min_size=1)),
        "crit_words": draw(integers(1)),
        "crit_url": draw(text(min_size=1))
    }

    return database.Row(**row)


@composite
def databases(draw):
    """
    Hypothesis strategy to generate dummy databases.

    A database is a list of Row() entries.
    """

    db = draw(lists(rows(), min_size=1))

    return db
