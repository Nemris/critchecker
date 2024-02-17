""" Tests for critchecker.comment. """

from hypothesis import given
import pytest

from critchecker.comment import Comment, CommentPage, InvalidCommentTypeError, URL
from tests.strategies import comment_pages
from tests.strategies import comment_urls
from tests.strategies import comments
from tests.strategies import invalid_comments
from tests.strategies import random_urls


@given(invalid_comments() | comments())
def test_comment_instantiation_succeeds_only_for_draft_type(comment):
    """
    Test that a Comment accepts Draft comments and not others.
    """
    if comment["textContent"]["html"]["type"] == "draft":
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

    assert all(urls.count(url) == 1 for url in urls)


@given(comment_pages())
def test_commentpage_contains_only_draft_comments(comment_page):
    """
    Test that a comment page ignores non-Draft comments.
    """
    expected = len(
        [
            entry
            for entry in comment_page["thread"]
            if entry["textContent"]["html"]["type"] == "draft"
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
