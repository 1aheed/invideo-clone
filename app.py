import gradio as gr
import json
import requests
import random
import subprocess
import os

from gtts import gTTS
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips

# Function to fetch portrait videos from Pexels 
def get_pexels_video(keyword):
    headers = {"Authorization": "8LpygbUwv484x1RkoAJuKH08yhmBKrYpJ0MlLSLboSS736mfs1dODS3v"} 
    params = {
        "query": keyword, 
        "per_page": 20,  # Increase the per_page parameter to get more results
        "orientation": "portrait",  # Fetch portrait videos
        "size": "large",
    }
    response = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params)

    if response.status_code == 200:
        videos = response.json()['videos']
        portrait_videos = [video for video in videos if video['width'] < video['height']]  # Check for portrait videos
        if portrait_videos:
            selected_video = random.choice(portrait_videos)
            return selected_video['video_files'][0]['link']
        else:
            print(f"No portrait video found on Pexels for {keyword}")
            return None
    else:
        print("Failed to fetch video from Pexels")
        return None

# Function to generate voiceover using gTTS
def generate_voiceover(text, filename, speed=1.0):
    tts = gTTS(text=text, lang='en', slow=False)
    tts.save(filename)

# Function to generate video content and create data.json
def generate_video_content(topic):
    api_key = "AIzaSyAtVhAjcUi7tHYnYZTWA4_L2ExvsAeupQY"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.0-pro:generateContent?key={api_key}"

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": f"you are a professional youtube creator, create a one minute short video on {topic} and the keyword under each scene will be used for pexels search query so give precise keyword for each secene and create very short scene with a flow. Give upto 15 related tags. Give response in this json format and give just the json: {{    \"title_filename\": \"dont use colons or speacial characters here",    \"description\": \"\",    \"video\": [      {{        \"scene\": \"\",        \"keyword\": \"\",        \"voiceover\": \"\"      }}   ],    \"tags\": [\"\", \"\", \"\"]  }}"
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.9,
            "topK": 1,
            "topP": 1,
            "maxOutputTokens": 2048,
            "stopSequences": []
        },
        "safetySettings": [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_NONE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_NONE"
            }
        ]
    }

    headers = {
        'Content-Type': 'application/json'
    }

    response = requests.post(url, headers=headers, json=payload)

    if response.status_code == 200:
        try:
            with open("data.json", "w") as f:
                f.write(response.json()["candidates"][0]["content"]["parts"][0]["text"])
            print("Data saved successfully as data.json")
        except KeyError:
            print("Error: Could not find the desired data in the response")
    else:
        print("Error occurred while fetching data")

# Function to concatenate videos using FFmpeg
def concatenate_videos_ffmpeg(scene_videos, output_filename):
    # Write scene_videos to temporary files
    temp_filenames = []
    for i, video_clip in enumerate(scene_videos):
        temp_filename = f'temp_video_{i}.mp4'
        video_clip.write_videofile(temp_filename, codec="libx264", audio_codec="aac", temp_audiofile="temp-audio.m4a", remove_temp=True, verbose=False)
        temp_filenames.append(temp_filename)

    # Create a text file containing the list of videos to concatenate
    with open('video_list.txt', 'w') as f:
        for temp_filename in temp_filenames:
            f.write(f"file '{temp_filename}'\n")

    # Use FFmpeg to concatenate the videos without resizing
    subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'video_list.txt', '-vf', 'scale=1080:1920', '-c:a', 'aac', '-b:a', '256k', '-c:v', 'libx264', '-preset', 'medium', output_filename])

    # Clean up the video list file and temporary video files
    os.remove('video_list.txt')
    for temp_filename in temp_filenames:
        os.remove(temp_filename)

# Function to process video
def process_video(topic):
    generate_video_content(topic)

    # Load JSON data
    with open('data.json', 'r') as f:
        data = json.load(f)

    # Extract title, description, and tags
    title_filename = data.get('title_filename', '')
    description = data.get('description', '')
    tags = ", ".join(data.get('tags', []))

    # Step 2: Generate Voiceover and get duration
    scene_info = []
    for scene in data['video']:
        voiceover_text = scene['voiceover']
        voiceover_filename = f"{scene['scene']}_voiceover.mp3"
        generate_voiceover(voiceover_text, voiceover_filename)
        voiceover_duration = AudioFileClip(voiceover_filename).duration
        scene_info.append({'scene': scene['scene'], 'voiceover_filename': voiceover_filename, 'voiceover_duration': voiceover_duration, 'keyword': scene['keyword']})

    # Step 3: Fetch videos from Pexels based on portrait orientation
    for scene in scene_info:
        video_urls = [get_pexels_video(scene['keyword']) for _ in range(3)]  # Fetch 3 videos for each scene
        video_filenames = []
        for video_url in video_urls:
            if video_url:
                # Download video file locally
                video_filename = f"{scene['scene']}_video_{len(video_filenames)}.mp4"
                with open(video_filename, 'wb') as f:
                    f.write(requests.get(video_url).content)
                video_filenames.append(video_filename)
        scene['video_filenames'] = video_filenames

    # Step 4: Create Scene Videos without resizing
    scene_videos = []
    for scene in scene_info:
        video_clips = []
        for video_filename in scene['video_filenames']:
            video_clip = VideoFileClip(video_filename)
            video_clips.append(video_clip)
        concatenated_clip = concatenate_videoclips(video_clips)
        # Trim the concatenated clip to match the voiceover duration
        concatenated_clip = concatenated_clip.subclip(0, scene['voiceover_duration'])
        # Add audio to video clip
        concatenated_clip = concatenated_clip.set_audio(AudioFileClip(scene['voiceover_filename']))
        scene_videos.append(concatenated_clip)

    final_filename = title_filename + '.mp4'
    concatenate_videos_ffmpeg(scene_videos, final_filename)

    # Clean up downloaded files
    for scene in scene_info:
        os.remove(scene['voiceover_filename'])
        for video_filename in scene['video_filenames']:
            os.remove(video_filename)

    return final_filename, title_filename, description, tags

iface = gr.Interface(
    fn=process_video,
    inputs="text",
    outputs=["video", "text", "text", "text"],
    description="Generate a free video just from a topic for free! This is a prototype if you want for long videos with elevenlabs voice, contact me I have a code ready for it.",
    title="Text to YouTube Video"
)

iface.launch()
