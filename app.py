import gradio as gr
import json
import requests
import random
import subprocess
import os

from gtts import gTTS

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

    # Step 4: Create Scene Videos
    scene_videos = []
    for scene in scene_info:
        video_clips = []
        for video_filename in scene['video_filenames']:
            video_clip = f"file '{video_filename}'"
            video_clips.append(video_clip)
        video_concat = "|".join(video_clips)
        # Use FFmpeg to concatenate the videos
        subprocess.run(['ffmpeg', '-i', f'concat:{video_concat}', '-vf', 'scale=1920:1080', '-c:a', 'aac', '-b:a', '256k', f"{scene['scene']}_concatenated.mp4"], capture_output=True)
        # Trim the concatenated clip to match the voiceover duration
        subprocess.run(['ffmpeg', '-i', f"{scene['scene']}_concatenated.mp4", '-t', str(scene['voiceover_duration']), '-c', 'copy', f"{scene['scene']}_trimmed.mp4"], capture_output=True)
        # Add audio to trimmed video clip
        subprocess.run(['ffmpeg', '-i', f"{scene['scene']}_trimmed.mp4", '-i', scene['voiceover_filename'], '-c:v', 'copy', '-c:a', 'aac', '-strict', 'experimental', '-map', '0:v:0', '-map', '1:a:0', '-shortest', f"{scene['scene']}_final.mp4"], capture_output=True)
        scene_videos.append(f"{scene['scene']}_final.mp4")

    final_filename = title_filename + '.mp4'
    # Concatenate all scene videos into one final video
    with open('video_list.txt', 'w') as f:
        for video_filename in scene_videos:
            f.write(f"file '{video_filename}'\n")
    subprocess.run(['ffmpeg', '-f', 'concat', '-safe', '0', '-i', 'video_list.txt', '-c', 'copy', final_filename], capture_output=True)
    os.remove('video_list.txt')

    # Clean up downloaded files
    for scene in scene_info:
        os.remove(scene['voiceover_filename'])
        for video_filename in scene['video_filenames']:
            os.remove(video_filename)
        os.remove(f"{scene['scene']}_concatenated.mp4")
        os.remove(f"{scene['scene']}_trimmed.mp4")
        os.remove(f"{scene['scene']}_final.mp4")

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
