""" Functions and dataclasses that handle Critmas reports. """

import csv
import dataclasses
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

    crit_parent_id: int
    crit_parent_type: int
    crit_id: int
    crit_posted_at: str
    crit_edited_at: typing.Optional[str]
    crit_author: str
    crit_words: int
    crit_url: str


def load(infile: typing.TextIO) -> list[Row]:
    """
    Load a Critmas database.

    Args:
        infile: A .read()-supporting file-like object pointing to a
            .csv database.

    Returns:
        A list of Critmas database rows.
    """

    return [Row(**row) for row in csv.DictReader(infile)]


def dump(database: list[Row], outfile: typing.TextIO) -> int:
    """
    Dump a Critmas database to a file.

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
