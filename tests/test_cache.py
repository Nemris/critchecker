""" Tests for critchecker.cache. """

from hypothesis import given
from hypothesis.strategies import lists

from critchecker.cache import Cache
from critchecker.comment import Comment
from critchecker.comment import URL
from tests.strategies import comment_urls
from tests.strategies import comments


@given(lists(comments(), min_size=1, max_size=3))
def test_cached_comments_can_be_retrieved_by_url(comment_dicts):
    """
    Test that all cached comments can be retrieved by their URL.
    """
    data = (Comment(comment) for comment in comment_dicts)
    cache = Cache.from_comments(data)

    assert all(cache.find_comment_by_url(comment.url) for comment in data)


@given(lists(comment_urls(), min_size=1, max_size=3))
def test_attempting_to_fetch_nonexistent_comment_returns_none(urls):
    """
    Test that attempting to fetch uncached comments returns None.
    """
    urls = (URL.from_str(url) for url in urls)
    cache = Cache({})

    for url in urls:
        assert cache.find_comment_by_url(url) is None
