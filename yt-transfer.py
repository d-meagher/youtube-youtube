from pytube import YouTube
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import os.path
import pickle
import argparse

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['<https://www.googleapis.com/auth/youtube.upload>']

def get_authenticated_service(args):
    credentials = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                args.credentials_file, SCOPES)
            credentials = flow.run_console()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)

    return build('youtube', 'v3', credentials=credentials)

def download_youtube_video(url):
    youtube = YouTube(url)
    video = youtube.streams.get_highest_resolution()
    video.download()
    return youtube.title, youtube.description, video.default_filename

def upload_video_to_youtube(service, title, description, file_path):
    request = service.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "categoryId": "22",
                "description": description,
                "title": title
            },
            "status": {
                "privacyStatus": "private"
            }
        },
        media_body=MediaFileUpload(file_path)
    )
    response = request.execute()
    print(f"Video uploaded: {response['snippet']['title']}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--credentials-file", help="Path to client_secrets.json",
                        default="client_secrets.json")
    args = parser.parse_args()

    youtube_url = input("Enter the YouTube URL: ")
    title, description, file_path = download_youtube_video(youtube_url)

    service = get_authenticated_service(args)

    print(f"Title: {title}")
    print(f"Description: {description}")
    new_title = input("Enter the new title (leave blank to use the original): ")
    new_description = input("Enter the new description (leave blank to use the original): ")

    if new_title:
        title = new_title
    if new_description:
        description = new_description

    upload_video_to_youtube(service, title, description, file_path)

if __name__ == '__main__':
    main()
