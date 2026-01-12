"""Command-line interface for critchecker."""

import argparse
import asyncio
from collections.abc import Callable
from datetime import datetime
import itertools
import pathlib
import sys

from sundown import client
from sundown import comment
from sundown import deviation
from tqdm.asyncio import tqdm

from critchecker.critique import Batch
from critchecker.database import Database, Row


Cache = dict[str, comment.Comment]


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
        help="URL of the Critmas launch journal",
    )
    parser.add_argument(
        "startdate",
        type=str,
        help="Critmas start date, in the format YYYY-MM-DD",
    )
    parser.add_argument(
        "-r",
        "--report",
        type=pathlib.Path,
        default=pathlib.Path.home().joinpath("critmas.csv"),
        help="path and filename to save the CSV report as",
    )
    parser.add_argument(
        "-s",
        "--scan-text",
        action="store_true",
        help="scan comment bodies to potentially retrieve more critiques",
    )

    return parser.parse_args()


def exit_fatal(msg: str) -> None:
    """
    Print an error message to standard error and exit with code 1.

    Args:
        msg: The error message to print.
    """
    sys.exit(f"Fatal: {msg}")


def identify_critique_batches(
    comments: list[comment.Comment], scan_text: bool
) -> list[Batch]:
    """
    Find the journal comments that contain critique links.

    Args:
        comments: The comments to a launch journal.
        scan_text: If True, scan each comment's text for links. Else,
            check only the link data sent by DeviantArt in the bodies.

    Returns:
        Batches mapping a journal comment URL to critique links found
            in the comment.
    """
    batches = []
    for c in comments:
        urls = {u for u in c.body.urls if comment.URL_PATTERN.search(u)}
        if scan_text:
            urls.update({m.group(0) for m in comment.URL_PATTERN.finditer(c.body.text)})

        if urls:
            batches.append(
                Batch(c.metadata.url, [comment.URL.from_str(u) for u in urls])
            )

    return batches


def get_unique_deviations(batches: list[Batch], ignored_ids: set[str]) -> set[str]:
    """
    Get the unique deviations referenced by critiques.

    Args:
        batches: Critique batches to examine.
        ignored_ids: Deviation IDs to ignore.

    Returns:
        The unique IDs of the deviations referenced by critiques.
    """
    return {
        url.deviation.id
        for batch in batches
        for url in batch.crit_urls
        if url.deviation.id not in ignored_ids
    }


async def fetch_comments(
    dev: deviation.Deviation | deviation.PartialDeviation,
    client_: client.Client,
    keep_downloading: Callable[[comment.Comment], bool],
) -> list[comment.Comment]:
    """
    Fetch comments to a deviation until a condition occurs.

    Args:
        dev: The deviation whose comments to fetch.
        client_: A client that interfaces with DeviantArt.
        keep_downloading: A function executed for each comment, which
            returns True to keep downloading or False to stop.

    Returns:
        The comments to a deviation.

    Raises:
        client.Error: If an error occurred while fetching comments.
        comment.Error: If an error occurred while parsing comment data.
    """
    comments = []
    async for page in comment.PageIterator(client_, dev, 0, 50):
        for c in page:
            if not keep_downloading(c):
                return comments
            comments.append(c)

    return comments


async def cache_comments(
    deviation_ids: set[str], min_date: datetime, client_: client.Client
) -> Cache:
    """
    Fetch and cache comments to specific deviations.

    Args:
        deviation_ids: The deviations whose comments to fetch.
        min_date: Comments older than this will be ignored.
        client_: A client that interfaces with DeviantArt.

    Returns:
        A cache of comments to deviations.

    Raises:
        client.Error: If an error occurred while fetching comments.
        comment.Error: If an error occurred while parsing comment data.
    """
    tasks = set()
    for id_ in deviation_ids:
        d = deviation.PartialDeviation(deviation.Kind.ART, id_)
        t = asyncio.create_task(
            fetch_comments(d, client_, lambda c: c.metadata.posted >= min_date)
        )
        tasks.add(t)

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

    return {c.metadata.id: c for c in itertools.chain.from_iterable(comments)}


def populate_database(batches: list[Batch], cache: Cache) -> Database:
    """
    Prepare a Database from cached comment data.

    Args:
        batches: Critique batches to examine.
        cache: A cache of comments to deviations.

    Returns:
        A database of critique metadata.
    """
    data = []
    for batch in batches:
        for url in batch.crit_urls:
            row = Row(crit_url=str(url), batch_url=str(batch.url))

            # Enrich row with critique metadata, if available.
            if entry := cache.get(url.comment_id):
                row.crit_tstamp = entry.metadata.posted.strftime("%Y-%m-%dT%H:%M:%S%z")
                row.crit_author = entry.metadata.author
                row.crit_words = entry.body.words

            data.append(row)

    return Database(data)


async def main(args: argparse.Namespace) -> None:
    """
    Core of critchecker.

    Args:
        args: Command-line arguments.
    """
    try:
        journal = deviation.Deviation.from_url(args.journal)
    except ValueError as exc:
        exit_fatal(f"{exc}.")

    async with client.Client() as client_:
        print("Fetching journal comments...")
        try:
            comments = await fetch_comments(journal, client_, lambda c: True)
        except (client.Error, comment.Error) as exc:
            exit_fatal(f"{exc}.")

        batches = identify_critique_batches(comments, args.scan_text)
        unique_deviations = get_unique_deviations(batches, {journal.id})

        try:
            cache = await cache_comments(unique_deviations, args.startdate, client_)
        except (client.Error, comment.Error) as exc:
            exit_fatal(f"{exc}.")

    data = populate_database(batches, cache)
    data.deduplicate()
    print(f"Total critiques:   {data.total_critiques:>4}")
    print(f"Valid critiques:   {data.valid_critiques:>4}")
    print(f"Deleted critiques: {data.deleted_critiques:>4}")

    try:
        with args.report.open("w", newline="") as outfile:
            data.dump(outfile)
    except (ValueError, OSError) as exc:
        exit_fatal(f"{exc}.")


def wrapper() -> None:
    """
    Entry point for critchecker.
    """
    args = read_args()

    try:
        args.startdate = datetime.fromisoformat(f"{args.startdate}T00:00:00-0800")
    except ValueError:
        exit_fatal(f"{args.startdate!r}: invalid YYYY-MM-DD date.")

    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        # Gracefully abort.
        pass
