TRANSIENT_ERROR_NAMES = frozenset(
    {
        "APIConnectionError",
        "APITimeoutError",
        "ConnectError",
        "ConnectionError",
        "ConnectTimeout",
        "ReadTimeout",
        "Timeout",
        "TimeoutException",
    }
)


def is_transient(error: BaseException) -> bool:
    """True for failures where the request never completed."""
    return type(error).__name__ in TRANSIENT_ERROR_NAMES
