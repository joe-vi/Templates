import asyncpg
from sqlalchemy.exc import DBAPIError


def is_deadlock(exc: DBAPIError) -> bool:
    """Report whether a DBAPIError was caused by a database deadlock.

    Args:
        exc: The DBAPIError raised by the driver.

    Returns:
        True if the underlying cause is a deadlock, False otherwise.
    """
    return isinstance(exc.__cause__, asyncpg.exceptions.DeadlockDetectedError)
