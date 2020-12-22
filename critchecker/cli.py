""" Command-line interface for critchecker. """

import argparse
import pathlib
import sys

from critchecker import database
from critchecker import deviation
from critchecker import comment


def read_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        The parsed command-line arguments.
    """

    parser = argparse.ArgumentParser(
        description="Extract and measure the length of DeviantArt Critmas critiques."
    )

    parser.add_argument(
        "journal",
        type=str,
        help="the URL of the Critmas launch journal"
    )
    parser.add_argument(
        "-r",
        "--report",
        type=pathlib.Path,
        default=pathlib.Path.home().joinpath("critmas.csv"),
        help="the path to a CSV report created by critchecker"
    )

    return parser.parse_args()


def print_warn(msg: str) -> None:
    """
    Print a warning message to standard error.

    Args:
        msg: The message to print.
    """

    print(f"Warning: {msg}")


def exit_fatal(msg: str) -> None:
    """
    Print an error message to standard error and exit with code 1.

    Args:
        msg: The error message to print.
    """

    sys.exit(f"Fatal: {msg}")


def fetch_critique(url: str) -> comment.Comment:
    """
    Fetch a critique by its URL.

    Args:
        url: The URL to the critique.

    Returns:
        The critique.
    """

    ids = comment.extract_ids_from_url(url)

    return comment.fetch(ids["deviation_id"], ids["type_id"], ids["comment_id"])


def truncate_timestamp(timestamp: str) -> str:
    """
    Inelegantly truncate a timestamp and return the date segment.

    Args:
        timestamp: The timestamp to truncate.

    Returns:
        The date segment of the timestamp.
    """

    try:
        date = timestamp.split("T")[0]
    except AttributeError:
        # Not tragic, just return an empty string.
        date = ""

    return date


def count_crit_words(crit: comment.Comment) -> int:
    """
    Measure a critique's length in words, excluding URLs.

    Args:
        crit: The critique to check.

    Returns:
        The critique's length, in words.
    """

    return comment.count_words(comment.markup_to_text(crit.body))


def crit_to_row(crit: comment.Comment) -> database.Row:
    """
    Compose a database row from critique attributes.

    Args:
        crit: The critique to analyze.

    Returns:
        A database row composed of select critique attributes.
    """

    row = database.Row(
        crit_parent_id = crit.belongs_to,
        crit_parent_type = crit.type_id,
        crit_id = crit.id,
        crit_posted_at = truncate_timestamp(crit.posted_at),
        crit_edited_at = truncate_timestamp(crit.edited_at),
        crit_author = crit.author,
        crit_words = count_crit_words(crit),
        crit_url = comment.assemble_url(crit.belongs_to, crit.type_id, crit.id)
    )

    return row


def main(journal: str, report: pathlib.Path) -> None:
    """
    Core of critchecker.

    Args:
        journal: The URL of the Critmas launch journal.
        database: The path to a CSV report created by critchecker.
    """

    try:
        journal_id = deviation.extract_id(journal)
        journal_category = deviation.extract_category(journal)
    except ValueError as exception:
        exit_fatal(f"{exception}.")

    journal_type = deviation.typeid_of(journal_category)

    data = []
    try:
        infile = report.open("r", newline="")
    except OSError as exception:
        # Let's not get scared if there are problems loading the
        # report.
        print_warn(f"{exception}.\n")
    else:
        with infile:
            data = database.load(infile)


def wrapper() -> None:
    """
    Entry point for critchecker.
    """

    try:
        main(**vars(read_args()))
    except KeyboardInterrupt:
        # Gracefully abort.
        print("\rInterrupted by user.")
