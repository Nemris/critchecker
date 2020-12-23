""" Tests for critchecker.comment. """

import json

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
def bad_urls(draw):
    """
    Hypothesis strategy to generate dummy bad URLs.

    A bad URL must contain the \"https://\" string, and may contain
    any other string.
    """

    url = "".join([
        "https://",
        "/".join(
            draw(
                lists(
                    text(min_size=1),
                    min_size=1
                )
            )
        )
    ])

    return url


@composite
def misc_urls(draw):
    """
    Hypothesis strategy to generate valid and invalid dummy DA comment
    URLs.

    Invalid comment URLs must contain the \"https://\" prefix, and may
    contain any other string.
    """

    urls = "\n".join(
        draw(
            lists(
                comment_urls() | bad_urls()
            )
        )
    )

    return urls


@composite
def comment_markups(draw):
    """
    Hypothesis strategy to generate dummy DA comment body markups.

    Body markups contain text, and may contain HTML tags.
    """

    markup = "".join([
        draw(text()),
        "<br />",
        draw(text())
    ])

    return markup


@composite
def comment_bodies(draw):
    """
    Hypothesis strategy to generate dummy DA comment bodies.

    Bodies contain text, and must not be empty.
    """

    body = draw(
        lists(
            text(min_size=1),
            min_size=1
        )
    )

    return " ".join(body)


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
        "edited": draw(text()),
        "user": {
            "userId": draw(integers(1)),
            "username": draw(text())
        },
        "textContent": {
            "html": {
                "markup": json.dumps(
                    {
                        "blocks": [
                            {
                                "text": draw(text())
                            }
                        ]
                    }
                ),
                "features": json.dumps(
                    [
                        {
                            "type": "WORD_COUNT_FEATURE",
                            "data": {
                                "words": draw(integers(1))
                            }
                        }
                    ]
                )
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

    blocks = json.loads(comment_dict["textContent"]["html"]["markup"])["blocks"]
    features = json.loads(comment_dict["textContent"]["html"]["features"])
    result = comment.Comment(comment_dict)

    assert result.id == comment_dict["commentId"]
    assert result.parent_id == comment_dict["parentId"]
    assert result.type_id == comment_dict["typeId"]
    assert result.belongs_to == comment_dict["itemId"]
    assert result.posted_at == comment_dict["posted"]
    assert result.edited_at == comment_dict["edited"]
    assert result.author_id == comment_dict["user"]["userId"]
    assert result.author == comment_dict["user"]["username"]
    assert result.body == "\n".join([block["text"] for block in blocks])
    assert result.words == features[0]["data"]["words"]


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

    result = comment.is_url_valid(comment_url)

    assert result


@given(deviation_ids(), type_ids(), comment_ids())
def test_assembled_comment_urls_pass_validation(deviation_id, type_id, comment_id):
    """
    Test that the assembled comment URL passes verification.
    """

    result = comment.assemble_url(deviation_id, type_id, comment_id)

    assert comment.is_url_valid(result)


@given(anchor_tags())
def test_extracted_urls_pass_validation(tag):
    """
    Test that the extracted comment URL passes validation.
    """

   # result = [link for link in comment.yield_links(tag)]

    for link in comment.yield_links(tag):
        assert comment.is_url_valid(link)


@given(comment_urls())
def test_extracted_ids_from_url_are_ints(comment_url):
    """
    Test that the IDs extracred from a comment URLs are int instances.
    """

    result = comment.extract_ids_from_url(comment_url)

    for key in result:
        assert isinstance(result[key], int)


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
