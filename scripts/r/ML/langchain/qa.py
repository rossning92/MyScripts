# https://python.langchain.com/en/latest/use_cases/question_answering.html

import argparse
import logging
import os

from langchain import hub
from langchain.chat_models import ChatOpenAI
from langchain.document_loaders.generic import GenericLoader
from langchain.embeddings import CacheBackedEmbeddings
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.schema.runnable import RunnablePassthrough
from langchain.storage import LocalFileStore
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Chroma
from utils.logger import setup_logger

if __name__ == "__main__":
    langchain_qa_log = os.path.join(
        os.environ.get("MY_TEMP_DIR", os.getcwd()), "langchain_qa_log.txt"
    )
    setup_logger(level=logging.DEBUG, log_file=langchain_qa_log, log_to_stderr=False)

    # Argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Input file path")
    parser.add_argument(
        "-o", "--output", help="Output file path", default=None, type=str
    )
    args = parser.parse_args()

    # Load document using a generic loader (based on the file type)
    loader = GenericLoader.from_filesystem(
        path=os.path.dirname(args.file),
        glob=os.path.basename(args.file),
    )
    docs = loader.lazy_load()

    # Split doc into chunks
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=0)
    docs = text_splitter.split_documents(docs)

    # Embed and store splits
    underlying_embeddings = OpenAIEmbeddings()

    # Caching embeddings
    # https://python.langchain.com/docs/modules/data_connection/text_embedding/caching_embeddings
    embedding_cache_path = os.path.join(
        os.environ.get("MY_TEMP_DIR", os.getcwd()), "embedding_cache"
    )
    fs = LocalFileStore(embedding_cache_path)
    cached_embedder = CacheBackedEmbeddings.from_bytes_store(
        underlying_embeddings, fs, namespace=underlying_embeddings.model
    )

    vectorstore = Chroma.from_documents(docs, cached_embedder)
    retriever = vectorstore.as_retriever()

    # Prompt
    rag_prompt = hub.pull("rlm/rag-prompt")

    # LLM
    llm = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)  # type: ignore

    # RAG chain
    rag_chain = (
        {"context": retriever, "question": RunnablePassthrough()} | rag_prompt | llm
    )
    try:
        while True:
            query = input("> ")
            result = rag_chain.invoke(query)
            print(result.content)
    except (BrokenPipeError, IOError):
        pass
