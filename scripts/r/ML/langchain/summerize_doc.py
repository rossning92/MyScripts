# https://python.langchain.com/en/latest/use_cases/question_answering.html
# https://python.langchain.com/en/latest/modules/chains/index_examples/summarize.html

# OPENAI_API_KEY

import argparse
import logging
from pprint import pprint

from _shutil import setup_logger
from langchain import OpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.text_splitter import CharacterTextSplitter

if __name__ == "__main__":
    setup_logger(level=logging.DEBUG)

    llm = OpenAI(temperature=0)

    text_splitter = CharacterTextSplitter()

    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Input file path")
    parser.add_argument(
        "-o", "--output", help="Output file path", default=None, type=str
    )
    args = parser.parse_args()

    with open(args.file, encoding="utf-8") as f:
        content = f.read()
    texts = text_splitter.split_text(content)

    docs = [Document(page_content=t) for t in texts]
    chain = load_summarize_chain(
        llm,
        chain_type="map_reduce",
        return_intermediate_steps=True,
    )
    result = chain({"input_documents": docs})

    pprint(result)
    if args.output:
        with open(args.file, "w", encoding="utf-8") as f:
            f.write(result["output_text"])
