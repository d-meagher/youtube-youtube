# YouTube Video Transfer Tool

This project is a Python-based tool designed to download YouTube videos and upload them to a new YouTube channel with customisable titles and descriptions. It utilises the Google API for authentication and video upload.

## Features

- Choose your video and audio download quality.
- Use ffmpeg to combine the downloaded files.
- Upload videos to a new YouTube channel with customisable title, description and [categories](https://gist.github.com/dgp/1b24bf2961521bd75d6c).
- Supports OAuth 2.0 for secure authentication.

## Prerequisites

- Python 3.6 or higher.
- A Google account with access to the YouTube Data API v3.
- A YouTube channel where you want to upload the videos.

## Installation

1. Clone the repository to your local machine.
2. Ensure you have Python 3.6 or higher installed.
3. Install the required Python packages by running `pip install -r requirements.txt` in your terminal.

## Usage

1. Run the script with the command `python yt-yt.py`.
2. Enter the YouTube URL of the video you want to download and upload.
3. Follow the prompts to enter a new title and description for the video.
4. Choose whether to make the video public, private or unlisted.
5. The script will download the video, and then upload it to your specified YouTube channel with the new title, description, and privacy setting.
6. Choose whether to delete some, all or none of the downloaded files.

## Configuration

- The script uses a `client_secrets.json` file for OAuth 2.0 authentication. Ensure this file is correctly configured with your Google API credentials.
- The script saves downloaded videos in the current working directory. You can change this by modifying the script.

## Contributing

Contributions to improve the tool are welcome. Please submit a pull request with your changes.

## License

This project is licensed under the MIT License.