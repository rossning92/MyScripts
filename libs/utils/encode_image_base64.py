import base64


def encode_image_base64(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("utf-8")
    return "data:image/jpeg;base64,{}".format(encoded)
