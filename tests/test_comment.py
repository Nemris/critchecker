""" Tests for critchecker.comment. """

from hypothesis import given
import pytest

from critchecker import comment
from tests.strategies import comment_pages
from tests.strategies import comment_urls
from tests.strategies import comments
from tests.strategies import mixed_urls


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


@given(comment_urls())
def test_validating_valid_comment_urls_returns_true(comment_url):
    """
    Test that validating valid comment URLs returns True.
    """
    result = comment.is_url_valid(comment_url)

    assert result


@given(mixed_urls())
def test_extracted_urls_pass_validation(body):
    """
    Test that the extracted comment URLs pass validation.
    """
    result = comment.extract_comment_urls(body)

    for link in result:
        assert comment.is_url_valid(link)


@given(comment_urls())
def test_extracted_ids_from_url_are_three(comment_url):
    """
    Test that the IDs extracted from a comment URLs are three.
    """
    result = comment.extract_ids_from_url(comment_url)

    assert len(result) == 3
