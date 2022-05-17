import os
import re


class Template:
    """Compile an text into a template function"""

    def __init__(self, text):
        self.delimiter = re.compile(r"{{(.*?)}}", re.DOTALL)
        self.tokens = self.compile(text)

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

    def render(self, context=None, **kwargs):
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
        def include(file):
            with open(file, "r", encoding="utf-8") as f:
                result.append(f.read())

        global_context["include"] = include

        # run the code
        result = []
        for is_code, token in self.tokens:
            if is_code:
                try:
                    ret = eval(token, global_context)
                    if ret is not None:
                        result.append(ret)
                except NameError:
                    pass
            else:
                result.append(token)
        result = [str(x) for x in result]
        return "".join(result)

    # make instance callable
    __call__ = render


def render_template_file(template_file, output_file, context=None):
    with open(template_file, "r", encoding="utf-8") as f:
        s = Template(f.read()).render(context)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(s)


def render_template(template, context=None):
    return Template(template).render(context)
