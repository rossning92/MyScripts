import csv
from typing import List, Optional, OrderedDict

from utils.editor import edit_text

from ..menu import Menu
from .textinput import TextInput

COLUMN_WIDTH = 16
COLUMN_SEPARATOR = " "


def format_text(s: str) -> str:
    max_width = COLUMN_WIDTH
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

    def get_header(self) -> List[str]:
        return self._rows[0]

    def sort_by_column(self, name: str, desc=False):
        header = self.get_header()
        idx = header.index(name)
        self._rows[1:] = sorted(self._rows[1:], key=lambda x: x[idx], reverse=desc)

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

    def save(self):
        with open(self._file, mode="w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerows(self._rows)

    def add_row(
        self, values: Optional[List[str]] = None, index: Optional[int] = None
    ) -> int:
        num_columns = len(self.get_header())
        if values is None:
            values = [""] * num_columns
        elif len(values) != num_columns:
            raise Exception(f"{num_columns} elements are required based on the header.")

        if index is None:
            index = len(self._rows)
        self._rows.insert(index, values)
        return index

    def delete_row(self, row_index: int) -> None:
        if row_index < 0 or row_index >= len(self._rows):
            raise IndexError(f"Row index {row_index} out of bounds.")

        del self._rows[row_index]


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

        self.cells: List[_Cell] = []
        self._initialize_cells()

        super().__init__(items=self.cells, wrap_text=True, prompt=f"row {row_index}")

        self.add_command(
            lambda: self.call_func_without_curses(
                lambda: self.edit_cell(external_editor=True)
            ),
            hotkey="ctrl+e",
            name="edit_cell_in_editor",
        )
        self.add_command(
            self._prev_row,
            hotkey="left",
        )
        self.add_command(
            self._next_row,
            hotkey="right",
        )

    def _goto_row(self, row_index: int):
        self.row_index = row_index
        self.set_prompt(f"row {row_index}")
        self._initialize_cells()
        self.update_screen()

    def _prev_row(self):
        self._goto_row(max(self.row_index - 1, 0))

    def _next_row(self):
        self._goto_row(min(self.row_index + 1, self.df.get_row_count() - 1))

    def _initialize_cells(self):
        max_column_name_width = max(len(col) for col in self.df.get_header())
        self.cells[:] = [
            _Cell(
                df=self.df,
                row_index=self.row_index,
                name=name,
                max_column_name_width=max_column_name_width,
            )
            for name, _ in self.df.get_row_dict(self.row_index).items()
        ]

    def on_enter_pressed(self):
        self.edit_cell()

    def edit_cell(self, external_editor=False):
        cell = self.get_selected_item()
        if cell is not None:
            value = self.df.get_cell(self.row_index, cell.name)

            if external_editor:
                new_value = edit_text(text=value).rstrip()
            else:
                new_value = TextInput(
                    prompt=f"Edit {cell.name} :", text=value
                ).request_input()

            if new_value is not None and new_value != value:
                self.df.set_cell(self.row_index, cell.name, new_value)
                self.df.save()
                # If the header is changed, close the menu because the cell becomes invalid.
                if self.row_index == 0:
                    self.close()
                self.update_screen()


class CsvMenu(Menu[_Row]):
    def __init__(self, csv_file: str, text: str = ""):
        self.df = _CsvData(csv_file)
        self.selected_val: Optional[str] = None

        self._rows: List[_Row] = []
        self._update_rows()

        super().__init__(items=self._rows, text=text, prompt="filter row :")

        self.add_command(self._add_row, hotkey="alt+n")
        self.add_command(self._delete_row, hotkey="alt+d")
        self.add_command(self._save, hotkey="ctrl+s")
        self.add_command(self._sort_by_column, hotkey="alt+s")

    def _sort_by_column(self):
        menu = Menu(items=self.df.get_header(), prompt="sort by :")
        menu.exec()
        name = menu.get_selected_item()
        if name is not None:
            self.df.sort_by_column(name=name)
            self.update_screen()

    def _save(self):
        self.df.save()
        self.set_message("saved")

    def _update_rows(self):
        self._rows.clear()
        for row_index in range(self.df.get_row_count()):
            self._rows.append(_Row(df=self.df, row_index=row_index))

    def on_enter_pressed(self):
        row = self.get_selected_item()
        if row is not None:
            self._edit_row(row_index=row.row_index)

    def get_scroll_distance(self) -> int:
        return COLUMN_WIDTH + len(COLUMN_SEPARATOR)

    def _edit_row(self, row_index: int):
        menu = RowMenu(df=self.df, row_index=row_index)
        menu.exec()
        if menu.selected_cell is not None:
            val = self.df.get_cell(row_index, menu.selected_cell.name)
            self.selected_val = val
            self.close()

    def get_item_text(self, item: _Row) -> str:
        row = self.df.get_row_list(item.row_index)
        return COLUMN_SEPARATOR.join(
            [
                format_text(text) if i < len(row) - 1 else text
                for i, text in enumerate(map(str, row))
            ]
        )

    def _add_row(self):
        row_index = self.df.add_row()
        self._update_rows()
        self._edit_row(row_index=row_index)
        self.set_selected_row(row_index)

    def _delete_row(self):
        row = self.get_selected_item()
        if row is not None:
            self.df.delete_row(row_index=row.row_index)
            self._update_rows()
