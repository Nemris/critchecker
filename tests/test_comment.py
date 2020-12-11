""" Tests for critchecker.comment. """

from hypothesis import given
from hypothesis.strategies import booleans
from hypothesis.strategies import composite
from hypothesis.strategies import lists
from hypothesis.strategies import integers
from hypothesis.strategies import text

from critchecker import comment


# pylint: disable=no-value-for-parameter


@composite
def deviation_ids(draw):
    """
    Hypothesis strategy to generate dummy DA deviation IDs.

    Deviation IDs must contain only positive integers.
    """

    deviation_id = draw(integers(1))

    return deviation_id


@composite
def type_ids(draw):
    """
    Hypothesis strategy to generate dummy DA type IDs.

    Type IDs must contain only positive integers.
    """

    type_id = draw(integers(1))

    return type_id


@composite
def comment_ids(draw):
    """
    Hypothesis strategy to generate dummy DA comment IDs.

    Comment IDs must contain only positive integers.
    """

    comment_id = draw(integers(1))

    return comment_id


@composite
def comment_urls(draw):
    """
    Hypothesis strategy to generate dummy DA comment URLs.

    Comment URLs must contain the
    \"https://www.deviantart.com/comments\" string, a type ID, a
    deviation ID and a comment ID.
    """

    url = "/".join([
        "https://www.deviantart.com",
        "comments",
        str(draw(type_ids())),
        str(draw(deviation_ids())),
        str(draw(comment_ids()))
    ])

    return url


@composite
def comments(draw):
    """
    Hypothesis strategy to generate dummy DA Eclipse comment dicts.
    """

    data = {
        "commentId": draw(comment_ids()),
        "parentId": draw(comment_ids()),
        "typeId": draw(type_ids()),
        "itemId": draw(deviation_ids()),
        "posted": draw(text()),
        "user": {
            "userId": draw(integers(1)),
            "username": draw(text())
        },
        "textContent": {
            "html": {
                "markup": draw(text())
            }
        }
    }

    return data


@composite
def commentpages(draw):
    """
    Hypothesis strategy to generate dummy DA Eclipse comment page

    dicts.
    """

    data = {
        "hasMore": draw(booleans()),
        "nextOffset": draw(integers(0)),
        "thread": draw(lists(comments(), max_size=50))
    }

    return data


@given(comments())
def test_comment_data_same_as_dict(comment_dict):
    """
    Test that instantiating a comment.Comment doesn't alter the sample
    data.
    """

    result = comment.Comment(comment_dict)

    assert result.id == comment_dict["commentId"]
    assert result.parent_id == comment_dict["parentId"]
    assert result.type_id == comment_dict["typeId"]
    assert result.belongs_to == comment_dict["itemId"]
    assert result.posted_at == comment_dict["posted"]
    assert result.author_id == comment_dict["user"]["userId"]
    assert result.author == comment_dict["user"]["username"]
    assert result.body == comment_dict["textContent"]["html"]["markup"]


@given(commentpages())
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


@given(deviation_ids(), type_ids(), comment_ids())
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

    result = comment.is_valid(comment_url)

    assert result


@given(deviation_ids(), type_ids(), comment_ids())
def test_assembled_comment_urls_pass_validation(deviation_id, type_id, comment_id):
    """
    Test that the assembled comment URL passes verification.
    """

    result = comment.assemble_url(deviation_id, type_id, comment_id)

    assert comment.is_valid(result)
