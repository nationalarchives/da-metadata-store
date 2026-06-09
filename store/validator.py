import json
from urllib.request import urlopen

from joserfc.jwk import KeySet
from authlib.oauth2.rfc7523 import JWTBearerTokenValidator
from django.conf import settings


class CognitoJWTBearerTokenValidator(JWTBearerTokenValidator):
    def __init__(self):
        issuer = settings.ISSUER
        if issuer:
            try:
                jsonurl = urlopen(f"{issuer}/.well-known/jwks.json")
                public_key = KeySet.import_key_set(json.loads(jsonurl.read()))
                super().__init__(public_key, issuer=issuer)
            except Exception:
                super().__init__(KeySet.import_key_set({"keys": []}), issuer=issuer)
        else:
            super().__init__(KeySet.import_key_set({"keys": []}), issuer="")

        self.claims_options = {"exp": {"essential": True}}
