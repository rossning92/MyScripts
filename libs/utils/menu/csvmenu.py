import csv
from typing import List, Optional, OrderedDict

from ..menu import Menu
from .textinput import TextInput


def format_text(s: str) -> str:
    max_width = 16
    s = s.replace("\n", " ")
    return (s[: (max_width - 2)] + "..") if len(s) > max_width else s.ljust(max_width)


class _CsvData:
    def __init__(self, file: str) -> None:
        self._rows: List[List[str]] = []
        self._file = file

        with open(file, encoding="utf-8") as csvfile:
            reader = csv.reader(csvfile)
            for i, row in enumerate(reader):
                self._rows.append(row)

    def get_cell(self, row_index: int, name: str) -> str:
        col_index = self.get_header().index(name)
        return self._rows[row_index][col_index]

    def set_cell(self, row_index: int, name: str, value: str):
        col_index = self.get_header().index(name)
        self._rows[row_index][col_index] = value

    def get_row_list(self, row_index) -> List[str]:
        return self._rows[row_index]

    def get_row_dict(self, row_index: int) -> OrderedDict[str, str]:
        d: OrderedDict[str, str] = OrderedDict()
        for name, val in zip(self.get_header(), self._rows[row_index]):
            d[name] = val
        return d

    def get_row_count(self) -> int:
        return len(self._rows)

    def get_header(self) -> List[str]:
        return self._rows[0]

    def save(self):
        with open(self._file, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(self._rows)


class _Cell:
    def __init__(
        self,
        df: _CsvData,
        row_index: int,
        name: str,
        max_column_name_width: int,
    ) -> None:
        self.df = df
        self.row_index = row_index
        self.name = name
        self.max_column_name_width = max_column_name_width

    def __str__(self) -> str:
        cell_value = str(self.df.get_cell(self.row_index, self.name))
        lines = cell_value.splitlines()
        header = self.name.ljust(self.max_column_name_width, " ") + " : "
        indented_lines = "\n".join(
            ((" " * (self.max_column_name_width + 3)) + line if i > 0 else line)
            for i, line in enumerate(lines)
        )
        return header + indented_lines


class _Row:
    def __init__(self, df: _CsvData, row_index: int) -> None:
        self.df = df
        self.row_index = row_index

    def __str__(self) -> str:
        row = self.df.get_row_list(self.row_index)
        row_str = " ".join([x for x in map(str, row)])
        return row_str


class RowMenu(Menu[_Cell]):
    def __init__(self, df: _CsvData, row_index: int) -> None:
        self.df = df
        self.row_index = row_index
        self.selected_cell: Optional[_Cell] = None

        max_column_name_width = max(len(col) for col in df.get_header())

        self.cells = [
            _Cell(
                df=self.df,
                row_index=self.row_index,
                name=name,
                max_column_name_width=max_column_name_width,
            )
            for name, _ in df.get_row_dict(self.row_index).items()
        ]

        super().__init__(items=self.cells, wrap_text=True, prompt=f"row {row_index}")

    def on_enter_pressed(self):
        cell = self.get_selected_item()
        if cell is not None:
            value = self.df.get_cell(self.row_index, cell.name)
            new_value = TextInput(prompt=f"{cell.name} :", text=value).request_input()
            if new_value is not None and new_value != value:
                self.df.set_cell(self.row_index, cell.name, new_value)
                self.df.save()
                # If the header is changed, close the menu because the cell becomes invalid.
                if self.row_index == 0:
                    self.close()


class CsvMenu(Menu[_Row]):
    def __init__(self, csv_file: str, text: str = ""):
        self.df = _CsvData(csv_file)
        self.selected_val: Optional[str] = None

        rows: List[_Row] = []
        for row_index in range(self.df.get_row_count()):
            rows.append(_Row(df=self.df, row_index=row_index))
        super().__init__(items=rows, text=text)

    def on_enter_pressed(self):
        row = self.get_selected_item()
        if row is not None:
            menu = RowMenu(df=self.df, row_index=row.row_index)
            menu.exec()
            if menu.selected_cell is not None:
                val = self.df.get_cell(row.row_index, menu.selected_cell.name)
                self.selected_val = val
                self.close()

    def get_item_text(self, item: _Row) -> str:
        row = self.df.get_row_list(item.row_index)
        return " ".join([format_text(x) for x in map(str, row)])
