import random
from gtts import gTTS
from moviepy.editor import *
from google.oauth2.credentials import Credentials
from PIL import Image, ImageDraw, ImageFont
import google.auth
from google.auth.transport.requests import Request
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload
import json
import os
import google_auth_oauthlib.flow

# Function to generate audio from text
def generate_audio(text, file_name):
    tts = gTTS(text=text, lang='en', slow=False)
    tts.save(file_name)

# Function to create an image with text
def create_image(text, file_name):
    img = Image.new('RGB', (1280, 720), color=(73, 109, 137))  # Background color
    d = ImageDraw.Draw(img)
    font_size = 200  # Initial font size (large)
    font = ImageFont.truetype("arial.ttf", font_size)  # Load the font with the initial size
    
    # Use textbbox to calculate the width and height of the text
    bbox = d.textbbox((0, 0), text, font=font)  # Calculate text size
    text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]  # Width and height of text

    # Adjust the font size to fit the text in the image width
    while text_width > img.width - 40 and font_size > 35:  # Set minimum font size limit to 35
        font_size -= 5  # Decrease the font size by 5
        font = ImageFont.truetype("arial.ttf", font_size)  # Update the font
        bbox = d.textbbox((0, 0), text, font=font)  # Recalculate text size
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]  # Recalculate width and height

    # Split the text into multiple lines
    lines = []
    words = text.split(' ')
    current_line = ""
    for word in words:
        if len(current_line + " " + word) < 35:  # Maximum of 35 characters per line
            current_line += " " + word
        else:
            lines.append(current_line.strip())
            current_line = word
    if current_line:
        lines.append(current_line.strip())

    # Center the lines in the image
    y_position = (img.height - len(lines) * font_size) // 2
    for line in lines:
        bbox = d.textbbox((0, 0), line, font=font)
        text_width, text_height = bbox[2] - bbox[0], bbox[3] - bbox[1]
        position = ((img.width - text_width) // 2, y_position)
        d.text(position, line, fill=(255, 255, 255), font=font)
        y_position += text_height + 10  # Space between lines

    img.save(file_name)

# Function to create a video from images and audio
def create_video(images, audios, background_music_path, output_file):
    clips = []
    
    # Load background music
    background_music = AudioFileClip(background_music_path)
    
    for i, img in enumerate(images):
        audio_duration = AudioFileClip(audios[i]).duration  # Get audio duration
        background_music_duration = AudioFileClip(background_music_path).duration  # Background music duration
        
        # If background music is longer than audio
        if background_music_duration > audio_duration:
            background_music = background_music.subclip(0, audio_duration)  # Trim background music
        
        clip = ImageClip(img).set_duration(audio_duration)  # Set image duration to audio duration
        clips.append(clip)

    # Concatenate image clips
    video = concatenate_videoclips(clips, method="compose")
    
    # Combine the audio files
    audio_clips = [AudioFileClip(audio) for audio in audios]
    final_audio = concatenate_audioclips(audio_clips)
    
    # Adjust the volume of the background music
    background_music = background_music.volumex(0.2)  # Reduce background music to 20% of the original volume
    
    # Extend background music by 10 seconds after the last audio
    video_duration = final_audio.duration  # Total audio duration
    extended_background_music = background_music.subclip(0, video_duration + 10)  # Add 10 seconds after audio
    
    # Set the audio of the video as the combined audio: prayer audio + background music
    video = video.set_audio(CompositeAudioClip([final_audio, extended_background_music]))  # Merge the audio

    video.write_videofile(output_file, fps=24)

# Function to read prayers from a file
def read_prayers_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        prayers = file.readlines()
    # Clean the line breaks
    prayers = [prayer.strip() for prayer in prayers]
    return prayers

# Function to get the next sequence of prayers
def get_next_sequence():
    progress_path = "progress.json"
    
    if os.path.exists(progress_path):
        with open(progress_path, "r") as file:
            progress = json.load(file)
        current_index = progress["index"]
    else:
        current_index = 0
    
    prayers = read_prayers_from_file("prayers.txt")
    total_prayers = len(prayers)
    
    sequence = []
    for i in range(3):
        sequence.append(prayers[(current_index + i) % total_prayers])
    
    new_index = (current_index + 3) % total_prayers
    with open(progress_path, "w") as file:
        json.dump({"index": new_index}, file)
    
    return sequence

# Function to get YouTube credentials (or load existing ones)
def get_youtube_credentials():
    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    CREDENTIALS_FILE = "credentials.json"  # Path to save credentials
    
    credentials = None
    
    # Check if the credentials file exists
    if os.path.exists(CREDENTIALS_FILE):
        # Load the credentials
        with open(CREDENTIALS_FILE, 'r') as token:
            credentials = Credentials.from_authorized_user_file(CREDENTIALS_FILE, SCOPES)
    
    # If no credentials or if they are expired
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())  # Refresh the credentials if expired
        else:
            flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                "your_credentials_file_path", SCOPES
            )
            credentials = flow.run_local_server(port=8080)  # Request authentication if needed

        # Save credentials for future use
        with open(CREDENTIALS_FILE, 'w') as token:
            token.write(credentials.to_json())

    return credentials

def upload_video(credentials, video_file, title, description):
    youtube = googleapiclient.discovery.build("youtube", "v3", credentials=credentials)

    request = youtube.videos().insert(
        part="snippet, status",
        body={
            "snippet": {
                "title": title,
                "description": description,
                "tags": ["prayers", "christianity", "religion", "spirituality"],
            },
            "status": {
                "privacyStatus": "public",  # Video set to public
            },
        },
        media_body=MediaFileUpload(video_file)
    )

    response = request.execute()  # Execute the upload
    print(f"Video '{title}' uploaded to YouTube successfully! ID: {response['id']}")

# Main function
def main():
    texts = get_next_sequence()  # Get the next 3 prayers sequentially
    images = []
    audios = []
    
    # Create images and save audio for each prayer
    for i, text in enumerate(texts):
        image_name = f"image_{i}.png"
        audio_name = f"audio_{i}.mp3"
        create_image(text, image_name)  # Create image with prayer
        generate_audio(text, audio_name)  # Generate audio for prayer
        images.append(image_name)
        audios.append(audio_name)

    # Create the video
    output_file = "final_video.mp4"
    background_music_path = "background_music_path"  # Path to the background music file
    create_video(images, audios, background_music_path, output_file)
    
    # Upload the video to YouTube
    credentials = get_youtube_credentials()
    title = "Prayer of the Day"
    description = "Watch and reflect on today's prayer."
    upload_video(credentials, output_file, title, description)

# Run the script
if __name__ == "__main__":
    main()
