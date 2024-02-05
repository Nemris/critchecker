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
