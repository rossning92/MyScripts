from typing import NamedTuple


class ImageData(NamedTuple):
    mime_type: str
    data: str


def parse_image_data_url(data_url: str) -> ImageData:
    if not data_url.startswith("data:"):
        raise ValueError("Invalid data URL")

    header, sep, payload = data_url[5:].partition(",")
    if not header or not sep or not payload:
        raise ValueError("Invalid data URL")

    mime_type = header.split(";", 1)[0].strip()
    if not mime_type or not mime_type.lower().startswith("image/"):
        raise ValueError("Invalid image mime type")

    return ImageData(mime_type=mime_type, data=payload)
