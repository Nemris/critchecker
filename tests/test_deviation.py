""" Tests for critchecker.deviation. """

from hypothesis import example
from hypothesis import given

from critchecker import deviation
from tests.strategies import deviation_urls
from tests.strategies import deviation_categories


# pylint: disable=no-value-for-parameter


@given(deviation_urls())
def test_deviation_id_is_decimal(url):
    """
    Test that a deviation ID represents a decimal number.
    """

    result = deviation.extract_id(url)

    assert result.isdecimal()


@given(deviation_urls())
def test_deviation_category_is_lowercase(url):
    """
    Test that a deviation category is lowercase.
    """

    result = deviation.extract_category(url)

    assert result.islower()


@given(deviation_categories())
@example("art")
@example("journal")
def test_deviation_type_id_greater_equal_to_zero(category):
    """
    Test that a deviation type ID is greater or equal to zero.
    """

    result = deviation.typeid_of(category)

    assert result >= 0
