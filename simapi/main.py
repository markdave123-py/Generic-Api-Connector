"""FastAPI simulation of the third‑party API (robust to FastAPI versions <0.110)."""
import math
import os
import time
from fastapi import Depends, FastAPI, HTTPException, Form
from fastapi.security import OAuth2PasswordBearer
from starlette.responses import JSONResponse

# --- Compatibility shim ------------------------------------------------------
# FastAPI ≤0.109 does not ship OAuth2ClientCredentialsRequestForm.  If it is
# unavailable we build a minimal replacement that behaves the same for our test
# purposes.
try:
    from fastapi.security import OAuth2ClientCredentialsRequestForm  # type: ignore
except ImportError:  # pragma: no cover – for older FastAPI

    class OAuth2ClientCredentialsRequestForm:  # pylint: disable=too-few-public-methods
        """Fallback form parser for client‑credentials grant."""

        def __init__(
            self,
            client_id: str = Form(...),
            client_secret: str = Form(...),
            grant_type: str = Form("client_credentials"),
        ):
            self.client_id = client_id
            self.client_secret = client_secret
            self.grant_type = grant_type

# ----------------------------------------------------------------------------

app = FastAPI(title="Simulated API")

# Dummy credentials (env‑driven to avoid hard‑coding)
CLIENT_ID = os.getenv("API_CLIENT_ID", "testclient")
CLIENT_SECRET = os.getenv("API_CLIENT_SECRET", "testsecret")
TOKEN_VALUE = "simtoken"  # constant token for simplicity
TOKEN_LIFETIME = 30  # seconds

# OAuth2 token endpoint
@app.post("/oauth2/token")
async def token(form: OAuth2ClientCredentialsRequestForm = Depends()):
    if form.client_id != CLIENT_ID or form.client_secret != CLIENT_SECRET:
        return JSONResponse({"error": "invalid_client"}, status_code=401)
    return {
        "access_token": TOKEN_VALUE,
        "token_type": "Bearer",
        "expires_in": TOKEN_LIFETIME,
    }

bearer_scheme = OAuth2PasswordBearer(tokenUrl="/oauth2/token", auto_error=False)

# Sample data – five items
ITEMS = [
    {"id": i, "name": f"Item {i}", "value": i * 1.5} for i in range(1, 6)
]
PAGE_SIZE = 2

@app.get("/items")
async def list_items(page: int = 1, token: str = Depends(bearer_scheme)):
    if token != TOKEN_VALUE:
        raise HTTPException(status_code=401, detail="Unauthorized")
    start, end = (page - 1) * PAGE_SIZE, page * PAGE_SIZE
    page_items = ITEMS[start:end]
    total_pages = math.ceil(len(ITEMS) / PAGE_SIZE)
    next_page = page + 1 if page < total_pages else None
    return {
        "items": page_items,
        "page": page,
        "total_pages": total_pages,
        "next_page": next_page,
    }