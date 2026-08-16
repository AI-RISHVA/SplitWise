import os
from dotenv import load_dotenv
load_dotenv()
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_SECRET_KEY = os.getenv("GOOGLE_SECRET_KEY")


from authlib.integrations.starlette_client import OAuth
oauth =OAuth()
oauth.register(
    name="google",
    client_id = GOOGLE_CLIENT_ID,
    client_secret = GOOGLE_SECRET_KEY,
    server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs ={
        "scope":"openid email profile"
    }

)


