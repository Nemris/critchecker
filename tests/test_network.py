""" Tests for critchecker.network. """

from hypothesis import given

from critchecker import network
from tests.strategies import markups_with_csrf_token


@given(markups_with_csrf_token())
def test_extracted_token_is_between_quotes_in_markup(markup_with_csrf_token):
    """
    Test that the extracted token is between quotes in the markup.
    """

    result = network.extract_csrf_token(markup_with_csrf_token)

    assert f"'{result}'" in markup_with_csrf_token
