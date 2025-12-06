async def check_for_status(response):
    if response.status >= 400:
        error_text = await response.text()
        raise Exception(f"Request failed with status {response.status}: {error_text}")
