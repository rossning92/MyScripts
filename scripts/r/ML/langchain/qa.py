# https://python.langchain.com/en/latest/use_cases/question_answering.html
# https://python.langchain.com/en/latest/modules/chains/index_examples/summarize.html

# OPENAI_API_KEY

import argparse
import logging

from _shutil import print2, setup_logger
from langchain import OpenAI
from langchain.chains.question_answering import load_qa_chain
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.llms import OpenAI
from langchain.text_splitter import CharacterTextSplitter, PythonCodeTextSplitter
from langchain.vectorstores import Chroma

if __name__ == "__main__":
    setup_logger(level=logging.DEBUG)

    # argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file", help="Input file path", nargs="?", default=r"C:\tmp\1.txt"
    )
    parser.add_argument(
        "-o", "--output", help="Output file path", default=None, type=str
    )
    args = parser.parse_args()

    # Read doc
    with open(args.file, encoding="utf-8") as f:
        content = f.read()

    # Split doc into chunks
    # text_splitter = PythonCodeTextSplitter(chunk_size=512, chunk_overlap=0)
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    texts = text_splitter.split_text(content)

    # Create embeddings
    embeddings = OpenAIEmbeddings()
    docsearch = Chroma.from_texts(
        texts, embeddings, metadatas=[{"source": str(i)} for i in range(len(texts))]
    ).as_retriever()

    # Query relevant docs using the embeddings
    query = input("question?")
    # query = "which file may be most suitable for adding InitVulkan() function"
    docs = docsearch.get_relevant_documents(query)

    llm = OpenAI(temperature=0)
    chain = load_qa_chain(OpenAI(temperature=0), chain_type="stuff")
    result = chain.run(input_documents=docs, question=query)

    print2(result)
