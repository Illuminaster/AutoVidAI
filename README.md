# AutoVidAI
"AI Video Creator is an intelligent automation tool that simplifies video creation and posting. With advanced AI algorithms, it generates engaging videos based on provided content and automatically uploads them to YouTube. Whether it's generating voiceovers, adding backgrounds, or synchronizing audio with visuals, AI Video Creator streamlines the entire process, saving you time while ensuring high-quality, consistent uploads. Perfect for content creators, businesses, and marketers who want to boost their YouTube presence effortlessly."


This script automates the process of creating a video from prayers, adding background music, and uploading it to YouTube. Here’s a breakdown of how it works and the steps the user must follow to use it:

Workflow:
Generate Audio: The script uses the gTTS (Google Text-to-Speech) library to convert the prayer texts into audio files (.mp3 format).
Create Image: It generates images with text from the prayers and adjusts the font size to fit the text within the image.
Create Video: The script combines the generated images and audio files into a video. It also adds background music and adjusts the volume.
Upload to YouTube: After generating the video, it uploads the video to YouTube using the YouTube API.
Steps to Use:
Install Dependencies: You need to install the required libraries if you haven't already:

pip install gtts moviepy google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client pillow

Google API Setup:
To upload the video to YouTube, you need to set up the YouTube API:

Go to the Google Developers Console.
Create a project and enable the YouTube Data API v3.
Create OAuth 2.0 credentials and download the credentials.json file.
Place the credentials.json file in your working directory.
When running the script for the first time, it will prompt you to authenticate your Google account via a browser. After authentication, the credentials will be saved for future use.
Prepare Your Files:

Create a text file (prayers.txt) containing the prayers you want to use. Each prayer should be on a new line.
Provide a path to a background music file (in .mp3 format) in the background_music_path variable.
Run the Script:
Once everything is set up, run the script. It will:

Read the next three prayers from prayers.txt.
Generate images and audio files for those prayers.
Create a video by combining the images, audio, and background music.
Upload the video to YouTube with the title "Prayer of the Day" and the description "Watch and reflect on today's prayer."
Customization:
YouTube Video Title and Description: You can change the title and description variables inside the main() function to personalize the video.
Font and Image Size: You can adjust the font size and background color by modifying the create_image function.
Background Music: You can specify any .mp3 file to use as background music.
Notes:
Ensure that the credentials.json file is correct and available in your project folder. If it's missing or invalid, the script will attempt to authenticate via the Google OAuth flow.
The script assumes a public privacy status for the uploaded video. If you want to make it private or unlisted, change the "privacyStatus": "public" line inside the upload_video function.
With these steps, the user will be able to automate the creation and uploading of prayer videos to YouTube using this script.
