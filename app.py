from flask import Flask, request, jsonify
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import os

app = Flask(__name__)

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail(user_email):
    token_file = f"token_{user_email.replace('@', '_').replace('.', '_')}.json"
    creds = None

    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
        creds = flow.run_local_server(port=8502)
        with open(token_file, "w") as token:
            token.write(creds.to_json())

    return creds

@app.route("/fetch-emails", methods=["POST"])
def fetch_emails():
    data = request.json
    user_email = data.get("email")
    creds = authenticate_gmail(user_email)

    service = build("gmail", "v1", credentials=creds)
    results = service.users().messages().list(userId="me", labelIds=["INBOX"], maxResults=5).execute()
    messages = results.get("messages", [])

    emails = []
    for msg in messages:
        message = service.users().messages().get(userId="me", id=msg["id"], format="full").execute()
        headers = message["payload"]["headers"]
        subject = next((header["value"] for header in headers if header["name"] == "Subject"), "No Subject")
        snippet = message.get("snippet", "")
        emails.append({"subject": subject, "snippet": snippet})

    return jsonify(emails)

if __name__ == "__main__":
    app.run(debug=True)
