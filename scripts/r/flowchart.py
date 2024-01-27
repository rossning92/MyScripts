import os
import subprocess
import sys
import tempfile
from typing import Iterator, List, Optional

from _shutil import load_json, save_json, shell_open
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
    def __init__(self, file: str):
        self.__file = file
        self.__nodes: List[Node] = []
        self.__cur_node: Optional[str] = None

        super().__init__(items=self.__nodes, cancellable=False)

        self.add_command(
            lambda: self.call_func_without_curses(self.__export_to_mermaid),
            hotkey="ctrl+e",
        )
        self.add_command(self.__add_node_from, hotkey="ctrl+f")
        self.add_command(self.__add_node_to, hotkey="ctrl+t")
        self.add_command(self.__add_node, hotkey="ctrl+n")
        self.add_command(self.__load, hotkey="ctrl+s")
        self.add_command(self.__rename_node, hotkey="alt+n")

        self.__load()

    def node_exists(self, name: str):
        for node in self.__nodes:
            if node.name == name:
                return True
        else:
            return False

    def __add_node(self):
        name = TextInput(
            prompt=f"{self.__cur_node} ::", items=[node.name for node in self.__nodes]
        ).request_input()
        if name:
            self.add_node(name=name)
            self.get_node(name=name).parent = self.__cur_node

        self.__save()
        self.update_screen()

    def add_node(self, name: str):
        if not self.node_exists(name):
            self.__nodes.append(Node(name=name))

    def get_node(self, name: str) -> Node:
        for node in self.__nodes:
            if node.name == name:
                return node
        raise Exception(f"Cannot find node with name: {name}")

    def get_children(self, name: Optional[str]) -> Iterator[Node]:
        for node in self.__nodes:
            if node.parent == name:
                yield node

    def __add_node_to(self):
        if self.__cur_node:
            name = TextInput(
                prompt=f"{self.__cur_node} -->",
                items=[node.name for node in self.__nodes],
            ).request_input()
            if name:
                self.add_node(name=name)
                self.get_node(self.__cur_node).deps.append(name)

        self.__save()
        self.update_screen()

    def __add_node_from(self):
        if self.__cur_node:
            name = TextInput(
                prompt=f"{self.__cur_node} <--",
                items=[node.name for node in self.__nodes],
            ).request_input()
            if name:
                self.add_node(name=name)
                self.get_node(name=name).deps.append(self.__cur_node)

        self.__save()
        self.update_screen()

    def __export_to_mermaid(self):
        s = "flowchart TB\n"

        def render_nodes(nodes: List[Node], indent: str):
            nonlocal s
            for node in nodes:
                children = list(self.get_children(node.name))
                if not children:
                    s += indent + f"{node.name}\n"
                else:
                    s += indent + f"subgraph {node.name}\n"
                    render_nodes(children, indent + "  ")
                    s += indent + "end\n"

        render_nodes(list(self.get_children(None)), "  ")

        def render_dep():
            nonlocal s
            for node in self.__nodes:
                for dep in node.deps:
                    s += f"  {node.name} --> {dep}\n"

        render_dep()
        print(s)

        mermaid_file = os.path.join(tempfile.gettempdir(), "export.mmd")
        image_file = os.path.join(tempfile.gettempdir(), "export.svg")
        with open(mermaid_file, "w", encoding="utf-8") as f:
            f.write(s)
        subprocess.check_call(
            ["mmdc", "-i", mermaid_file, "-o", image_file],
            shell=sys.platform == "win32",
        )
        shell_open(image_file)

    def on_enter_pressed(self):
        node = self.get_selected_item()
        if node is not None:
            self.__set_cur_node(node.name)

    def on_escape_pressed(self):
        self.__set_cur_node(None)

    def __set_cur_node(self, name: Optional[str]):
        self.__cur_node = name
        self.set_prompt(name if name else "")

    def __save(self):
        save_json(file=self.__file, data=[x.__dict__ for x in self.__nodes])

    def __load(self):
        self.__nodes.clear()
        arr = load_json(file=self.__file, default=[])
        for item in arr:
            node = Node(name=item["name"])
            node.__dict__ = item
            self.__nodes.append(node)

    def __rename_node(self):
        node = self.get_selected_item()
        if not node:
            return
        old_name = node.name

        new_name = TextInput(prompt=f"rename {old_name}>").request_input()
        if not new_name:
            return

        for node in self.__nodes:
            if node.name == old_name:
                node.name = new_name
            if node.parent == old_name:
                node.parent = new_name
            for i, dep in enumerate(node.deps):
                if dep == old_name:
                    node.deps[i] = new_name

        self.__save()
        self.update_screen()


if __name__ == "__main__":
    menu = FlowChartMenu(file=os.environ["FLOWCHART_FILE"])
    menu.exec()
