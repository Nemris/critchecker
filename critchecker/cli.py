""" Command-line interface for critchecker. """

import argparse
import asyncio
import datetime
import itertools
import pathlib
import sys
import warnings

from bs4 import MarkupResemblesLocatorWarning
import tqdm.asyncio

from critchecker import cache
from critchecker import client
from critchecker import comment
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
        help="the URL of the Critmas launch journal",
    )
    parser.add_argument(
        "startdate",
        type=str,
        help="the Critmas start date, in the format YYYY-MM-DD",
    )
    parser.add_argument(
        "-r",
        "--report",
        type=pathlib.Path,
        default=pathlib.Path.home().joinpath("critmas.csv"),
        help="the path and filename to save the CSV report as",
    )

    return parser.parse_args()


def exit_fatal(msg: str) -> None:
    """
    Print an error message to standard error and exit with code 1.

    Args:
        msg: The error message to print.
    """
    sys.exit(f"Fatal: {msg}")


async def fetch_blocks(
    journal: deviation.Deviation, da_client: client.Client
) -> list[comment.Comment]:
    """
    Fetch the critique blocks posted as comments to a launch journal.

    Valid critique blocks contain at least one link to a critique.

    Args:
        journal: The launch journal.
        da_client: A client that interfaces with DeviantArt.

    Returns:
        The comments containing at least one link to another comment.

    Raises:
        comment.CommentError: If an error occurred while fetching the
            critique blocks.
    """
    # Fetch only top-level comments.
    depth = 0

    pbar = tqdm.asyncio.tqdm(
        comment.fetch_pages(journal.id, journal.type_id, depth, da_client),
        desc="Fetching journal comment pages",
        unit="page",
    )

    blocks = []
    async for page in pbar:
        for block in page.comments:
            if block.get_unique_comment_urls():
                blocks.append(block)

    return blocks


def get_unique_deviations(
    blocks: list[comment.Comment], ignored_ids: set[str]
) -> set[str]:
    """
    Get the unique deviations referenced by critiques.

    Args:
        blocks: Critique blocks to examine.
        ignored_ids: Deviation IDs to ignore.

    Returns:
        The unique IDs of the deviations referenced by critiques.
    """
    return {
        url.deviation_id
        for block in blocks
        for url in block.get_unique_comment_urls()
        if url.deviation_id not in ignored_ids
    }


async def fetch_comments(
    deviation_id: str, min_date: datetime.datetime, da_client: client.Client
) -> list[comment.Comment]:
    """
    Fetch comments younger than a specific datetime.

    Args:
        deviation_id: The deviation whose comments to fetch.
        min_date: Comments older than this will be ignored.
        da_client: A client that interfaces with DeviantArt.

    Returns:
        The comments to a deviation that are more recent than the
            specified datetime.

    Raises:
        comment.CommentError: If an error occurred while fetching the
            comments.
    """
    # We're interested only in art, and only in top-level comments.
    dev_type = 1
    depth = 0

    comments = []
    async for page in comment.fetch_pages(deviation_id, dev_type, depth, da_client):
        # TODO: fix naming.
        for comment_ in page.comments:
            if comment_.timestamp < min_date:
                return comments
            comments.append(comment_)

    return comments


async def cache_comments(
    deviation_ids: set[str], min_date: datetime.datetime, da_client: client.Client
) -> cache.Cache:
    """
    Fetch and cache comments to specific deviations.

    Args:
        deviation_ids: The deviations whose comments to fetch.
        min_date: Comments older than this will be ignored.
        da_client: A client that interfaces with DeviantArt.

    Returns:
        A mapping between deviation IDs and their comments.

    Raises:
        comment.CommentError: If an error occurred while fetching the
            comments.
    """
    coros = [fetch_comments(dev_id, min_date, da_client) for dev_id in deviation_ids]
    pbar = tqdm.asyncio.tqdm.gather(
        *coros, desc="Fetching deviation comments", unit="deviation"
    )

    # .gather() returns an iterable of results - flatten it.
    mapping = cache.Cache.from_comments(itertools.chain.from_iterable(await pbar))

    return mapping


def rows_from_cache(
    blocks: list[comment.Comment], mapping: cache.Cache
) -> list[database.Row]:
    """
    Prepare database rows from cached comment data.

    Args:
        blocks: Critique blocks to examine.
        mapping: A mapping between unique deviations and their
            comments.

    Returns:
        A list of rows, enriched with critique metadata if available.
    """
    data = []
    for block in blocks:
        for url in block.get_unique_comment_urls():
            row = database.Row(crit_url=str(url), block_url=str(block.url))

            # Enrich row with critique metadata, if available.
            entry = mapping.find_comment_by_url(url)
            if entry:
                row.crit_tstamp = entry.timestamp.strftime("%Y-%m-%dT%H:%M:%S%z")
                row.crit_author = entry.author
                row.crit_words = entry.words

            data.append(row)

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


async def main(
    journal: str, start_date: datetime.datetime, report: pathlib.Path
) -> None:
    """
    Core of critchecker.

    Args:
        journal: The URL of the Critmas launch journal.
        start_date: The Critmas start date, in PST time.
        report: The path and filename to save the CSV report as.
    """
    try:
        journal = deviation.Deviation(journal)
    except ValueError as exc:
        exit_fatal(f"{exc}.")

    try:
        da_client = await client.Client.new()
    except client.ClientError as exc:
        exit_fatal(f"{exc}.")

    async with da_client:
        try:
            blocks = await fetch_blocks(journal, da_client)
        except comment.CommentError as exc:
            exit_fatal(f"{exc}.")

        unique_deviations = get_unique_deviations(blocks, {journal.id})
        try:
            mapping = await cache_comments(unique_deviations, start_date, da_client)
        except comment.CommentError as exc:
            exit_fatal(f"{exc}.")

    data = rows_from_cache(blocks, mapping)

    # Cosmetic newline.
    print()

    try:
        total_crits, valid_crits, deleted_crits = database.measure_stats(data)
    except ValueError as exc:
        # An error at this point means the database is garbage.
        exit_fatal(f"{exc}.")

    print(f"Total critiques:   {total_crits:>4}")
    print(f"Valid critiques:   {valid_crits:>4}")
    print(f"Deleted critiques: {deleted_crits:>4}")

    try:
        save_database(data, report)
    except OSError as exc:
        exit_fatal(f"{exc}.")


def wrapper() -> None:
    """
    Entry point for critchecker.
    """
    args = read_args()

    try:
        start_date = datetime.datetime.fromisoformat(f"{args.startdate}T00:00:00-0800")
    except ValueError:
        exit_fatal(f"{args.startdate!r}: invalid YYYY-MM-DD date.")

    # Mute bs4 since it tends to be overzealous.
    warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

    loop = asyncio.get_event_loop()

    try:
        loop.run_until_complete(main(args.journal, start_date, args.report))
    except KeyboardInterrupt:
        # Gracefully abort and let the garbage collector handle the
        # loop.
        print("\r\nInterrupted by user.")
