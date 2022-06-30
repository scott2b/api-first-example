from fastapi import Form


class OAuth2ClientTokenRequestForm:
    def __init__(
        self,
        grant_type: str = Form(None, regex="client_credentials"),
        token_type: str = "Bearer",
        client_id: str = Form(...),
        client_secret: str = Form(...),
    ):
        self.grant_type = grant_type
        self.token_type = token_type
        self.scopes = ["api"]
        self.client_id = client_id
        self.client_secret = client_secret


class OAuth2ClientRefreshTokenRequestForm:
    def __init__(
        self,
        grant_type: str = Form(None, regex="refresh_token"),
        refresh_token: str = Form(...),
    ):
        self.grant_type = grant_type
        self.refresh_token = refresh_token
