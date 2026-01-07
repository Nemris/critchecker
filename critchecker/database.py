"""Functions and dataclasses that handle Critmas reports."""

import csv
import dataclasses
from typing import TextIO


@dataclasses.dataclass
class Row:
    """
    A single row in a Critmas report.

    Args:
        crit_tstamp: The critique's timestamp.
        crit_author: The critique's author.
        crit_words: The critique's length in words.
        crit_url: The critique's URL.
        batch_url: The critique batch's URL.
    """

    crit_tstamp: str = None
    crit_author: str = None
    crit_words: int = None
    crit_url: str = None
    batch_url: str = None


@dataclasses.dataclass
class Database:
    """
    A database that stores critique metadata in rows.

    Args:
        rows: Rows containing critique metadata.
    """

    rows: list[Row]

    def deduplicate(self) -> None:
        """
        Deduplicates self using critique URLs as keys.
        """
        deduped = {row.crit_url: row for row in self.rows}
        self.rows = list(deduped.values())

    def dump(self, outfile: TextIO) -> int:
        """
        Dump self to a text stream.

        Args:
            outfile: A text stream that supports .write().

        Returns:
            The number of written rows.
        """
        header = dataclasses.asdict(self.rows[0]).keys()
        writer = csv.DictWriter(outfile, header)

        writer.writeheader()
        for row in self.rows:
            writer.writerow(dataclasses.asdict(row))

        return len(self.rows) + 1

    @property
    def total_critiques(self) -> int:
        """Total amount of critiques in the database."""
        return len(self.rows)

    @property
    def valid_critiques(self) -> int:
        """Valid critiques in the database."""
        return sum(True for row in self.rows if row.crit_words)

    @property
    def deleted_critiques(self) -> int:
        """Deleted critiques in the database."""
        return self.total_critiques - self.valid_critiques
