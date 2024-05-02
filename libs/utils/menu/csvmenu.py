import csv
from typing import List

from ..menu import Menu


class _Item:
    def __init__(self, columns) -> None:
        self.columns = columns

    def __str__(self) -> str:
        return " , ".join(self.columns)


class CsvMenu(Menu[_Item]):
    def __init__(self, csv_file: str, text: str = ""):
        items: List[_Item] = []

        with open(csv_file, encoding="utf-8") as csvfile:
            spamreader = csv.reader(csvfile)
            for i, row in enumerate(spamreader):
                if i > 0:
                    items.append(_Item(row))

        super().__init__(items=items, close_on_selection=True, text=text)
