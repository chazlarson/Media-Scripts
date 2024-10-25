""" docstring placeholder """
# This little script needs only Python 3.9 and a couple requirements, and will generate the MAL section for your Kometa config file.
# Most of this code is pulled from Kometa's own MAL authentication; it's just been simplified to do
# the one thing and not rely on any Kometa code.
#
# You can run this on a completely separate machine to where Kometa is running.
#
# Download it somewhere,
# python3 -m pip install pyopenssl
# python3 -m pip install requests secrets
# python3 kometa-mal-auth.py
# then run it with "python3 kometa-mal-auth.py".
#
# If you're running Kometa locally, just copy it into the Kometa directory and run in the Kometa environment.  All teh requirements are already there.
#
# You'll be asked for your MyAnimeList Client ID and Client Secret
# Then taken to a MyAnimeList web page
# Login and click "Allow"
# You'll be taken to a local URL that won't load.
# Copy that localhost URL and paste it at the prompt.
#
# Some yaml will be printed, ready to copy-paste into your Kometa config.yml.

import webbrowser
import secrets
import re
import os
import sys
import requests

urls = {
    "oauth_token": "https://myanimelist.net/v1/oauth2/token",
    "oauth_authorize": "https://myanimelist.net/v1/oauth2/authorize",
}

print("Let's authenticate against MyAnimeList!{os.linesep}{os.linesep}")
session = requests.Session()

client_id = input("MyAnimeList Client ID: ").strip()
client_secret = input("MyAnimeList Client Secret: ").strip()

code_verifier = secrets.token_urlsafe(100)[:128]
URL = f"{urls['oauth_authorize']}?response_type=code&client_id={client_id}&code_challenge={code_verifier}"

print(f"We're going to open {URL}{os.linesep}{os.linesep}")
print(f"Log in and click the Allow option.{os.linesep}")
print(
    f"You will be redirected to a localhost url that probably won't load.{os.linesep}"
)
print(f"That's fine.  Copy that localhost URL and paste it below.{os.linesep}")
tmpVar = input("Hit enter when ready: ").strip()

webbrowser.open(URL, new=2)

url = input("URL: ").strip()

match = re.search("code=([^&]+)", str(url))
if not match:
    print(f"Couldn't find the required code in that URL.{os.linesep}")
    sys.exit()

code = match.group(1)

data = {
    "client_id": client_id,
    "client_secret": client_secret,
    "code": code,
    "code_verifier": code_verifier,
    "grant_type": "authorization_code",
}

new_authorization = session.post(urls["oauth_token"], data=data).json()

if "error" in new_authorization:
    print(f"ERROR: invalid code.{os.linesep}")
    sys.exit()

print(f"{os.linesep}{os.linesep}Copy the following into your Kometa config.yml:")
print("############################################")
print("mal:")
print(f"  client_id: {client_id}")
print(f"  client_secret: {client_secret}")
print("  authorization:")
print(f"    access_token: {new_authorization['access_token']}")
print(f"    token_type: {new_authorization['token_type']}")
print(f"    expires_in: {new_authorization['expires_in']}")
print(f"    refresh_token: {new_authorization['refresh_token']}")
print("############################################")
