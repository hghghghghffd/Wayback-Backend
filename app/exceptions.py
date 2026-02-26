from fastapi import HTTPException, status


def unauthorized(detail: str = "Not authenticated"):
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def forbidden(detail: str = "Access denied"):
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def not_found(detail: str = "Resource not found"):
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detail)


def conflict(detail: str = "Resource already exists"):
    raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=detail)


def bad_request(detail: str = "Bad request"):
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=detail)
