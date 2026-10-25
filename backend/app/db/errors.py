from sqlalchemy.exc import SQLAlchemyError


def database_error_code(exc: SQLAlchemyError) -> int | None:
    original = getattr(exc, "orig", None)
    arguments = getattr(original, "args", ())
    code = arguments[0] if arguments else None
    return code if isinstance(code, int) and not isinstance(code, bool) else None
