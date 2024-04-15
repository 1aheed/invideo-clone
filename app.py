import gradio as gr
import json
import requests
import random
import cv2
import numpy as np
from gtts import gTTS

# Function to generate voiceover using gTTS
def generate_voiceover(text, filename):
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

# Function to generate video content using Google API
def generate_video_content(topic):
    api_key = "AIzaSyAtVhAjcUi7tHYnYZTWA4_L2ExvsAeupQY"
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
    # Generate video content
    generate_video_content(topic)

    # Load JSON data
    with open('data.json', 'r') as f:
        data = json.load(f)

    scene_info = []
    for scene in data['video']:
        voiceover_text = scene['voiceover']
        voiceover_filename = f"{scene['scene']}_voiceover.mp3"
        generate_voiceover(voiceover_text, voiceover_filename)
        scene_info.append({'voiceover_filename': voiceover_filename, 'keyword': scene['keyword']})

    # Fetch videos from Pexels
    for scene in scene_info:
        video_url = get_pexels_video(scene['keyword'])
        if video_url:
            scene['video_url'] = video_url
        else:
            return "Error: Failed to fetch video from Pexels"

    # Create Scene Videos
    scene_videos = []
    for scene in scene_info:
        cap = cv2.VideoCapture(scene['video_url'])
        if not cap.isOpened():
            return "Error: Failed to open video file"

        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Set duration of the video to match voiceover duration
        duration = frame_count / fps

        # Create VideoWriter object
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        output_filename = f"{scene['keyword']}_scene.mp4"
        out = cv2.VideoWriter(output_filename, fourcc, fps, (1920, 1080))

        # Read frames and write to output video
        for i in range(int(fps * duration)):
            ret, frame = cap.read()
            if not ret:
                break
            out.write(frame)

        # Release VideoCapture and VideoWriter objects
        cap.release()
        out.release()

        scene_videos.append(output_filename)

    # Concatenate scene videos
    final_video = cv2.VideoCapture(scene_videos[0])
    for video_file in scene_videos[1:]:
        video = cv2.VideoCapture(video_file)
        while True:
            ret, frame = video.read()
            if not ret:
                break
            final_video.write(frame)
        video.release()

    final_video.release()

    # Extract title_filename, description, and tags from JSON
    title_filename = data.get('title_filename', '')
    description = data.get('description', '')
    tags = ', '.join(data.get('tags', []))

    # Return video file, title filename, description, and tags
    return scene_videos[0], title_filename, description, tags

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
