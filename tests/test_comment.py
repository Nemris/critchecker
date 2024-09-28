""" Tests for critchecker.comment. """

from collections import Counter

from hypothesis import given
import pytest

from critchecker.comment import Comment, CommentPage, InvalidCommentTypeError, URL
from tests.strategies import comment_pages
from tests.strategies import comment_urls
from tests.strategies import comments
from tests.strategies import invalid_comments
from tests.strategies import random_urls


@given(invalid_comments() | comments())
def test_comment_instantiation_succeeds_only_for_tiptap_type(comment):
    """
    Test that a Comment accepts Tiptap comments and not others.
    """
    if comment["textContent"]["html"]["type"] == "tiptap":
        Comment(comment)
    else:
        with pytest.raises(InvalidCommentTypeError):
            Comment(comment)


@given(comments())
def test_extracted_comment_urls_are_unique(comment):
    """
    Test that the comment URLs extracted from a comment are unique.
    """
    urls = Comment(comment).get_unique_comment_urls()
    counter = Counter(urls)

    assert all(value == 1 for value in counter.values())


@given(comment_pages())
def test_commentpage_contains_only_tiptap_comments(comment_page):
    """
    Test that a comment page ignores non-Tiptap comments.
    """
    expected = len(
        [
            entry
            for entry in comment_page["thread"]
            if entry["textContent"]["html"]["type"] == "tiptap"
        ]
    )

    result = CommentPage(comment_page)

    assert len(result.comments) == expected


@given(comment_urls() | random_urls())
def test_url_instantiation_succeds_only_for_valid_urls(url):
    """
    Test that a URL accepts only valid comment URLs.
    """
    if "/comments/" in url:
        URL.from_str(url)
    else:
        with pytest.raises(ValueError):
            URL.from_str(url)
