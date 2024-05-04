import logging
import sys
from pprint import pprint

from haystack import Pipeline
from haystack.components.builders.prompt_builder import PromptBuilder
from haystack.components.converters import HTMLToDocument
from haystack.components.fetchers import LinkContentFetcher
from haystack.components.generators import OpenAIGenerator
from haystack.components.websearch import SerperDevWebSearch

logging.basicConfig(
    format="%(levelname)s - %(name)s -  %(message)s", level=logging.WARNING
)
logging.getLogger("haystack").setLevel(logging.DEBUG)


web_search = SerperDevWebSearch(top_k=6)
link_content = LinkContentFetcher()
html_converter = HTMLToDocument()

template = """Given the information below: \n
            {% for document in documents %}
                {{ document.content }}
            {% endfor %}
            Answer question: {{ query }}. \n Answer:"""

prompt_builder = PromptBuilder(template=template)
llm = OpenAIGenerator(model="gpt-4")

pipe = Pipeline()
pipe.add_component("search", web_search)
pipe.add_component("fetcher", link_content)
pipe.add_component("converter", html_converter)
pipe.add_component("prompt_builder", prompt_builder)
pipe.add_component("llm", llm)

pipe.connect("search.links", "fetcher.urls")
pipe.connect("fetcher.streams", "converter.sources")
pipe.connect("converter.documents", "prompt_builder.documents")
pipe.connect("prompt_builder.prompt", "llm.prompt")


query = sys.argv[-1]
result = pipe.run(data={"search": {"query": query}, "prompt_builder": {"query": query}})
pprint(result)
