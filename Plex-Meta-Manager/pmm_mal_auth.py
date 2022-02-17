# This little script needs only Python 3.9 and a couple requirements, and will generate the MAL section for your PMM config file.
# Most of this code is pulled from PMM's own MAL authentication; it's just been simplified to do
# the one thing and not rely on any PMM code.
#
# You can run this on a completely separate machine to where PMM is running.
#
# Download it somewhere, "python3 -m pip install requests, webbrowser, secrets, re" and run it with "python3 pmm_mal_auth.py".
#
# You'll be asked for your MyAnimeList Client ID and Client Secret
# Then taken to a MyAnimeList web page
# Login and click "Allow"
# You'll be taken to a local URL that won't load.
# Copy that localhost URL and paste it at the prompt.
#
# Some yaml will be printed, ready to copy-paste into your PMM config.yml.

import requests, webbrowser, secrets, re

urls = {
    "oauth_token": f"https://myanimelist.net/v1/oauth2/token",
    "oauth_authorize": f"https://myanimelist.net/v1/oauth2/authorize",
}

print("Let's authenticate against MyAnimeList!\n\n")
session = requests.Session()

client_id = input("MyAnimeList Client ID: ").strip()
client_secret = input("MyAnimeList Client Secret: ").strip()

code_verifier = secrets.token_urlsafe(100)[:128]
url = f"{urls['oauth_authorize']}?response_type=code&client_id={client_id}&code_challenge={code_verifier}"

print(f"We're going to open {url}\n\n")
print(f"Log in and click the Allow option.\n")
print(f"You will be redirected to a localhost url that probably won't load.\n")
print(f"That's fine.  Copy that localhost URL and paste it below.\n")
tmpVar = input("Hit enter when ready: ").strip()

webbrowser.open(url, new=2)

url = input("URL: ").strip()

match = re.search("code=([^&]+)", str(url))
if not match:
    print(f"Couldn't find the required code in that URL.\n")
    exit()

code = match.group(1)

data = {
    "client_id": client_id,
    "client_secret": client_secret,
    "code": code,
    "code_verifier": code_verifier,
    "grant_type": "authorization_code"
}

new_authorization = session.post(urls["oauth_token"], data=data).json()

if "error" in new_authorization:
    print(f"ERROR: invalid code.\n")
    exit()

print (f"\n\nCopy the following into your PMM config.yml:")
print (f"############################################")
print (f"mal:")
print (f"  client_id: {client_id}")
print (f"  client_secret: {client_secret}")
print (f"  authorization:")
print (f"    access_token: {new_authorization['access_token']}")
print (f"    token_type: {new_authorization['token_type']}")
print (f"    expires_in: {new_authorization['expires_in']}")
print (f"    refresh_token: {new_authorization['refresh_token']}")
print (f"############################################")
