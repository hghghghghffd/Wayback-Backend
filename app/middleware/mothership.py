from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.config import settings

EXEMPT_PATHS = {"/", "/health", "/favicon.ico", "/api/v1/docs", "/api/v1/redoc", "/api/v1/openapi.json"}


class MothershipMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path in EXEMPT_PATHS or path.startswith("/static"):
            return await call_next(request)

        client_ip = self._get_ip(request)

        try:
            from app.database import SessionLocal
            from app.models.models import SuspiciousIP, IPBan
            from sqlalchemy.sql import func

            db = SessionLocal()
            try:
                ban = db.query(IPBan).filter(
                    IPBan.ip_address == client_ip,
                    IPBan.is_active == True
                ).first()

                if ban:
                    return JSONResponse(
                        status_code=403,
                        content={
                            "status": "banned",
                            "code": "IP_BANNED",
                            "message": "Your IP address has been permanently banned from Waygo.",
                            "contact": "playfabauthenticatorsettings_ on Discord"
                        }
                    )

                key = request.headers.get("X-Mothership-Key", "")
                if key != settings.MOTHERSHIP_KEY:
                    existing = db.query(SuspiciousIP).filter(SuspiciousIP.ip_address == client_ip).first()
                    if existing:
                        existing.attempt_count += 1
                        existing.last_attempt = func.now()
                        attempts = existing.attempt_count
                    else:
                        new_ip = SuspiciousIP(ip_address=client_ip, attempt_count=1)
                        db.add(new_ip)
                        attempts = 1

                    db.commit()

                    if attempts >= settings.IP_BAN_THRESHOLD:
                        existing_ban = db.query(IPBan).filter(IPBan.ip_address == client_ip).first()
                        if not existing_ban:
                            db.add(IPBan(
                                ip_address=client_ip,
                                reason="Exceeded unauthorized mothership key attempt threshold"
                            ))
                            db.commit()

                        return JSONResponse(
                            status_code=403,
                            content={
                                "status": "banned",
                                "code": "IP_BANNED",
                                "message": "Your IP has been permanently banned due to repeated unauthorized access attempts. This incident has been logged.",
                                "contact": "playfabauthenticatorsettings_ on Discord"
                            }
                        )

                    return JSONResponse(
                        status_code=401,
                        content={
                            "status": "unauthorized",
                            "code": "INVALID_MOTHERSHIP_KEY",
                            "message": "Invalid or missing Mothership Key. All unauthorized access attempts are logged and traced.",
                            "attempts_remaining": max(0, settings.IP_BAN_THRESHOLD - attempts),
                            "contact": "playfabauthenticatorsettings_ on Discord"
                        }
                    )
            finally:
                db.close()

        except Exception:
            key = request.headers.get("X-Mothership-Key", "")
            if key != settings.MOTHERSHIP_KEY:
                return JSONResponse(
                    status_code=401,
                    content={
                        "status": "unauthorized",
                        "code": "INVALID_MOTHERSHIP_KEY",
                        "message": "Invalid or missing Mothership Key.",
                        "contact": "playfabauthenticatorsettings_ on Discord"
                    }
                )

        return await call_next(request)

    def _get_ip(self, request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "unknown"
