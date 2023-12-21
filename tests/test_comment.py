""" Tests for critchecker.comment. """

from hypothesis import assume
from hypothesis import given
from hypothesis.strategies import one_of
import pytest

from critchecker import comment
from tests.strategies import comment_pages
from tests.strategies import comment_urls
from tests.strategies import comments
from tests.strategies import random_urls


@given(comments())
def test_comment_instantiation_succeeds_only_for_draft_type(comment_):
    """
    Test that a comment.Comment accepts Draft comments and not others.
    """
    if comment_["textContent"]["html"]["type"] == "draft":
        comment.Comment(comment_)
    else:
        with pytest.raises(comment.InvalidCommentTypeError):
            comment.Comment(comment_)


@given(comments())
def test_extracted_comment_urls_are_unique(comment_):
    """
    Test that the comment URLs extracted from a comment are unique.
    """
    assume(comment_["textContent"]["html"]["type"] == "draft")

    urls = comment.Comment(comment_).get_unique_comment_urls()

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

    result = comment.CommentPage(comment_page)

    assert len(result.comments) == expected


@given(one_of(random_urls(), comment_urls()))
def test_url_instantiation_succeds_only_for_valid_urls(url):
    """
    Test that a comment.URL accepts only valid comment URLs.
    """
    if "/comments/" in url:
        comment.URL.from_str(url)
    else:
        with pytest.raises(ValueError):
            comment.URL.from_str(url)
