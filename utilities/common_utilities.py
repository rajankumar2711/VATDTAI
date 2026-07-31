import inspect


def get_current_test_method_name():
    """
    Retrieves the name of the currently executing test method.

    Returns:
        str: The name of the current test method or 'Unknown' if it cannot be determined.
    """
    stack = inspect.stack()
    # Iterate over the stack in reverse to find the first 'test_' prefixed method
    for frame_info in reversed(stack):
        if frame_info.function.startswith('test_'):
            return frame_info.function
    return 'Unknown'