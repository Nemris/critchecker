""" Command-line interface for critchecker. """

import argparse
import asyncio
from datetime import datetime
import itertools
import pathlib
import sys
import warnings

from bs4 import MarkupResemblesLocatorWarning
from tqdm.asyncio import tqdm

from critchecker.cache import Cache
from critchecker.client import Client, ClientError
from critchecker import comment
from critchecker.database import Database, Row
from critchecker.deviation import Deviation


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


async def fetch_blocks(journal: Deviation, client: Client) -> list[comment.Comment]:
    """
    Fetch the critique blocks posted as comments to a launch journal.

    Valid critique blocks contain at least one link to a critique.

    Args:
        journal: The launch journal.
        client: A client that interfaces with DeviantArt.

    Returns:
        The comments containing at least one link to another comment.

    Raises:
        comment.CommentError: If an error occurred while fetching the
            critique blocks.
    """
    # Fetch only top-level comments.
    depth = 0
    offset = 0

    pbar = tqdm(
        comment.fetch_pages(journal.id, journal.type_id, depth, offset, client),
        desc="Fetching journal comment pages",
        unit="page",
        leave=False,
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
    deviation_id: str, min_date: datetime, client: Client
) -> list[comment.Comment]:
    """
    Fetch comments younger than a specific datetime.

    Args:
        deviation_id: The deviation whose comments to fetch.
        min_date: Comments older than this will be ignored.
        client: A client that interfaces with DeviantArt.

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
    offset = 0

    comments = []
    async for page in comment.fetch_pages(deviation_id, dev_type, depth, offset, client):
        # TODO: fix naming.
        for comment_ in page.comments:
            if comment_.timestamp < min_date:
                return comments
            comments.append(comment_)

    return comments


async def cache_comments(
    deviation_ids: set[str], min_date: datetime, client: Client
) -> Cache:
    """
    Fetch and cache comments to specific deviations.

    Args:
        deviation_ids: The deviations whose comments to fetch.
        min_date: Comments older than this will be ignored.
        client: A client that interfaces with DeviantArt.

    Returns:
        A cache of comments to deviations.

    Raises:
        comment.CommentError: If an error occurred while fetching the
            comments.
    """
    tasks = {
        asyncio.create_task(fetch_comments(dev_id, min_date, client))
        for dev_id in deviation_ids
    }
    pbar = tqdm.as_completed(
        tasks, desc="Fetching deviation comments", unit="dev", leave=False
    )

    comments = []
    try:
        for coro in pbar:
            comments.append(await coro)
    except asyncio.CancelledError:
        # Cleanup.
        for task in tasks:
            task.cancel()
        raise

    return Cache.from_comments(itertools.chain.from_iterable(comments))


def populate_database(blocks: list[comment.Comment], cache: Cache) -> Database:
    """
    Prepare a Database from cached comment data.

    Args:
        blocks: Critique blocks to examine.
        cache: A cache of comments to deviations.

    Returns:
        A database of critique metadata.
    """
    data = []
    for block in blocks:
        for url in block.get_unique_comment_urls():
            row = Row(crit_url=str(url), block_url=str(block.url))

            # Enrich row with critique metadata, if available.
            entry = cache.find_comment_by_url(url)
            if entry:
                row.crit_tstamp = entry.timestamp.strftime("%Y-%m-%dT%H:%M:%S%z")
                row.crit_author = entry.author
                row.crit_words = entry.words

            data.append(row)

    return Database(data)


async def main(journal: str, start_date: datetime, report: pathlib.Path) -> None:
    """
    Core of critchecker.

    Args:
        journal: The URL of the Critmas launch journal.
        start_date: The Critmas start date, in PST time.
        report: The path and filename to save the CSV report as.
    """
    try:
        journal = Deviation(journal)
    except ValueError as exc:
        exit_fatal(f"{exc}.")

    try:
        client = await Client.new()
    except ClientError as exc:
        exit_fatal(f"{exc}.")

    async with client:
        try:
            blocks = await fetch_blocks(journal, client)
        except comment.CommentError as exc:
            exit_fatal(f"{exc}.")

        unique_deviations = get_unique_deviations(blocks, {journal.id})
        try:
            cache = await cache_comments(unique_deviations, start_date, client)
        except comment.CommentError as exc:
            exit_fatal(f"{exc}.")

    data = populate_database(blocks, cache)
    print(f"Total critiques:   {data.total_critiques:>4}")
    print(f"Valid critiques:   {data.valid_critiques:>4}")
    print(f"Deleted critiques: {data.deleted_critiques:>4}")

    try:
        with report.open("w", newline="") as outfile:
            data.dump(outfile)
    except OSError as exc:
        exit_fatal(f"{exc}.")


def wrapper() -> None:
    """
    Entry point for critchecker.
    """
    args = read_args()

    try:
        start_date = datetime.fromisoformat(f"{args.startdate}T00:00:00-0800")
    except ValueError:
        exit_fatal(f"{args.startdate!r}: invalid YYYY-MM-DD date.")

    # Mute bs4 since it tends to be overzealous.
    warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

    try:
        asyncio.run(main(args.journal, start_date, args.report))
    except KeyboardInterrupt:
        # Gracefully abort.
        pass
