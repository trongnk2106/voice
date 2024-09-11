import requests
import json
import base64

VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Rachel
YOUR_XI_API_KEY = "sk_7e8d60ce5cc1d77dab5e4376b71a3e592a385637d8e8dfde"

url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}/stream/with-timestamps"

headers = {
  "Content-Type": "application/json",
  "xi-api-key": YOUR_XI_API_KEY
}

data = {
  "text": (
    "Born and raised in the charming south, " 
    "I can add a touch of sweet southern hospitality " 
    "to your audiobooks and podcasts"
  ),
  "model_id": "eleven_multilingual_v2",
  "voice_settings": {
    "stability": 0.5,
    "similarity_boost": 0.75
  }
}


response = requests.post(
    url,
    json=data,
    headers=headers,
    stream=True
)

if response.status_code != 200:
  print(f"Error encountered, status: {response.status_code}, "
          f"content: {response.text}")
  quit()

audio_bytes = b""
characters = []
character_start_times_seconds = []
character_end_times_seconds = []
 
for line in response.iter_lines():
    if line:  # filter out keep-alive new line
        # convert the response which contains bytes into a JSON string from utf-8 encoding
        json_string = line.decode("utf-8")

        # parse the JSON string and load the data as a dictionary
        response_dict = json.loads(json_string)

        # the "audio_base64" entry in the dictionary contains the audio as a base64 encoded string, 
        # we need to decode it into bytes in order to save the audio as a file
        audio_bytes_chunk = base64.b64decode(response_dict["audio_base64"])
        audio_bytes += audio_bytes_chunk
        
        if response_dict["alignment"] is not None:
            characters.extend(response_dict["alignment"]["characters"])
            character_start_times_seconds.extend(response_dict["alignment"]["character_start_times_seconds"])
            character_end_times_seconds.extend(response_dict["alignment"]["character_end_times_seconds"])

with open('output.mp3', 'wb') as f:
  f.write(audio_bytes)

print({
    "characters": characters,
    "character_start_times_seconds": character_start_times_seconds,
    "character_end_times_seconds": character_end_times_seconds
})

