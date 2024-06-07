import logging
import re
import subprocess
from typing import Any, Callable, List, Optional, Tuple


class Template:
    """Compile an text into a template function"""

    def __init__(self, text, file_locator: Optional[Callable[[str], str]] = None):
        self.delimiter = re.compile(r"{{(.*?)}}", re.DOTALL)
        self.tokens = self.compile(text)
        self.file_locator = file_locator

    def compile(self, text) -> List[Tuple[bool, str]]:
        tokens: List[Tuple[bool, str]] = []
        for index, token in enumerate(self.delimiter.split(text)):
            if index % 2 == 0:
                # plain string
                if token:
                    tokens.append((False, token))
            else:
                # code block
                tokens.append((True, token))
        return tokens

    def render(
        self, context=None, undefined_names: Optional[List[str]] = None, **kwargs
    ):
        """Render the template according to the given context"""

        VARIABLE_NAME_REGEX = "[_a-zA-Z]\\w*"

        global_context = {}
        if context:
            global_context.update(context)
        if kwargs:
            global_context.update(kwargs)

        # Assignment function
        def set(name, value):
            global_context[name] = value

        global_context["set"] = set

        # Include function
        def include(file: str, context={}):
            nonlocal undefined_names

            if self.file_locator:
                file = self.file_locator(file)
            with open(file, "r", encoding="utf-8") as f:
                s = f.read()
            return Template(s, file_locator=self.file_locator).render(
                context={**global_context, **context},
                undefined_names=undefined_names,
                **kwargs,
            )

        global_context["include"] = include

        def expect(exp, message):
            if not exp:
                raise Exception(message)

        global_context["expect"] = expect

        def shell(args):
            return subprocess.check_output(args, shell=True, universal_newlines=True)

        global_context["shell"] = shell

        # Evaluated result.
        result: List[str] = []

        def eval_code(source: str) -> Optional[Any]:
            try:
                ret = eval(source, global_context)
                if ret is not None:
                    return ret
            except NameError as ex:
                logging.warning(f"Undefined name: {ex.name}")
                if undefined_names is not None:
                    undefined_names.append(ex.name)
                else:
                    raise
            return None

        def eval_tokens(tokens: List[Tuple[bool, str]], should_eval=True) -> List[str]:
            result: List[str] = []
            while len(tokens) > 0:
                is_code, token = tokens.pop(0)
                if not is_code:
                    result.append(token)
                else:
                    if token.startswith("#"):
                        pass
                    elif match := re.match(
                        rf"({VARIABLE_NAME_REGEX})\s*=\s*(.+)", token
                    ):
                        variable_name = match.group(1)
                        expr = match.group(2)
                        val = eval(expr, global_context)
                        global_context[variable_name] = val
                    elif token.startswith("if "):
                        condition = token[3:]
                        cond = eval(condition, global_context)
                        result.extend(eval_tokens(tokens=tokens, should_eval=cond))
                        is_code, token = tokens.pop(0)
                        if (is_code, token) == (True, "else"):
                            result.extend(
                                eval_tokens(tokens=tokens, should_eval=not cond)
                            )
                            is_code, token = tokens.pop(0)
                        if (is_code, token) != (True, "end"):
                            raise Exception('Expect "{{end}}"')
                    elif token == "else":
                        tokens.insert(0, (True, "else"))
                        return result if should_eval else []
                    elif match := re.match(
                        f"for ({VARIABLE_NAME_REGEX}) in (.+)", token
                    ):
                        variable_name = match.group(1)
                        iterable = match.group(2)
                        tokens_copy = tokens.copy()
                        for val in eval(iterable, global_context):
                            global_context[variable_name] = val
                            tokens[:] = tokens_copy
                            result.extend(eval_tokens(tokens=tokens))
                        is_code, token = tokens.pop(0)
                        assert (is_code, token) == (True, "end")
                    elif token == "end":
                        tokens.insert(0, (True, "end"))
                        return result if should_eval else []
                    else:
                        ret = eval_code(source=token)
                        if ret is not None:
                            result.append(ret)

            return result if should_eval else []

        result = eval_tokens(tokens=self.tokens)
        return "".join([str(x) for x in result])

    # make instance callable
    __call__ = render


def render_template_file(
    template_file,
    output_file,
    context=None,
    undefined_names: Optional[List[str]] = None,
    file_locator: Optional[Callable[[str], str]] = None,
):
    with open(template_file, "r", encoding="utf-8") as f:
        s = Template(f.read(), file_locator=file_locator).render(
            context, undefined_names=undefined_names
        )

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(s)


def render_template(
    template,
    context=None,
    file_locator: Optional[Callable[[str], Optional[str]]] = None,
    undefined_names: Optional[List[str]] = None,
):
    return Template(template, file_locator=file_locator).render(
        context, undefined_names=undefined_names
    )
