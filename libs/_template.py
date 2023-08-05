import logging
import re
import subprocess
from typing import Callable, List, Optional


class Template:
    """Compile an text into a template function"""

    def __init__(
        self, text, file_locator: Optional[Callable[[str], Optional[str]]] = None
    ):
        self.delimiter = re.compile(r"{{(.*?)}}", re.DOTALL)
        self.tokens = self.compile(text)
        self.file_locator = file_locator

    def compile(self, text):
        tokens = []
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
        def include(file, context={}):
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

        # run the code
        result = []
        for is_code, token in self.tokens:
            if is_code:
                try:
                    ret = eval(token, global_context)
                    if ret is not None:
                        result.append(ret)
                except NameError as ex:
                    if undefined_names is not None:
                        logging.debug(f"Undefined name: {ex.name}")
                        undefined_names.append(ex.name)
            else:
                result.append(token)
        result = [str(x) for x in result]
        return "".join(result)

    # make instance callable
    __call__ = render


def render_template_file(
    template_file,
    output_file,
    context=None,
    undefined_names: Optional[List[str]] = None,
):
    with open(template_file, "r", encoding="utf-8") as f:
        s = Template(f.read()).render(context, undefined_names=undefined_names)

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
