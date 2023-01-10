""" Functions and dataclasses that handle Critmas reports. """

import csv
import dataclasses
import typing


@dataclasses.dataclass
class Row():  # pylint: disable=too-many-instance-attributes
    """
    A single row in a Critmas report.

    Args:
        crit_posted_at: The critique's timestamp.
        crit_edited_at: The critique's edited timestamp, if any.
        crit_author: The critique's author.
        deviation_artist: The author of the critiqued deviation.
        crit_words: Thw critique's length in words.
        block_posted_at: The critique block's timestamp.
        block_edited_at: The critique block's edited timestamp, if any.
        crit_url: The critique's URL.
        block_url: The critique block's URL.
    """

    # pylint: disable=unsubscriptable-object

    crit_posted_at: str = None
    crit_edited_at: typing.Optional[str] = None
    crit_author: str = None
    deviation_artist: str = None
    crit_words: int = 0
    block_posted_at: str = None
    block_edited_at: typing.Optional[str] = None
    crit_url: str = None
    block_url: str = None

    def __post_init__(self) -> None:
        """
        Convert the instance attributes expected to be int.

        Raises:
            ValueError: If converting to int fails.
        """

        self.crit_words = int(self.crit_words)


def load(infile: typing.TextIO) -> list[Row]:
    """
    Load a Critmas database.

    Args:
        infile: A .read()-supporting file-like object containing a
            CSV document.

    Returns:
        A list of Critmas database rows.
    """

    return [Row(**row) for row in csv.DictReader(infile)]


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
    written = 0

    writer.writeheader()
    written += 1

    for row in database:
        writer.writerow(dataclasses.asdict(row))
        written += 1

    return written


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
    except StopIteration as exception:
        raise ValueError(f"'{url}' not found in database rows") from exception

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
        deleted = sum((True for row in data if row.crit_words == 0))
    except AttributeError as exception:
        raise ValueError("invalid database") from exception

    total = len(data)
    valid = total - deleted

    return total, valid, deleted
