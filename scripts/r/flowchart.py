import os
import subprocess
import tempfile
from typing import List, Optional

from _shutil import shell_open
from utils.menu import Menu
from utils.menu.textinput import TextInput


class Node:
    def __init__(
        self, name: str, deps: Optional[List[str]] = None, parent: Optional[str] = None
    ) -> None:
        self.name = name
        self.deps: List[str] = deps if deps else []
        self.parent = parent

    def __str__(self) -> str:
        return self.name


class FlowChartMenu(Menu[Node]):
    def __init__(self):
        self.__nodes: List[Node] = []
        self.__cur_node: Optional[str] = None

        super().__init__(items=self.__nodes, cancellable=False)

        self.__nodes.append(Node(name="a", deps=["b", "c"]))
        self.__nodes.append(Node(name="b", deps=["c"]))
        self.__nodes.append(Node(name="c", deps=["a"]))

        self.add_command(
            lambda: self.call_func_without_curses(self.to_mermaid), hotkey="ctrl+e"
        )
        self.add_command(self.__add_node, hotkey="ctrl+n")
        self.add_command(self.__add_dep, hotkey="ctrl+d")

    def node_exists(self, name: str):
        for node in self.__nodes:
            if node.name == name:
                return True
        else:
            return False

    def __add_node(self):
        name = TextInput(
            prompt="new node>", items=[node.name for node in self.__nodes]
        ).request_input()
        if name:
            self.add_node(name=name)
        self.update_screen()

    def add_node(self, name: str):
        if not self.node_exists(name):
            self.__nodes.append(Node(name=name))

    def get_node(self, name: str) -> Node:
        for node in self.__nodes:
            if node.name == name:
                return node
        raise Exception(f"Cannot find node with name: {name}")

    def __add_dep(self):
        if self.__cur_node:
            name = TextInput(
                prompt=f"{self.__cur_node} -->",
                items=[node.name for node in self.__nodes],
            ).request_input()
            if name:
                self.add_node(name=name)
                self.get_node(self.__cur_node).deps.append(name)
        self.update_screen()

    def to_mermaid(self):
        s = "flowchart TB\n"
        for node in self.__nodes:
            s += f"  {node.name}\n"

        for node in self.__nodes:
            for dep in node.deps:
                s += f"  {node.name} --> {dep}\n"
        print(s)
        mermaid_file = os.path.join(tempfile.gettempdir(), "export.mmd")
        image_file = os.path.join(tempfile.gettempdir(), "export.svg")
        with open(mermaid_file, "w", encoding="utf-8") as f:
            f.write(s)
        subprocess.check_call(
            ["mmdc", "-i", mermaid_file, "-o", image_file], shell=True
        )
        shell_open(image_file)

    def on_enter_pressed(self):
        node = self.get_selected_item()
        if node is not None:
            self.__cur_node = node.name
            self.set_prompt(self.__cur_node)


if __name__ == "__main__":
    menu = FlowChartMenu()
    menu.exec()
