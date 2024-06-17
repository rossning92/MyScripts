from typing import List, Optional

import pandas as pd

from ..menu import Menu


def format_text(s: str) -> str:
    max_width = 16
    return (s[: (max_width - 2)] + "..") if len(s) > max_width else s.ljust(max_width)


class _Cell:
    def __init__(
        self,
        df: pd.DataFrame,
        row_index: int,
        name: str,
        max_column_name_width: int,
    ) -> None:
        self.df = df
        self.row_index = row_index
        self.name = name
        self.max_column_name_width = max_column_name_width

    def __str__(self) -> str:
        return (
            self.name.ljust(self.max_column_name_width, " ")
            + " : "
            + str(self.df.iloc[self.row_index][self.name])
        )


class _Row:
    def __init__(self, df: pd.DataFrame, row_index: int) -> None:
        self.df = df
        self.row_index = row_index

    def __str__(self) -> str:
        row = self.df.iloc[self.row_index].values.tolist()
        row_str = " ".join([x for x in map(str, row)])
        return row_str


class RowMenu(Menu[_Cell]):
    def __init__(self, df: pd.DataFrame, row_index: int) -> None:
        self.df = df
        self.row_index = row_index
        self.selected_cell: Optional[_Cell] = None

        max_column_name_width = max(len(col) for col in df.columns)

        self.cells = [
            _Cell(
                df=self.df,
                row_index=self.row_index,
                name=name,
                max_column_name_width=max_column_name_width,
            )
            for name, _ in df.iloc[self.row_index].items()
        ]

        super().__init__(items=self.cells, wrap_text=True, prompt=f"row {row_index}")

    def on_enter_pressed(self):
        cell = self.get_selected_item()
        if cell is not None:
            self.selected_cell = cell
            self.close()


class CsvMenu(Menu[_Row]):
    def __init__(self, csv_file: str, text: str = ""):
        self.df = pd.read_csv(csv_file, header=0, index_col=None)
        self.selected_val: Optional[str] = None

        rows: List[_Row] = []
        for row_index in range(len(self.df)):
            rows.append(_Row(df=self.df, row_index=row_index))
        super().__init__(items=rows, text=text)

    def on_enter_pressed(self):
        row = self.get_selected_item()
        if row is not None:
            menu = RowMenu(df=self.df, row_index=row.row_index)
            menu.exec()
            if menu.selected_cell is not None:
                val = self.df.iloc[row.row_index][menu.selected_cell.name]
                self.selected_val = val
                self.close()

    def get_item_text(self, item: _Row) -> str:
        row = self.df.iloc[item.row_index].values.tolist()
        return " ".join([format_text(x) for x in map(str, row)])
