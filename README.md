# Text to Long Video - Invideo AI Clone

This project aims to generate long landscape videos based on a given topic or word. It utilizes various APIs and libraries to create compelling video content suitable for platforms like YouTube or documentaries.

## Description

The project consists of a Python script that takes a text input (topic or word) and generates a video based on that input. The generated video includes scenes with relevant content fetched from Pexels, accompanied by voiceovers synthesized using Google Text-to-Speech (gTTS).

## Huggingface demo
[View here](https://huggingface.co/spaces/aheedsajid/invideo-clone)

## Web demo
[View here](https://ziverr.xyz)


## Requirements

- Python 3.x
- Gradio
- gTTS
- moviepy
- requests

You can install the required Python packages using pip:

```plaintext
pip install gradio gtts moviepy requests
```

## API Key Setup

To use this project, you need to obtain API keys for the following services:

- Google Gemini API: Obtain your API key from [Gemini](https://aistudio.google.com/app/apikey)
- Pexels API: Obtain your API key from [Pexels](https://www.pexels.com/api/)

Once you have obtained the API keys, replace the placeholders in the script with your actual API keys.

## Usage

1. Clone the repository:

```
git clone https://github.com/1aheed/invideo-clone.git
```

2. Navigate to the project directory:

```
cd invideo-clone
```

3. Run the script:

```
python app.py
```
## Gradio Interface
After running the app.py command you will get a URL to the gradio interface.

On the gradio interface input your desired topic or word when prompted.

The script will generate a video based on the input and save it as with the title you give. It will also auto-generate video descriptions and tags.

## Custom Projects

If you want bulk video/image generators or any other software or web app, feel free to contact me.

## Show some love

If you find this project helpful, consider supporting by [donating here](https://nowpayments.io/donation/aheed).

## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements, feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Gemini
- Gradio
- Pexels
- gTTS
