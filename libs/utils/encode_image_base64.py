import base64
import mimetypes


def encode_image_base64(image_path: str) -> str:
    mime_type, _ = mimetypes.guess_type(image_path)
    if not mime_type:
        raise ValueError(f"Could not determine MIME type for file: {image_path}")

    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode("utf-8")

    return "data:{};base64,{}".format(mime_type, encoded)
