import gradio as gr
import json
import requests
import random
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip
from gtts import gTTS
import os

# Function to generate voiceover using gTTS
def generate_voiceover(text, filename, speed=1.0):
    tts = gTTS(text=text, lang='en', slow=False)
    tts.save(filename)

# Function to fetch landscape videos from Pexels 
def get_pexels_video(keyword):
    headers = {"Authorization": "8LpygbUwv484x1RkoAJuKH08yhmBKrYpJ0MlLSLboSS736mfs1dODS3v"} 
    params = {
        "query": keyword, 
        "per_page": 20,  # Increase the per_page parameter to get more results
        "orientation": "landscape", 
        "size": "large"
    }
    response = requests.get("https://api.pexels.com/videos/search", headers=headers, params=params)

    if response.status_code == 200:
        videos = response.json()['videos']
        landscape_videos = [video for video in videos if video['width'] > video['height']]
        if landscape_videos:
            selected_video = random.choice(landscape_videos)
            return selected_video['video_files'][0]['link']
        else:
            print(f"No landscape video found on Pexels for {keyword}")
            return None
    else:
        print("Failed to fetch video from Pexels")
        return None

# Step 1: Generate video content and create data.json
def generate_video_content(topic):
    api_key = "AIzaSyAtVhAjcUi7tHYnYZTWA4_L2ExvsAeupQY"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.0-pro:generateContent?key={api_key}"

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": f"you are a professional youtube creator, create a video on {topic} and the keyword under each scene will be used for pexels search query so give precise keyword for each secene. Give upto 15 related tags. Always create in this json format and give just the json: {{    \"title_filename\": \"\",    \"description\": \"\",    \"video\": [      {{        \"scene\": \"\",        \"keyword\": \"\",        \"voiceover\": \"\"      }}   ],    \"tags\": [\"\", \"\", \"\"]  }}"
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

    # Step 3: Fetch videos from Pexels based on default orientation (landscape)
    for scene in scene_info:
        video_url = get_pexels_video(scene['keyword'])
        if video_url:
            # Download video file locally
            video_filename = f"{scene['scene']}_video.mp4"
            with open(video_filename, 'wb') as f:
                f.write(requests.get(video_url).content)
            scene['video_filename'] = video_filename

    # Step 4: Create Scene Videos
    scene_videos = []
    for scene in scene_info:
        video_clip = VideoFileClip(scene['video_filename']).subclip(0, scene['voiceover_duration'])
        video_clip = video_clip.set_audio(AudioFileClip(scene['voiceover_filename']))
        video_clip = video_clip.resize((1920, 1080))
        scene_videos.append(video_clip)

    final_video = concatenate_videoclips(scene_videos)
    final_filename = title_filename + '.mp4'
    final_video.write_videofile(final_filename, codec='libx264', fps=24)

    # Clean up downloaded files
    for scene in scene_info:
        os.remove(scene['voiceover_filename'])
        os.remove(scene['video_filename'])

    return final_filename, title_filename, description, tags

def gr_interface(topic):
    video_file, title_filename, description, tags = process_video(topic)
    return video_file, title_filename, description, tags

iface = gr.Interface(
    fn=gr_interface,
    inputs="text",
    outputs=["video", "text", "text", "text"],
    description="Generate a video from topic for free",
    title="Video Processing"
)

iface.launch()
