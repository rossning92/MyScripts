import csv
from typing import List

from ..menu import Menu


class _Item:
    def __init__(self, columns, column_width: List[int]) -> None:
        self.columns = columns
        self.column_width = column_width

    def __str__(self) -> str:
        return " ".join(
            [
                x[: self.column_width[i]].ljust(self.column_width[i])
                if i < len(self.columns) - 1
                else x
                for i, x in enumerate(self.columns)
            ]
        )


class CsvMenu(Menu[_Item]):
    def __init__(self, csv_file: str, text: str = ""):
        items: List[_Item] = []
        column_width: List[int] = []

        with open(csv_file, encoding="utf-8") as csvfile:
            spamreader = csv.reader(csvfile)
            for i, row in enumerate(spamreader):
                for j, s in enumerate(row):
                    if j >= len(items):
                        column_width.append(0)
                    column_width[j] = max(column_width[j], len(s))

                if i > 0:
                    items.append(_Item(row, column_width=column_width))

        super().__init__(items=items, close_on_selection=True, text=text)
