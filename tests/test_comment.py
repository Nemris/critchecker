""" Tests for critchecker.comment. """

import json

from hypothesis import given

from critchecker import comment
from tests.strategies import comment_bodies
from tests.strategies import comment_markups
from tests.strategies import comment_pages
from tests.strategies import comment_urls
from tests.strategies import draft_comments
from tests.strategies import ids
from tests.strategies import mixed_urls


# pylint: disable=no-value-for-parameter


@given(draft_comments())
def test_comment_data_same_as_dict(comment_dict):
    """
    Test that instantiating a comment.Comment doesn't alter the sample
    data.
    """

    blocks = json.loads(comment_dict["textContent"]["html"]["markup"])["blocks"]
    features = json.loads(comment_dict["textContent"]["html"]["features"])
    result = comment.Comment(comment_dict)

    # The URL is assembled from three attributes, so let's just check
    # its validity, rather than remaking it ourselves.
    assert comment.is_url_valid(result.url)

    assert result.parent_id == comment_dict["parentId"]
    assert result.posted_at == comment_dict["posted"]
    assert result.edited_at == comment_dict["edited"]
    assert result.author == comment_dict["user"]["username"]
    assert result.body == "\n".join([block["text"] for block in blocks])
    assert result.words == features[0]["data"]["words"]


@given(comment_pages())
def test_commentpage_data_same_as_dict(commentpage_dict):
    """
    Test that instantiating a comment.CommentPage doesn't alter the
    sample data.
    """

    result = comment.CommentPage(commentpage_dict)

    assert result.has_more == commentpage_dict["hasMore"]
    assert result.next_offset == commentpage_dict["nextOffset"]

    # No way to test result.comments for equality, so we compare its
    # length, instead.
    assert len(result.comments) == len(commentpage_dict["thread"])


@given(ids(), ids(), ids())
def test_comment_url_contains_all_ids(deviation_id, type_id, comment_id):
    """
    Test that the assembled comment URL contains the starting IDs.
    """

    result = comment.assemble_url(deviation_id, type_id, comment_id)

    assert str(deviation_id) in result
    assert str(type_id) in result
    assert str(comment_id) in result


@given(comment_urls())
def test_validating_valid_comment_urls_returns_true(comment_url):
    """
    Test that validating valid comment URLs returns True.
    """

    result = comment.is_url_valid(comment_url)

    assert result


@given(ids(), ids(), ids())
def test_assembled_comment_urls_pass_validation(deviation_id, type_id, comment_id):
    """
    Test that the assembled comment URL passes verification.
    """

    result = comment.assemble_url(deviation_id, type_id, comment_id)

    assert comment.is_url_valid(result)


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


@given(comment_markups())
def test_comment_markup_to_text_replaces_br_tag(comment_markup):
    """
    Test that converting comment markup to text strips \"<br>\" tags.
    """

    result = comment.markup_to_text(comment_markup)

    assert "<br />" not in result


@given(comment_bodies())
def test_comment_word_count_is_always_positive_int(body):
    """
    Test that counting the words in a comment always returns a positive
    integer.
    """

    result = comment.count_words(body)

    assert result >= 0
