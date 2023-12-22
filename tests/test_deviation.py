""" Tests for critchecker.deviation. """

from hypothesis import given
import pytest

from critchecker import deviation
from tests.strategies import comment_urls
from tests.strategies import deviation_urls
from tests.strategies import random_urls


@given(deviation_urls())
def test_deviation_urls_pass_validation(url):
    """
    Test that a deviation.Deviation accepts deviation URLs.
    """
    result = deviation.Deviation(url)

    assert result.artist in url
    assert result.category in url
    assert str(result.id) in url


@given(comment_urls() | random_urls())
def test_misc_urls_are_rejected(url):
    """
    Test that a deviation.Deviation rejects non-deviation URLs.
    """
    with pytest.raises(ValueError):
        deviation.Deviation(url)
