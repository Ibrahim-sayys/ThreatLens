def clean_newlines(text):
    """
    Removes backslash-n and backslash-r from the input string,
    replacing them with a space. Also strips leading/trailing spaces.

    Args:
        text (str): The string to clean.

    Returns:
        str: The cleaned string.
    """
    print("helper cleaner was called")
    if not isinstance(text, str):
        return text
    return text.replace('\n', ' ').replace('\r', ' ').strip()