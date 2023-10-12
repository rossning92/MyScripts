# https://python.langchain.com/docs/use_cases/summarization#option-2-map-reduce

# OPENAI_API_KEY

import argparse
import os
from pprint import pprint

from langchain.chains.summarize import load_summarize_chain
from langchain.document_loaders.generic import GenericLoader
from langchain.llms import OpenAI
from langchain.text_splitter import CharacterTextSplitter


def summarize(file: str):
    abspath = os.path.abspath(file)

    # Create language model
    llm = OpenAI(temperature=0)

    # Load document from a text file
    # loader = TextLoader(file, autodetect_encoding=True)
    # docs = loader.load()

    # Load document using a generic loader (based on the file type)
    loader = GenericLoader.from_filesystem(
        path=os.path.dirname(abspath),
        glob=os.path.basename(abspath),
    )
    docs = loader.lazy_load()

    # Create text splitter
    text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    docs = text_splitter.split_documents(docs)

    chain = load_summarize_chain(
        llm,
        chain_type="map_reduce",
        return_intermediate_steps=True,
    )
    result = chain({"input_documents": docs})

    # Save summarize chain result for debugging purpose
    summerize_chain_result = os.path.join(
        os.environ.get("MY_TEMP_DIR", os.getcwd()), "summerize_chain_result.txt"
    )
    with open(summerize_chain_result, "w", encoding="utf-8") as f:
        pprint(result, f)

    output_text = result["output_text"]
    return output_text


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file", help="Input file path")
    parser.add_argument(
        "-o", "--output", help="Output file path", default=None, type=str
    )
    args = parser.parse_args()

    print(f'Summarizing "{args.file}"...')
    output_text = summarize(file=args.file)

    if args.output:
        with open(args.file, "w", encoding="utf-8") as f:
            f.write(output_text)
    else:
        print(output_text)


if __name__ == "__main__":
    main()
