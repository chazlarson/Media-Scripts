# This little script needs only Python 3.9 and requests, and will generate the trakt section for your PMM config file.
# Most of this code is pulled from PMM's own trakt authentication; it's just been simplified to do
# the one thing and not rely on any PMM code.
#
# You can run this on a completely separate machine to where PMM is running.
#
# Download it somewhere, "python3 -m pip install requests" and run it with "python3 pmm_trakt_auth.py".
#
# You'll be asked for your trakt Client ID and Client Secret
# Then taken to a trakt web page
# copy the PIN and paste it at the prompt.
#
# Some yaml will be printed, ready to copy-paste into your PMM config.yml.

import requests, webbrowser

redirect_uri = "urn:ietf:wg:oauth:2.0:oob"
redirect_uri_encoded = redirect_uri.replace(":", "%3A")
base_url = "https://api.trakt.tv"

print("Let's authenticate against Trakt!\n\n")

client_id = input("Trakt Client ID: ").strip()
client_secret = input("Trakt Client Secret: ").strip()

url = f"https://trakt.tv/oauth/authorize?response_type=code&client_id={client_id}&redirect_uri={redirect_uri_encoded}"
print(f"Taking you to: {url}\n\nIf you get an OAuth error your Client ID or Client Secret is invalid\n\nIf a browser window doesn't open go to that URL manually.\n\n")
webbrowser.open(url, new=2)
pin = input("Enter the Trakt pin from that web page: ").strip()
json = {
    "code": pin,
    "client_id": client_id,
    "client_secret": client_secret,
    "redirect_uri": redirect_uri,
    "grant_type": "authorization_code"
}
response = requests.post(f"{base_url}/oauth/token", json=json, headers={"Content-Type": "application/json"})
if response.status_code != 200:
    print("Trakt Error: Invalid trakt pin. If you're sure you typed it in correctly your client_id or client_secret may be invalid")
else:
    print (f"Copy the following into your PMM config.yml:")
    print (f"############################################")
    print (f"trakt:")
    print (f"  client_id: {client_id}")
    print (f"  client_secret: {client_secret}")
    print (f"  authorization:")
    print (f"    access_token: {response.json()['access_token']}")
    print (f"    token_type: {response.json()['token_type']}")
    print (f"    expires_in: {response.json()['expires_in']}")
    print (f"    refresh_token: {response.json()['refresh_token']}")
    print (f"    scope: {response.json()['scope']}")
    print (f"    created_at: {response.json()['created_at']}")
    print (f"############################################")
