""" Tests for critchecker.deviation. """

import string

from hypothesis import assume
from hypothesis import given
from hypothesis.strategies import composite
from hypothesis.strategies import integers
from hypothesis.strategies import text

from critchecker import deviation


# pylint: disable=no-value-for-parameter

@composite
def usernames(draw):
    """
    Hypothesis strategy to generate dummy DA usernames.

    Usernames have a minimum length of 3, and must contain only upper
    and lowercase ASCII letters, digits and hyphens. The latter must
    not be at the beginning or end of the string.

    Note that DA considers usernames in a case-insensitive way.
    """

    username = draw(
        text(
            alphabet=string.ascii_letters + string.digits + "-",
            min_size=3
        )
    )

    assume(not username.startswith("-") and not username.endswith("-"))

    return username


@composite
def categories(draw):
    """
    Hypothesis strategy to generate dummy DA deviation categories.

    Category names must contain only lowercase ASCII letters and
    hyphens. The latter must not be at the beginning or end of the
    string.
    """

    category = draw(
        text(
            alphabet=string.ascii_lowercase + "-",
            min_size=1
        )
    )

    assume(not category.startswith("-") and not category.endswith("-"))

    return category


@composite
def deviations(draw):
    """
    Hypothesis strategy to generate dummy DA deviation names.

    Deviation names must contain an alphanumeric string with a trailing
    hyphen, followed by a positive integer.
    """

    deviation_name = "-".join([
        draw(
            text(
                alphabet=string.ascii_letters + string.digits + "-",
                min_size=1
            )
        ),
        str(draw(integers(1)))
    ])

    return deviation_name

@composite
def deviation_urls(draw):
    """
    Hypothesis strategy to generate dummy DA deviation URLs.

    Deviation URLs must contain the \"https://www.deviantart.com\"
    string, a username, a category and a deviation name.
    """

    url = "/".join([
        "https://www.deviantart.com",
        draw(usernames()),
        draw(categories()),
        draw(deviations())
    ])

    return url


@given(deviation_urls())
def test_deviation_id_is_decimal(url):
    """
    Test that a deviation ID represents a decimal number.
    """

    result = deviation.extract_id(url)

    assert result.isdecimal()
