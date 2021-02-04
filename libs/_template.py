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
                # find out the indentation
                lines = token.splitlines()
                indent = min([len(l) - len(l.lstrip()) for l in lines if l.strip()])
                realigned = "\n".join(l[indent:] for l in lines)
                tokens.append(
                    (True, compile(realigned, "<template> %s" % realigned[:20], "exec"))
                )
        return tokens

    def render(self, context=None, **kwargs):
        """Render the template according to the given context"""
        global_context = {}
        if context:
            global_context.update(context)
        if kwargs:
            global_context.update(kwargs)

        # add function for output
        def echo(*args):
            result.extend([str(arg) for arg in args])

        global_context["echo"] = echo

        def include(file):
            with open(file, "r", encoding="utf-8") as f:
                result.append(f.read())

        global_context["include"] = include

        # run the code
        result = []
        for is_code, token in self.tokens:
            if is_code:
                exec(token, global_context)
            else:
                result.append(token)
        return "".join(result)

    # make instance callable
    __call__ = render


def render_template(template_file, output_file, context=None):
    with open(template_file, "r", encoding="utf-8") as f:
        s = Template(f.read()).render(context)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(s)
