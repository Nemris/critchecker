""" Tests for critchecker.client. """

from hypothesis import given

from critchecker import client
from tests.strategies import markups_with_csrf_token


@given(markups_with_csrf_token())
def test_extracted_token_exists_in_markup(markup_with_csrf_token):
    """
    Test that the extracted token exists in the markup.
    """
    result = client.extract_token(markup_with_csrf_token)

    assert f'"{result}"' in markup_with_csrf_token
