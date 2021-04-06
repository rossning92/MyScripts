import ast
import os
import subprocess
import sys
import re
import glob
from collections import defaultdict

try:
    import astunparse
except:
    subprocess.call([sys.executable, '-m', 'pip', 'install', 'astunparse'])
    import astunparse


def find_used_function_names(tree):
    used_functions = set()

    class FunctionCallVisitor(ast.NodeVisitor):
        def visit_Call(self, node):
            if type(node.func) == ast.Name:
                func_name = node.func.id
                used_functions.add(func_name)

    FunctionCallVisitor().visit(tree)
    return list(used_functions)


def find_all_imports(python_file):
    with open(python_file, "r", encoding='utf-8') as f:
        return re.findall('^import [a-z_.]+(?: as [a-z_]+)?$', f.read(), flags=re.MULTILINE)


def parse_ast(f):
    with open(f, "r", encoding='utf-8') as source:
        tree = ast.parse(source.read())
        return tree


def find_all_function_def(python_module):
    function_def = {}

    class FunctionDefVisitor(ast.NodeVisitor):
        def visit_FunctionDef(self, node):
            function_def[node.name] = node

    tree = parse_ast(python_module)
    FunctionDefVisitor().visit(tree)
    return function_def


def get_function_dep_tree(function_def, function_name, scores):
    if function_name in function_def.keys():
        scores[function_name] += 1
        function_names = find_used_function_names(function_def[function_name])
        for f in function_names:
            get_function_dep_tree(function_def, f, scores)


# used_functions += find_function_deps(parse_ast(r"../libs/_shutil.py"))


def transform_python_script(src_file):
    # Get all imports and function_def
    function_def = {}
    imports = set()
    for py_module in glob.glob('../../libs/_*.py'):
        function_def.update(find_all_function_def(py_module))
        imports = imports.union(find_all_imports(py_module))

    # Get used function in current module
    used_functions = []
    used_functions += find_used_function_names(parse_ast(src_file))

    # Get all used functions
    scores = defaultdict(lambda: 0)
    for f in used_functions:
        get_function_dep_tree(function_def, f, scores)

    # Sort function by dependency
    used_functions = sorted(scores.keys(), key=lambda k: scores[k], reverse=True)
    print('Used functions: ' + str(used_functions))

    # Read python file
    with open(src_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    out_lines = []
    first_import = True
    for line in lines:
        line = line.rstrip()

        match = re.match('from (.+) import *', line)
        if match is not None:
            # module_name = match.group(1)
            # function_def.update(get_all_function_def(f'../../libs/{module_name}.py'))

            if first_import:
                s = '\n'.join(imports)

                s += '\n\n'
                for func_name in set(used_functions):
                    if func_name in function_def:
                        s += astunparse.unparse(function_def[func_name])

                out_lines.append(s)
                first_import = False

        else:
            out_lines.append(line)

    return '\n'.join(out_lines)


if __name__ == "__main__":
    os.system('cls')

    out_dir = os.path.expanduser('~/Desktop/ScriptExport')
    script_path = os.getenv('_SCRIPT')
    out_script = out_dir + os.path.sep + os.path.basename(script_path)

    s = transform_python_script(script_path)
    print('Write to "%s"...' % out_script)

    os.makedirs(out_dir, exist_ok=True)
    with open(out_script, 'w', encoding='utf-8') as f:
        f.write(s)
