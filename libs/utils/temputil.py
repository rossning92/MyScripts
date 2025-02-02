def get_temp_file(ext: str) -> str:
    import tempfile

    return tempfile.NamedTemporaryFile(suffix=ext, delete=False).name
