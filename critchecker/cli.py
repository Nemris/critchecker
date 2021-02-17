""" Command-line interface for critchecker. """

import argparse
import asyncio
import pathlib
import sys
import warnings

import tqdm.asyncio

from critchecker import comment
from critchecker import database
from critchecker import deviation
from critchecker import network


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
        help="the path and filename to save the CSV report as"
    )

    return parser.parse_args()


def exit_fatal(msg: str) -> None:
    """
    Print an error message to standard error and exit with code 1.

    Args:
        msg: The error message to print.
    """

    sys.exit(f"Fatal: {msg}")


def get_journal_metadata(journal: str) -> tuple[int, int]:
    """
    Extract the journal ID and type ID.

    Args:
        journal: The URL of the Critmas journal.

    Returns:
        A tuple containing the journal ID and type ID.

    Raises:
        ValueError: If the journal URL is malformed.
    """

    journal_id = deviation.extract_id(journal)
    journal_type = deviation.typeid_of(deviation.extract_category(journal))

    return (journal_id, journal_type)


async def fetch_blocks(
    journal_id: int,
    journal_type: int,
    session: network.Session
) -> list[comment.Comment]:
    """
    Fetch the critique blocks posted as comments to a launch journal.

    Valid critique blocks contain at least one link to a critique.

    Args:
        journal_id: The launch journal's ID.
        journal_type: The launch journal's type ID.
        session: A session to use for requesting data.

    Returns:
        The comments containing at least one link to another comment.

    Raises:
        comment.CommentError: If an error occurred while fetching the
            critique blocks.
    """

    depth = 0

    blocks = []
    progress_bar = tqdm.asyncio.tqdm(
        comment.fetch_pages(
            journal_id, journal_type, depth, session
        ),
        desc="Analyzing comment pages",
        unit="page"
    )
    async for page in progress_bar:
        for block in page.comments:
            if comment.extract_comment_urls(block.body):
                blocks.append(block)

    return blocks


def initialize_database(blocks: list[comment.Comment]) -> list[database.Row]:
    """
    Initialize the critique database with the blocks' available data.

    Args:
        blocks: The blocks containing critique links.

    Returns:
        The critique database populated with the available block data,
            without duplicate critiques.
    """

    data = []
    for block in blocks:
        for crit_url in comment.extract_comment_urls(block.body):
            try:
                database.get_index_by_crit_url(crit_url, data)
                continue
            except ValueError:
                # No duplicate critiques, fall-through.
                pass

            data.append(
                database.Row(
                    block_posted_at = database.format_timestamp(block.posted_at),
                    block_edited_at = database.format_timestamp(block.edited_at),
                    crit_url = crit_url,
                    block_url = block.url
                )
            )

    return data


def get_unique_deviation_ids(data: list[database.Row]) -> set[int]:
    """
    Obtain the unique deviation IDs stored in a critique database.

    Args:
        data: The critique database.

    Returns:
        The unique deviation IDs in the database.

    Raises:
        ValueError: If a critique URL is malformed.
    """

    return set((comment.extract_ids_from_url(row.crit_url)[1] for row in data))


async def map_deviation_to_artist(deviation_id: int, session: network.Session) -> dict[int, str]:
    """
    Asynchronously fetch the artist matching a deviation ID.

    Args:
        deviation_id: A deviation ID whose matching artist to fetch.
        session: A session to use for requesting data.

    Returns:
        A deviation artist mapped to a deviation ID.

    Raises:
        deviation.DeviationError: If an error occurred while fetxhing a
            deviation's metadata.
    """
    try:
        metadata = await deviation.fetch_metadata(deviation_id, session)
    except deviation.BadDeviationError:
        # The deviation is likely unavailable.
        return {deviation_id: ""}

    return {deviation_id: metadata.author}


async def fetch_artists(data: list[database.Row], session: network.Session) -> dict[int, str]:
    """
    Fetch the artist for every unique deviation in a critique database.

    Args:
        data: The critique database.
        session: A session to use for requesting data.

    Returns:
        A mapping between unique deviation IDs and artists.

    Raises:
        ValueError: If a critique URL is malformed.
        deviation.DeviationError: If an error occurred while fetching
            a deviation's metadata.
    """

    mapping = dict.fromkeys(get_unique_deviation_ids(data))

    tasks = []
    for deviation_id in mapping:
        tasks.append(
            asyncio.create_task(
                map_deviation_to_artist(deviation_id, session)
            )
        )

    progress_bar = tqdm.asyncio.tqdm.as_completed(
        tasks,
        desc="Fetching artists",
        unit="artist"
    )

    for task in progress_bar:
        mapping.update(await task)

    return mapping


async def fill_row(
    row: database.Row,
    mapping: dict[int, str],
    session: network.Session
) -> database.Row:
    """
    Fetch the critique data belonging to a database row and fill it.

    Args:
        row: An initialized database row.
        mapping: A mapping between unique deviation IDs and artists.
        session: A session to use for requesting data.

    Returns:
        The database row with the missing fields filled.

    Raises:
        comment.CommentError: If an error occurred while fetching the
            critique.
    """

    # Always fill the deviation artist beforehand.
    row.deviation_artist = mapping[comment.extract_ids_from_url(row.crit_url)[1]]

    try:
        critique = await comment.fetch(row.crit_url, session)
    except comment.NoSuchCommentError:
        # Probably a hidden critique - skip filling critique metadata.
        return row

    row.crit_posted_at = database.format_timestamp(critique.posted_at)
    row.crit_edited_at = database.format_timestamp(critique.edited_at)
    row.crit_author = critique.author
    row.crit_words = critique.words

    return row


async def fill_database(
    data: list[database.Row],
    mapping: dict[int, str],
    session: network.Session
) -> list[database.Row]:
    """
    Asynchronously fetch critiques and fill the critique database.

    Args:
        data: The critique database.
        mapping: A mapping between unique deviation IDs and artists.
        session: A session to use for requesting data.

    Returns:
        The filled critique database.

    Raises:
        comment.CommentError: If an error occurred while fetching a
            critique.
    """

    tasks = []
    for row in data:
        tasks.append(
            asyncio.create_task(
                fill_row(row, mapping, session)
            )
        )

    progress_bar = tqdm.asyncio.tqdm.as_completed(
        tasks,
        desc="Fetching critiques",
        unit="crit"
    )

    for task in progress_bar:
        row = await task

        if row in data:
            continue

        # Not possible to get exceptions here, so let's not look for
        # one.
        index = database.get_index_by_crit_url(row.crit_url, data)

        data[index] = row

    return data


def save_database(data: list[database.Row], path: pathlib.Path) -> None:
    """
    Save a list of rows to a critchecker CSV database.

    An existing CSV database will be overwritten.

    Args:
        data: The data to save.
        path: The path to a critchecker CSV database.

    Raises:
        OSError: If an error happens while writing the CSV database.
    """

    with path.open("w", newline="") as outfile:
        database.dump(data, outfile)


async def main(journal: str, report: pathlib.Path) -> None:
    """
    Core of critchecker.

    Args:
        journal: The URL of the Critmas launch journal.
        report: The path and filename to save the CSV report as.
    """

    try:
        journal_metadata = get_journal_metadata(journal)
    except ValueError as exception:
        exit_fatal(f"{exception}.")

    async with network.Session() as session:
        session.headers.update({"Accept-Encoding": "gzip"})

        try:
            blocks = await fetch_blocks(*journal_metadata, session)
        except comment.CommentError as exception:
            exit_fatal(f"{exception}.")

        data = initialize_database(blocks)

        try:
            mapping = await fetch_artists(data, session)
        except (ValueError, deviation.DeviationError) as exception:
            exit_fatal(f"{exception}.")

        try:
            data = await fill_database(data, mapping, session)
        except comment.CommentError as exception:
            exit_fatal(f"{exception}.")

    # Cosmetic newline.
    print()

    try:
        total_crits, valid_crits, deleted_crits = database.measure_stats(data)
    except ValueError as exception:
        # An error at this point means the database is garbage.
        exit_fatal(f"{exception}.")

    print(f"Total critiques:   {total_crits:>4}")
    print(f"Valid critiques:   {valid_crits:>4}")
    print(f"Deleted critiques: {deleted_crits:>4}")

    try:
        save_database(data, report)
    except OSError as exception:
        exit_fatal(f"{exception}.")


def wrapper() -> None:
    """
    Entry point for critchecker.
    """

    # Mute bs4 since it tends to be overzealous.
    warnings.filterwarnings("ignore", category=UserWarning, module="bs4")

    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(main(**vars(read_args())))
    except KeyboardInterrupt:
        # Gracefully abort and let the garbage collector handle the
        # loop.
        print("\r\nInterrupted by user.")
