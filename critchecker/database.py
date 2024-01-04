""" Functions and dataclasses that handle Critmas reports. """

import csv
import dataclasses
import typing


@dataclasses.dataclass
class Row:
    """
    A single row in a Critmas report.

    Args:
        crit_tstamp: The critique's timestamp.
        crit_author: The critique's author.
        crit_words: Thw critique's length in words.
        crit_url: The critique's URL.
        block_url: The critique block's URL.
    """

    crit_tstamp: str = None
    crit_author: str = None
    crit_words: int = None
    crit_url: str = None
    block_url: str = None


def dump(database: list[Row], outfile: typing.TextIO) -> int:
    """
    Dump a Critmas database.

    Args:
        database: A list of Critmas database rows.
        outfile: A .write()-supporting file-like object.

    Returns:
        The number of written rows.
    """
    header = dataclasses.asdict(database[0]).keys()
    writer = csv.DictWriter(outfile, header)

    writer.writeheader()
    for row in database:
        writer.writerow(dataclasses.asdict(row))

    return len(database) + 1


def get_index_by_crit_url(url: str, data: list[Row]) -> int:
    """
    Find the index of a database row with a matching crit_url.

    Args:
        url: The crit_url to look for.
        data: The database to parse.

    Returns:
        The index of the row whose crit_url attribute matches url.

    Raises:
        ValueError: If no matching row is found.
    """
    try:
        index = next(index for index, row in enumerate(data) if row.crit_url == url)
    except StopIteration as exc:
        raise ValueError(f"'{url}' not found in database rows") from exc

    return index


def measure_stats(data: list[Row]) -> tuple[int, int, int]:
    """
    Obtain the total, valid and deleted critiques from a database.

    Args:
        data: The database to parse.

    Returns:
        A tuple containing the amount of total, valid and deleted
            critiques.

    Raises:
        ValueError: If the database contains invalid rows.
    """
    try:
        # Let's use a generator to avoid copying the whole database.
        deleted = sum((True for row in data if not row.crit_words))
    except AttributeError as exc:
        raise ValueError("invalid database") from exc

    total = len(data)
    valid = total - deleted

    return total, valid, deleted
