""" Functions and dataclasses that handle Critmas reports. """

import csv
import dataclasses
import datetime
import typing


@dataclasses.dataclass
class Row():  # pylint: disable=too-many-instance-attributes
    """
    A single row in a Critmas report.

    Args:
        crit_parent_id: The parent deviation's ID.
        crit_parent_type: The parent deviation's type ID.
        crit_id: The critique's ID.
        crit_posted_at: The critique's timestamp.
        crit_edited_at: The critique's edited timestamp, if any.
        crit_author: The critique's author.
        crit_words: The critique's length in words.
        crit_url: The critique's URL.
    """

    # pylint: disable=unsubscriptable-object

    crit_posted_at: str = None
    crit_edited_at: typing.Optional[str] = None
    crit_author: str = None
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


def format_timestamp(timestamp: str) -> str:
    """
    Truncate and format a timestamp.

    Args:
        timestamp: The timestamp to format.

    Returns:
        The formatted timestamp.

    Raises:
        ValueError: If the timestamp is malformed.
    """

    if timestamp is None:
        return ""

    try:
        as_datetime = datetime.datetime.strptime(
            timestamp[:-5],
            "%Y-%m-%dT%H:%M:%S"
        )
    except (ValueError, TypeError) as exception:
        raise ValueError(f"\"{timestamp}\": malformed timestamp") from exception

    return as_datetime.strftime("%m/%d/%Y %H:%M")


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
        raise ValueError(f"\"{url}\" not found in database rows") from exception

    return index
