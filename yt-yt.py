import os
import sys
import subprocess
import pickle
import ssl

from pytube import YouTube
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload
from colorama import Fore, Style, init

# Disable SSL verification
ssl._create_default_https_context = ssl._create_unverified_context

DEFAULT_CATEGORY_ID = "28"  # Science & Technology

def clear_terminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def get_authenticated_service(client_secret_file, credentials_file='credentials.pickle'):
    scopes = ["https://www.googleapis.com/auth/youtube.upload"]
    credentials = None

    # Determine the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the full path to the client_secret.json file
    client_secret_full_path = os.path.join(script_dir, client_secret_file)

    if os.path.exists(credentials_file):
        with open(credentials_file, 'rb') as token:
            credentials = pickle.load(token)

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(client_secret_full_path, scopes)
            credentials = flow.run_local_server(port=8080)

        with open(credentials_file, 'wb') as token:
            pickle.dump(credentials, token)

    return build('youtube', 'v3', credentials=credentials)

def print_colored_text(text, color):
    print(f"{color}{text}{Style.RESET_ALL}")

def print_video_quality_info(i, stream):
    if stream is not None:
        mime_type = getattr(stream, 'mime_type', 'N/A')
        if mime_type.startswith('audio'):
            print_colored_text(f"{i}. Audio Stream: Mime Type={mime_type}", Fore.CYAN)
        elif hasattr(stream, 'resolution'):
            resolution = getattr(stream, 'resolution', 'N/A')
            if resolution.startswith('1080p'):
                print_colored_text(f"{i}. Best quality: {resolution} ({mime_type})", Fore.GREEN)
            elif resolution.startswith('720p'):
                print_colored_text(f"{i}. Good quality: {resolution} ({mime_type})", Fore.YELLOW)
            elif resolution.startswith('480p'):
                print_colored_text(f"{i}. Medium quality: {resolution} ({mime_type})", Fore.BLUE)
            elif resolution.startswith('360p'):
                print_colored_text(f"{i}. Low quality: {resolution} ({mime_type})", Fore.BLUE)
            else:
                print_colored_text(f"{i}. Low quality: {resolution} ({mime_type})", Fore.RED)
        else:
            print_colored_text(f"{i}. No resolution info available for this stream.", Fore.RED)
    else:
        print_colored_text(f"{i}. No stream info available.", Fore.RED)

def print_audio_streams(i, stream, bitrate='Unknown'):
    if stream is not None:
        mime_type = stream.mime_type
        print_colored_text(f"{i}. Audio Stream: Mime Type={mime_type}, Bitrate={bitrate}", Fore.CYAN)
    else:
        print_colored_text(f"{i}. No stream info available.", Fore.RED)

def download_best_quality_video_and_audio(url):
    try:
        youtube = YouTube(url)
    except Exception as e:
        print_colored_text(f"Error fetching YouTube URL: {e}", Fore.RED)
        sys.exit(1)

    all_streams = youtube.streams

    print("Available video streams:")
    for i, stream in enumerate(all_streams):
        if stream.video_codec is not None:
            print_video_quality_info(i, stream)

    try:
        video_choice = int(input("Select a video stream by number: "))
        video_stream = all_streams[video_choice]
        video_file = video_stream.download(filename_prefix="video_")
    except Exception as e:
        print_colored_text(f"Error downloading video stream: {e}", Fore.RED)
        sys.exit(1)

    print("\nAvailable audio streams:")
    audio_streams = youtube.streams.filter(only_audio=True)
    for i, stream in enumerate(audio_streams):
        bitrate = stream.abr if hasattr(stream, 'abr') else 'Unknown'
        print_audio_streams(i, stream, bitrate)

    try:
        audio_choice = int(input("\nSelect an audio stream by number: "))
        audio_stream = audio_streams[audio_choice]
        audio_file = audio_stream.download(filename_prefix="audio_")
    except Exception as e:
        print_colored_text(f"Error downloading audio stream: {e}", Fore.RED)
        sys.exit(1)

    return video_file, audio_file, youtube.title, youtube.description


def combine_video_and_audio(video_file, audio_file, output_filename):
    command = ['ffmpeg', '-i', video_file, '-i', audio_file, '-c:v', 'copy', '-c:a', 'aac', '-loglevel', 'error', output_filename]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print_colored_text(f"Error combining video and audio: {e}", Fore.RED)
        sys.exit(1)

def upload_to_youtube(service, title, description, file_path, privacy_status, category_id):
    try:
        request = service.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "categoryId": category_id,
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
        print(f"URL: https://www.youtube.com/watch?v={response['id']}")
    except Exception as e:
        print_colored_text(f"Error uploading video: {e}", Fore.RED)
        sys.exit(1)

def get_user_input(prompt, default=None):
    user_input = input(prompt)
    return user_input if user_input else default

def get_privacy_status():
    privacy_options = ["public", "private", "unlisted"]
    print(Fore.LIGHTGREEN_EX + "Select the privacy status:" + Style.RESET_ALL)
    for i, option in enumerate(privacy_options, 1):
        print(f"{i}. {option}")

    while True:
        try:
            privacy_choice = int(input(Fore.LIGHTGREEN_EX + "Enter the number corresponding to your choice: " + Style.RESET_ALL))
            if 1 <= privacy_choice <= len(privacy_options):
                return privacy_options[privacy_choice - 1]
            else:
                print(Fore.RED + "Invalid choice. Please enter a number between 1 and 3." + Style.RESET_ALL)
        except ValueError:
            print(Fore.RED + "Invalid input. Please enter a number." + Style.RESET_ALL)

def delete_files(video_file, audio_file, output_filename):
    print(Fore.LIGHTBLUE_EX + "\nWould you like to delete any files?" + Style.RESET_ALL)
    print(Fore.LIGHTBLUE_EX + "1. Combined file" + Style.RESET_ALL)
    print(Fore.LIGHTBLUE_EX + "2. Separate video and audio files" + Style.RESET_ALL)
    print(Fore.LIGHTBLUE_EX + "3. All files" + Style.RESET_ALL)
    print(Fore.LIGHTBLUE_EX + "4. No deletion" + Style.RESET_ALL)
    choice = input(Fore.LIGHTGREEN_EX + "Enter your choice (1-4): " + Style.RESET_ALL)

    try:
        if choice == "1":
            os.remove(output_filename)
            print(Fore.LIGHTBLUE_EX + "Combined file deleted." + Style.RESET_ALL)
        elif choice == "2":
            os.remove(video_file)
            os.remove(audio_file)
            print(Fore.LIGHTBLUE_EX + "Separate video and audio files deleted." + Style.RESET_ALL)
        elif choice == "3":
            os.remove(output_filename)
            os.remove(video_file)
            os.remove(audio_file)
            print(Fore.LIGHTBLUE_EX + "All files deleted." + Style.RESET_ALL)
        else:
            print(Fore.LIGHTBLUE_EX + "No files deleted." + Style.RESET_ALL)
    except Exception as e:
        print_colored_text(f"Error deleting files: {e}", Fore.RED)

def main():
    clear_terminal()
    init(autoreset=True)

    url = get_user_input(Fore.LIGHTGREEN_EX + "Enter the YouTube URL: " + Style.RESET_ALL)
    video_file, audio_file, current_title, current_description = download_best_quality_video_and_audio(url)
    print(f"Video file saved as: {video_file}")
    print(f"Audio file saved as: {audio_file}")

    service = get_authenticated_service('client_secret.json')

    title_prompt = Fore.LIGHTGREEN_EX + f"Enter the new title (or press enter to keep the original *{current_title}*): " + Style.RESET_ALL
    description_prompt = Fore.LIGHTGREEN_EX + f"Enter the new description (or press enter to keep the original *{current_description}*): " + Style.RESET_ALL

    title = get_user_input(title_prompt, current_title)
    description = get_user_input(description_prompt, current_description)
    category_id = get_user_input(Fore.LIGHTGREEN_EX + f"Enter the YouTube category ID (or press enter to use default {DEFAULT_CATEGORY_ID}): " + Style.RESET_ALL, DEFAULT_CATEGORY_ID)

    privacy_status = get_privacy_status()

    # Create a valid filename from the title
    output_filename = f"{title.replace(' ', '_').replace('/', '_')}.mp4"
    combine_video_and_audio(video_file, audio_file, output_filename)

    upload_to_youtube(service, title, description, output_filename, privacy_status, category_id)

    delete_files(video_file, audio_file, output_filename)

if __name__ == "__main__":
    main()