import gradio as gr
import json
import subprocess
import requests
import random
import cv2
from gtts import gTTS

# Function to generate voiceover using gTTS
def generate_voiceover(text, filename):
    tts = gTTS(text=text, lang='en', slow=False)
    tts.save(filename)

# Function to fetch landscape videos from Pexels 
def get_pexels_video(keyword):
    headers = {"Authorization": "8LpygbUwv484x1RkoAJuKH08yhmBKrYpJ0MlLSLboSS736mfs1dODS3v"}  # Replace with your Pexels API key
    params = {
        "query": keyword, 
        "per_page": 20,
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

# Function to generate video content using Google API
def generate_video_content(topic):
    api_key = "AIzaSyAtVhAjcUi7tHYnYZTWA4_L2ExvsAeupQY"  # Replace with your Google API key
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.0-pro:generateContent?key={api_key}"

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": f"you are a professional youtube creator, create a video on {topic} and the keyword under each scene will be used for pexels search query so give precise keyword for each scene. Give up to 15 related tags. Always create in this json format and give just the json: {{    \"title_filename\": \"\",    \"description\": \"\",    \"video\": [      {{        \"scene\": \"\",        \"keyword\": \"\",        \"voiceover\": \"\"      }}   ],    \"tags\": [\"\", \"\", \"\"]  }}"
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

# Function to process video using OpenCV
def process_video(topic):
    generate_video_content(topic)

    with open('data.json', 'r') as f:
        data = json.load(f)

    scene_videos = []
    for scene in data['video']:
        # Fetch Pexels video
        video_url = get_pexels_video(scene['keyword'])
        if video_url:
            # Download Pexels video
            pexels_video_filename = f"{scene['scene']}_pexels.mp4"
            with requests.get(video_url, stream=True) as r:
                with open(pexels_video_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)
            # Generate voiceover
            voiceover_text = scene['voiceover']
            voiceover_filename = f"{scene['scene']}_voiceover.mp3"
            generate_voiceover(voiceover_text, voiceover_filename)
            # Combine Pexels video with voiceover
            output_filename = f"{scene['scene']}_output.mp4"
            cmd = f"ffmpeg -i {pexels_video_filename} -i {voiceover_filename} -c:v copy -c:a aac -strict experimental -map 0:v:0 -map 1:a:0 {output_filename}"
            subprocess.call(cmd, shell=True)
            scene_videos.append(output_filename)
        else:
            print(f"No video found on Pexels for {scene['keyword']}")

    # Concatenate scene videos
    final_video_filename = 'final_video.mp4'
    cmd = 'ffmpeg'
    for video_file in scene_videos:
        cmd += f" -i {video_file}"
    cmd += f" -filter_complex 'concat=n={len(scene_videos)}:v=1:a=1 [v] [a]' -map '[v]' -map '[a]' {final_video_filename}"
    subprocess.call(cmd, shell=True)

    return final_video_filename

def gr_interface(topic):
    video_file = process_video(topic)
    return video_file

iface = gr.Interface(
    fn=gr_interface,
    inputs="text",
    outputs="video",
    description="Generate a video from topic for free",
    title="Video Processing"
)

iface.launch()
