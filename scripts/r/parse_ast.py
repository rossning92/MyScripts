import ast
import os
import subprocess
import sys
import re

try:
    import astunparse
except:
    subprocess.call([sys.executable, '-m', 'pip', 'install', 'astunparse'])
    import astunparse


def find_function_deps(tree):
    used_functions = set()

    class FunctionCallVisitor(ast.NodeVisitor):
        def visit_Call(self, node):
            if type(node.func) == ast.Name:
                func_name = node.func.id
                used_functions.add(func_name)
                print(func_name)

    FunctionCallVisitor().visit(tree)
    return list(used_functions)


def parse_ast(f):
    with open(f, "r", encoding='utf-8') as source:
        tree = ast.parse(source.read())
        return tree


os.system('cls')


def find_all_function_def(python_module):
    function_def = {}

    class FunctionDefVisitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            function_def[node.name] = node

    tree = parse_ast(python_module)
    FunctionDefVisitor().visit(tree)
    return function_def


src_file = r"android/adb_backup.py"

# used_functions += find_function_deps(parse_ast(r"../libs/_shutil.py"))


used_functions = []
used_functions += find_function_deps(parse_ast(src_file))

function_def = {}
with open(src_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

out_lines = []
for line in lines:
    line = line.rstrip()

    match = re.match('from (.+) import *', line)
    if match is not None:
        module_name = match.group(1)
        function_def = {
            **function_def,
            **find_all_function_def(f'../../libs/{module_name}.py')
        }

        s = ''
        for func_name in set(used_functions):
            if func_name in function_def:
                s += astunparse.unparse(function_def[func_name])

        out_lines.append(s)

    else:
        out_lines.append(line)

# print('\n'.join(out_lines))
