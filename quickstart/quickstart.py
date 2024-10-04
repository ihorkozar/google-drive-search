import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import io
from googleapiclient.http import MediaIoBaseDownload

# Define read-only access scope
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

def download_file(service, file_id, file_name, mime_type):
    # Check if the file is a Google Docs file
    if mime_type in [
        'application/vnd.google-apps.document',  # Google Docs
        'application/vnd.google-apps.sheet',     # Google Sheets
        'application/vnd.google-apps.presentation'  # Google Slides
    ]:
        # Define export MIME types
        export_mime_types = {
            'application/vnd.google-apps.document': 'text/plain',  # Export as txt
            'application/vnd.google-apps.sheet': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # Export as XLSX
            'application/vnd.google-apps.presentation': 'application/pdf'  # Export as PDF
        }
        export_mime_type = export_mime_types[mime_type]

        # Export the file
        request = service.files().export(fileId=file_id, mimeType=export_mime_type)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)

        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Завантаження {int(status.progress() * 100)}%.")

        # Write to file
        with open(f"{file_name}.txt", 'wb') as f:
            f.write(fh.getvalue())
        print(f"Файл '{file_name}' успішно завантажено.")

    else:
        # If it's a regular file, download as media
        request = service.files().get_media(fileId=file_id)
        fh = io.BytesIO()

        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
            print(f"Завантаження {int(status.progress() * 100)}%.")

        # Write to file
        with open(file_name, 'wb') as f:
            f.write(fh.getvalue())
        print(f"Файл '{file_name}' успішно завантажено.")

def main():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("drive", "v3", credentials=creds)

        results = (
            service.files()
            .list(q="name contains 'presale'", pageSize=10, fields="nextPageToken, files(id, name, mimeType)")
            .execute()
        )
        items = results.get("files", [])

        if not items:
            print("No files found.")
            return
        print("Files:")
        for item in items:
            print(f"{item['name']} ({item['id']}) ({item['mimeType']})")
            download_file(service, item['id'], item['name'], item['mimeType'])
    except HttpError as error:
        print(f"An error occurred: {error}")

if __name__ == "__main__":
    main()
