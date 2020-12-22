""" Command-line interface for critchecker. """

import argparse


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
        "-d",
        "--database",
        type=str,
        help="the path to a CSV database created by critchecker"
    )

    return parser.parse_args()


def main(journal: str, database: str) -> None:
    """
    Core of crutchecker.

    Args:
        journal: The URL of the Critmas launch journal.
        database: The path to a CSV database created by critchecker.
    """


def wrapper() -> None:
    """
    Entry point for critchecker.
    """

    try:
        main(**vars(read_args()))
    except KeyboardInterrupt:
        # Gracefully abort.
        print("\rInterrupted by user.")
