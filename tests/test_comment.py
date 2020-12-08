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
def comments(draw):
    """
    Hypothesis strategy to generate dummy DA Eclipse comment dicts.
    """

    data = {
        "commentId": draw(integers(1)),
        "parentId": draw(integers(1)),
        "typeId": draw(integers(1)),
        "itemId": draw(integers(1)),
        "posted": draw(text()),
        "user": {
            "userId": integers(1),
            "username": text()
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
