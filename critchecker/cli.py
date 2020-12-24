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


def count_crit_words(crit: comment.Comment) -> int:
    """
    Measure a critique's length in words, excluding URLs.

    Args:
        crit: The critique to check.

    Returns:
        The critique's length, in words.
    """

    return comment.count_words(comment.markup_to_text(crit.body))


def to_row(block: comment.Comment, crit: comment.Comment) -> database.Row:
    """
    Compose a database row from block and critique attributes.

    Args:
        block: The critique block to analyze.
        crit: The critique to analyze.

    Returns:
        A database row composed of select block and critique
            attributes.
    """

    row = database.Row(
        crit_posted_at = database.format_timestamp(crit.posted_at),
        crit_edited_at = database.format_timestamp(crit.edited_at),
        crit_author = crit.author,
        crit_words = crit.words,
        block_posted_at = database.format_timestamp(block.posted_at),
        block_edited_at = database.format_timestamp(block.edited_at),
        crit_url = comment.assemble_url(crit.belongs_to, crit.type_id, crit.id),
        block_url = comment.assemble_url(block.belongs_to, block.type_id, block.id)
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
    except FileNotFoundError:
        # Fall-through.
        pass
    except OSError as exception:
        # Let's not get scared if there are problems loading the
        # report.
        print_warn(f"{exception}.\n")
    else:
        with infile:
            data = database.load(infile)

    # We don't care about replies, only top-level comments.
    depth = 0

    # Any error here is fatal, so let's use one try...except only.
    try:
        for block in comment.yield_all(journal_id, journal_type, depth):
            block_url = comment.assemble_url(block.belongs_to, block.type_id, block.id)

            print(f"Analyzing {block_url}...")

            for url in comment.extract_comment_urls(block.body):
                crit = fetch_critique(url)

                if crit is None:
                    # Skip impossible edge cases.
                    print_warn(f"critique {url} does not exist.")
                    continue

                if crit.author != block.author:
                    print_warn(f"participant {block.author} doesn't match {crit.author}.")
                    continue

                data.append(to_row(block, crit))
    except (comment.FetchingError, ValueError) as exception:
        exit_fatal(f"{exception}.")

    try:
        outfile = report.open("w", newline="")
    except OSError as exception:
        exit_fatal(f"{exception}.")
    else:
        with outfile:
            database.dump(data, outfile)


def wrapper() -> None:
    """
    Entry point for critchecker.
    """

    try:
        main(**vars(read_args()))
    except KeyboardInterrupt:
        # Gracefully abort.
        print("\rInterrupted by user.")
