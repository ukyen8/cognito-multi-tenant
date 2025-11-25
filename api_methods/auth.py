from fastapi import APIRouter, HTTPException, status, Depends

from aws_lambda_powertools import Logger
from cognito import get_cognito_client
from dtos.auth import TokenRequest, TokenResponse
from settings import get_settings, Settings

router = APIRouter()
logger = Logger()


@router.post("/auth/token", response_model=TokenResponse)
def get_token(
    request: TokenRequest,
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    """Issue a token for the user using their username and password."""
    client = get_cognito_client(settings)

    try:
        resp = client.initiate_auth(
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": request.username,
                "PASSWORD": request.password,
            },
            ClientId=settings.app_client_id,
        )
        tokens = resp["AuthenticationResult"]
        logger.info(f"Token issued for user {request.username}")
        return TokenResponse(
            id_token=tokens["IdToken"],
            access_token=tokens["AccessToken"],
            refresh_token=tokens["RefreshToken"],
        )
    except client.exceptions.NotAuthorizedException:
        logger.warning(f"Invalid login attempt for user {request.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
        ) from None
    except client.exceptions.UserNotFoundException:
        logger.warning(f"User not found: {request.username}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        ) from None
    except Exception as e:
        logger.exception(
            f"Failed to issue token for user {request.username}: {e}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        ) from e
