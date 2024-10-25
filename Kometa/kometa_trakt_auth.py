"""docstring placeholder"""
# This little script needs only Python 3.9 and requests, and will generate the trakt section for your Kometa config file.
# Most of this code is pulled from Kometa's own trakt authentication; it's just been simplified to do
# the one thing and not rely on any Kometa code.
#
# You can run this on a completely separate machine to where Kometa is running.
#
# Download it somewhere, "python3 -m pip install requests" and run it with "python3 kometa-trakt-auth.py".
#
# You'll be asked for your trakt Client ID and Client Secret
# Then taken to a trakt web page
# copy the PIN and paste it at the prompt.
#
# Some yaml will be printed, ready to copy-paste into your Kometa config.yml.

import webbrowser
import requests

REDIRECT_URI = "urn:ietf:wg:oauth:2.0:oob"
REDIRECT_URI_ENCODED = REDIRECT_URI.replace(":", "%3A")
BASE_URL = "https://api.trakt.tv"

print("Let's authenticate against Trakt!\n\n")

CLIENT_ID = input("Trakt Client ID: ").strip()
CLIENT_SECRET = input("Trakt Client Secret: ").strip()

URL = f"https://trakt.tv/oauth/authorize?response_type=code&client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI_ENCODED}"
print(
    f"Taking you to: {URL}\n\nIf you get an OAuth error your Client ID or Client Secret is invalid\n\nIf a browser window doesn't open go to that URL manually.\n\n"
)
webbrowser.open(URL, new=2)
pin = input("Enter the Trakt pin from that web page: ").strip()
json = {
    "code": pin,
    "client_id": CLIENT_ID,
    "client_secret": CLIENT_SECRET,
    "redirect_uri": REDIRECT_URI,
    "grant_type": "authorization_code",
}
response = requests.post(
    f"{BASE_URL}/oauth/token", json=json, headers={"Content-Type": "application/json"},
    timeout=30
)

if response.status_code != 200:
    print(
        "Trakt Error: Invalid trakt pin. If you're sure you typed it in correctly your client_id or client_secret may be invalid"
    )
else:
    print("Authentication successful; validating credentials...")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {response.json()['access_token']}",
        "trakt-api-version": "2",
        "trakt-api-key": CLIENT_ID,
    }

    validation_response = requests.get(f"{BASE_URL}/users/settings",
        headers=headers,
        timeout=30)
    if validation_response.status_code == 423:
        print("Trakt Error: Account is locked; please contact Trakt Support")
    else:
        print("Copy the following into your Kometa config.yml:")
        print("############################################")
        print("trakt:")
        print(f"  client_id: {CLIENT_ID}")
        print(f"  client_secret: {CLIENT_SECRET}")
        print("  authorization:")
        print(f"    access_token: {response.json()['access_token']}")
        print(f"    token_type: {response.json()['token_type']}")
        print(f"    expires_in: {response.json()['expires_in']}")
        print(f"    refresh_token: {response.json()['refresh_token']}")
        print(f"    scope: {response.json()['scope']}")
        print(f"    created_at: {response.json()['created_at']}")
        print("  pin:")
        print("############################################")
