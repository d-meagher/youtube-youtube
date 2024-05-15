import os
import os.path
import pickle
import argparse
import subprocess

from pytube import YouTube
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

clear = lambda: os.system('clear')
clear()

# If modifying SCOPES, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--credentials-file", help="Path to client_secrets.json", default="client_secrets.json")
    args = parser.parse_args()

    youtube_url = input("Enter the YouTube URL: ")
    title, description, file_path = download_youtube_video(youtube_url)

    service = get_authenticated_service(args)

    # Choose whether or not to change the name, description or category of the video
    print(f"Title: {title}")
    print(f"Description: {description}")
    new_title = input("Enter the new title (leave blank to use the original): ")
    new_description = input("Enter the new description (leave blank to use the original): ")
    category_id = input("Enter the YouTube category ID (leave blank to use the default): ")

    if new_title:
        title = new_title
    if new_description:
        description = new_description
    if category_id:
        category_id = category_id

    # Choose whether the video should be private or public
    privacy_status = input("Enter 'public' or 'private' for the video's privacy status: ").lower()

    upload_video_to_youtube(service, title, description, file_path, privacy_status, category_id)

    # Once the video has been uploaded ask if it should be deleted
    delete_file = input("Do you want to delete the downloaded file? (y/n): ").lower()
    if delete_file == "y":
        os.remove(file_path)
        print("Downloaded file has been deleted.")
    else:
        print("Downloaded file will not be deleted.")

def progress_function(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage_of_completion = bytes_downloaded / total_size * 100
    print(f"Downloaded {percentage_of_completion:.2f}%")

def download_youtube_video(url):
    print("Downloading video...")
    youtube = YouTube(url, on_progress_callback=progress_function)

    # Download the highest quality video stream without audio
    video_stream = youtube.streams.filter(adaptive=True, mime_type='video/webm').first()
    if video_stream:
        video_file = video_stream.download(filename_prefix="video_")
        print("Video stream downloaded.")
    else:
        print("Failed to find a video stream.")
        return None, None, None

    # Download the highest quality audio stream
    audio_streams = youtube.streams.filter(only_audio=True).all()
    if audio_streams:
        # Sort audio streams by bitrate in descending order and select the first one
        audio_stream = sorted(audio_streams, key=lambda x: x.abr, reverse=True)[0]
        audio_file = audio_stream.download(filename_prefix="audio_")
        print("Audio stream downloaded.")
    else:
        print("Failed to find an audio stream.")
        return None, None, None

    # Combine video and audio using ffmpeg
    output_filename = f"{youtube.title}.mp4"
    command = ['ffmpeg', '-i', video_file, '-i', audio_file, '-c:v', 'copy', '-c:a', 'copy', output_filename]
    result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Check if ffmpeg command was successful
    if result.returncode == 0:
        print("Download and merge complete.")
        # Delete intermediate files if option is enabled
        if delete_intermediate_files:
            os.remove(video_file)
            os.remove(audio_file)
            print("Intermediate files deleted.")
        return youtube.title, youtube.description, output_filename
    else:
        print("ffmpeg encountered an error:")
        print("stdout:", result.stdout.decode('utf-8'))
        print("stderr:", result.stderr.decode('utf-8'))
        return None, None, None

def get_authenticated_service(args):
    credentials = None
    # The file token.pickle stores the user's access and refresh tokens, and
    # is created automatically when the authorization flow completes for
    # the first time.
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
            credentials = flow.run_local_server(port=8080)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)

    return build('youtube', 'v3', credentials=credentials)

def upload_video_to_youtube(service, title, description, file_path, privacy_status, category_id):
    request = service.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "categoryId": category_id or "28",
                "description": description,
                "title": title
            },
            "status": {
                "privacyStatus": privacy_status
            }
        },
        media_body=MediaFileUpload(file_path)
    )
    response = request.execute()
    print(f"Video uploaded: {response['snippet']['title']}")

    # Construct the video URL using the video ID from the response
    video_id = response['id']
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"✅ Video Uploaded: {video_url}")


if __name__ == '__main__':
    url = input("Enter the YouTube URL: ")
    title, description, file_path = download_youtube_video(url)
    print(f"Title: {title}")
    print(f"Description: {description}")
    print(f"File Path: {file_path}")