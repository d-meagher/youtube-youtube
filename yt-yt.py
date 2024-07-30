import os
import sys
import subprocess
import pickle
import ssl

from yt_dlp import YoutubeDL
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
from colorama import Fore, Style, init

# Disable SSL verification
ssl._create_default_https_context = ssl._create_unverified_context

DEFAULT_CATEGORY_ID = "28"  # Science & Technology
SEPARATOR = Style.RESET_ALL + "━━━━━━━━━━━━━━━━━━━━━━━━━━━" + Style.RESET_ALL
SHORT_SEPARATOR = Style.RESET_ALL + "━━━━━━━━━━━━━━" + Style.RESET_ALL

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

def sort_video_formats(formats):
    resolution_order = {
        '2160p': 8,
        '1440p': 7,
        '1080p': 6,
        '720p': 5,
        '480p': 4,
        '360p': 3,
        '240p': 2,
        '144p': 1
    }
    return sorted(formats, key=lambda f: resolution_order.get(f.get('format_note'), 0), reverse=True)

def sort_audio_formats(formats):
    return sorted(formats, key=lambda f: int(f.get('abr', 0)), reverse=True)

def print_video_quality_info(i, format):
    if format is not None:
        mime_type = format.get('ext', 'N/A')
        resolution = format.get('format_note', 'N/A')
        if resolution == 'N/A':
            return  # Skip unknown quality
        if resolution == '2160p':
            print_colored_text(f"{i}. Ultra HD quality: {resolution} ({mime_type})", Fore.GREEN)
        elif resolution == '1440p':
            print_colored_text(f"{i}. Quad HD quality: {resolution} ({mime_type})", Fore.GREEN)
        elif resolution == '1080p':
            print_colored_text(f"{i}. Best quality: {resolution} ({mime_type})", Fore.MAGENTA)
        elif resolution == '720p':
            print_colored_text(f"{i}. Good quality: {resolution} ({mime_type})", Fore.YELLOW)
        elif resolution == '480p':
            print_colored_text(f"{i}. Medium quality: {resolution} ({mime_type})", Fore.BLUE)
        elif resolution == '360p':
            print_colored_text(f"{i}. Low quality: {resolution} ({mime_type})", Fore.RED)
        elif resolution == '240p':
            print_colored_text(f"{i}. Low quality: {resolution} ({mime_type})", Fore.RED)
        elif resolution == '144p':
            print_colored_text(f"{i}. Low quality: {resolution} ({mime_type})", Fore.RED)
        elif resolution == 'Premium':
            print_colored_text(f"{i}. Premium quality: {resolution} ({mime_type})", Fore.CYAN)
        else:
            print_colored_text(f"{i}. Unknown quality: {resolution} ({mime_type})", Fore.RED)
    else:
        print_colored_text(f"{i}. No format info available.", Fore.RED)

def print_audio_streams(i, format):
    if format is not None:
        mime_type = format.get('ext', 'N/A')
        bitrate = format.get('abr', 'Unknown')

        # Skip unknown quality
        if bitrate == 'Unknown' or bitrate is None:
            return

        # Determine quality based on bitrate
        try:
            bitrate_value = int(bitrate)
            if bitrate_value >= 160:
                quality = "High quality"
                color = Fore.GREEN
            elif bitrate_value >= 128:
                quality = "Medium quality"
                color = Fore.YELLOW
            else:
                quality = "Low quality"
                color = Fore.RED
        except ValueError:
            quality = "Unknown quality"
            color = Fore.CYAN

        print_colored_text(f"{i}. {quality}: {bitrate}kbps ({mime_type})", color)
    else:
        print_colored_text(f"{i}. No format info available.", Fore.RED)

def download_best_quality_video_and_audio(url):
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'noplaylist': True,
        'quiet': True,
        'outtmpl': '%(title)s.%(ext)s'
    }

    with YoutubeDL(ydl_opts) as ydl:
        try:
            info_dict = ydl.extract_info(url, download=False)
        except Exception as e:
            print_colored_text(f"Error fetching YouTube URL: {e}", Fore.RED)
            sys.exit(1)

        video_formats = [f for f in info_dict['formats'] if f.get('vcodec') != 'none' and f.get('format_note') != 'N/A']
        audio_formats = [f for f in info_dict['formats'] if f.get('acodec') != 'none' and f.get('abr') is not None]

        # Sort formats by quality
        video_formats = sort_video_formats(video_formats)
        audio_formats = sort_audio_formats(audio_formats)

        print("\nAvailable video streams:")
        print(SEPARATOR)
        for i, format in enumerate(video_formats):
            print_video_quality_info(i, format)
        print(SEPARATOR)

        try:
            video_choice = int(input("\nSelect a video stream by number: ❯ "))
            video_format = video_formats[video_choice]
            ydl.download([url])
            video_file = ydl.prepare_filename(info_dict)
        except Exception as e:
            print_colored_text(f"Error downloading video stream: {e}", Fore.RED)
            sys.exit(1)

        print("\nAvailable audio streams:")
        print(SEPARATOR)
        for i, format in enumerate(audio_formats):
            print_audio_streams(i, format)
        print(SEPARATOR)

        try:
            audio_choice = int(input("\nSelect an audio stream by number: ❯ "))
            audio_format = audio_formats[audio_choice]
            ydl.download([url])
            audio_file = ydl.prepare_filename(info_dict)
        except Exception as e:
            print_colored_text(f"Error downloading audio stream: {e}", Fore.RED)
            sys.exit(1)

        return video_file, audio_file, info_dict['title'], info_dict['description']

def combine_video_and_audio(video_file, audio_file, output_filename):
    command = ['ffmpeg', '-i', video_file, '-i', audio_file, '-c:v', 'copy', '-c:a', 'aac', '-loglevel', 'error', output_filename]
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print_colored_text(f"Error combining video and audio: {e}", Fore.RED)
        sys.exit(1)

def upload_to_youtube(service, title, description, file_path, privacy_status, category_id):
    try:
        media = MediaFileUpload(file_path, chunksize=-1, resumable=True)
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
            media_body=media
        )

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"Uploaded {int(status.progress() * 100)}%")

        print(f"Video uploaded: {response['snippet']['title']}")
        print(f"URL: https://www.youtube.com/watch?v={response['id']}")
    except HttpError as e:
        if e.resp.status == 403 and 'quotaExceeded' in e.content.decode():
            print_colored_text("Error uploading video: Quota exceeded. Please try again later or request a quota increase.", Fore.LIGHTRED_EX)
        else:
            print_colored_text(f"Error uploading video: {e}", Fore.LIGHTRED_EX)
        sys.exit(1)
    except Exception as e:
        print_colored_text(f"Error uploading video: {e}", Fore.LIGHTRED_EX)
        sys.exit(1)

def get_user_input(prompt, default=None):
    user_input = input(prompt + Style.RESET_ALL)
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
            if os.path.exists(output_filename):
                os.remove(output_filename)
                print(Fore.LIGHTBLUE_EX + "Combined file deleted." + Style.RESET_ALL)
            else:
                print(Fore.RED + f"File '{output_filename}' does not exist." + Style.RESET_ALL)
        elif choice == "2":
            if os.path.exists(video_file):
                os.remove(video_file)
            else:
                print(Fore.RED + f"File '{video_file}' does not exist." + Style.RESET_ALL)
            if os.path.exists(audio_file):
                os.remove(audio_file)
            else:
                print(Fore.RED + f"File '{audio_file}' does not exist." + Style.RESET_ALL)
            print(Fore.LIGHTBLUE_EX + "Separate video and audio files deleted." + Style.RESET_ALL)
        elif choice == "3":
            if os.path.exists(output_filename):
                os.remove(output_filename)
            else:
                print(Fore.RED + f"File '{output_filename}' does not exist." + Style.RESET_ALL)
            if os.path.exists(video_file):
                os.remove(video_file)
            else:
                print(Fore.RED + f"File '{video_file}' does not exist." + Style.RESET_ALL)
            if os.path.exists(audio_file):
                os.remove(audio_file)
            else:
                print(Fore.RED + f"File '{audio_file}' does not exist." + Style.RESET_ALL)
            print(Fore.LIGHTBLUE_EX + "All files deleted." + Style.RESET_ALL)
        else:
            print(Fore.LIGHTBLUE_EX + "No files deleted." + Style.RESET_ALL)
    except Exception as e:
        print_colored_text(f"Error deleting files: {e}", Fore.RED)

def main():
    clear_terminal()
    init(autoreset=True)

    print(Fore.LIGHTGREEN_EX + "YouTube Video Transfer Tool" + Style.RESET_ALL)
    print(SEPARATOR)

    url = get_user_input(Fore.LIGHTGREEN_EX + "\nEnter the YouTube URL: " + Style.RESET_ALL + "❯ ")
    video_file, audio_file, current_title, current_description = download_best_quality_video_and_audio(url)
    print(f"\nVideo file saved as: {video_file}")
    print(f"Audio file saved as: {audio_file}")

    service = get_authenticated_service('client_secret.json')

    print(Fore.LIGHTGREEN_EX + "\nVideo Metadata" + Style.RESET_ALL)
    print(SHORT_SEPARATOR)

    title_prompt = (Fore.LIGHTGREEN_EX + "Enter the new title (or press enter to keep the original):\n" +
                    Fore.LIGHTYELLOW_EX + f"➤ {current_title}\n" + Style.RESET_ALL + "❯ ")
    description_prompt = (Fore.LIGHTGREEN_EX + "Enter the new description (or press enter to keep the original):\n" +
                          Fore.LIGHTYELLOW_EX + f"➤ {current_description}\n" + Style.RESET_ALL + "❯ ")

    title = get_user_input(title_prompt, current_title)
    description = get_user_input(description_prompt, current_description)
    category_id = get_user_input(Fore.LIGHTGREEN_EX + f"\nEnter the YouTube category ID (or press enter to use default {DEFAULT_CATEGORY_ID}): " + Style.RESET_ALL + "❯ ", DEFAULT_CATEGORY_ID)

    privacy_status = get_privacy_status()

    # Create a valid filename from the title
    output_filename = f"{title.replace(' ', '_').replace('/', '_')}.mp4"

    if os.path.exists(output_filename):
        overwrite = get_user_input(Fore.LIGHTRED_EX + f"\nFile '{output_filename}' already exists. Overwrite? [y/N] " + Style.RESET_ALL + "❯ ", "n")
        if overwrite.lower() != 'y':
            print(Fore.LIGHTRED_EX + "Not overwriting - using existing file for upload" + Style.RESET_ALL)
        else:
            combine_video_and_audio(video_file, audio_file, output_filename)
    else:
        combine_video_and_audio(video_file, audio_file, output_filename)

    print(Fore.LIGHTGREEN_EX + "\nUploading Video" + Style.RESET_ALL)
    print(SHORT_SEPARATOR)

    upload_to_youtube(service, title, description, output_filename, privacy_status, category_id)

    delete_files(video_file, audio_file, output_filename)

if __name__ == "__main__":
    main()