# https://huggingface.co/models?pipeline_tag=image-to-text&sort=likes

from transformers import pipeline

captioner = pipeline("image-to-text", model="microsoft/git-large-coco")

while True:
    try:
        file = input("input file path: ")
        result = captioner(file)
        print(result)
    except Exception as ex:
        print(f"ERROR: {ex}")
        pass
