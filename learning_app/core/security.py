from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from core.jwt_utils import decode_access_token

bearer_scheme = HTTPBearer(auto_error=False)

def get_current_org(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):
    """
    Dependency to get current org from JWT in Authorization header.
    Accepts Swagger "Authorize" token and fetch API calls.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )

    token = credentials.credentials
    return decode_access_token(token)