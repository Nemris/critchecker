""" Tests for critchecker.deviation. """

from hypothesis import given
from hypothesis.strategies import one_of
import pytest

from critchecker import deviation
from tests.strategies import comment_urls
from tests.strategies import deviation_urls
from tests.strategies import random_urls


# pylint: disable=no-value-for-parameter


@given(deviation_urls())
def test_deviation_urls_pass_validation(url):
    """
    Test that a deviation.Deviation accepts deviation URLs.
    """
    result = deviation.Deviation(url)

    assert result.artist in url
    assert result.category in url
    assert str(result.id) in url


@given(one_of(comment_urls(), random_urls()))
def test_misc_urls_are_rejected(url):
    """
    Test that a deviation.Deviation rejects non-deviation URLs.
    """
    with pytest.raises(ValueError):
        deviation.Deviation(url)
