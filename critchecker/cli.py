""" Command-line interface for critchecker. """

import argparse
import pathlib
import sys

from critchecker import database
from critchecker import deviation


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
        print_warn(f"{exception}.")
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
