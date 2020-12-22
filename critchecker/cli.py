""" Command-line interface for critchecker. """

import argparse
import pathlib
import sys

from critchecker import database


def read_args() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Returns:
        The parsed command-line arguments.
    """

    parser = argparse.ArgumentParser(
        description="Extract and measure the length of DeviantART Critnas critiques."
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


def main(journal: str, report: pathlib.Path) -> None:
    """
    Core of critchecker.

    Args:
        journal: The URL of the Critmas launch journal.
        database: The path to a CSV report created by critchecker.
    """

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
