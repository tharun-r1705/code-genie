from io import BytesIO
from typing import Optional, Dict

import chainlit as cl
import os
import google.generativeai as genai
from chainlit.element import ElementBased
from dotenv import load_dotenv
from groq import Groq
from pyht import Client
from pyht.client import TTSOptions

load_dotenv()

client = Groq(api_key="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")

@cl.oauth_callback
def oauth_callback(
  provider_id: str,
  token: str,
  raw_user_data: Dict[str, str],
  default_user: cl.User,
) -> Optional[cl.User]:
  return default_user

async def speech_to_text(audio_file):
    response = client.audio.translations.create(
        file=audio_file,  # Required audio file
        model="whisper-large-v3",  # Required model to use for translation
        prompt="Specify context or spelling",  # Optional
        response_format="json",  # Optional
        temperature=0.0  # Adjust this based on Groq's API
    )
    return response.text

def text_to_speech(text):
    client = Client(
        user_id="4PITN4xNgkQvptZ1JKpoMqPAozB2",
        api_key="15667a819f71438f88c2027d6b4ebb8f",
    )

    # Text-to-Speech options
    options = TTSOptions(voice="s3://voice-cloning-zero-shot/775ae416-49bb-4fb6-bd45-740f205d20a1/jennifersaad/manifest.json")

    # Open a file to store the output audio
    with open("output_audio.mp3", "wb") as audio_file:
        # Iterate over the audio chunks from the TTS client
        for chunk in client.tts(text, options):
            # Write each chunk to the file
            audio_file.write(chunk)

@cl.on_audio_chunk
async def on_audio_chunk(chunk: cl.AudioChunk):
    if chunk.isStart:
        buffer = BytesIO()
        buffer.name = f"input_audio.{chunk.mimeType.split('/')[1]}"
        cl.user_session.set("audio_buffer", buffer)
        cl.user_session.set("audio_mime_type", chunk.mimeType)

    cl.user_session.get("audio_buffer").write(chunk.data)

@cl.on_audio_end
async def on_audio_end(elements: list[ElementBased]):
    audio_buffer: BytesIO = cl.user_session.get("audio_buffer")
    # audio_buffer = cl.user_session.get("audio_buffer")
    audio_buffer.seek(0)
    transcription = await speech_to_text(audio_buffer)
    await cl.Message(content=transcription).send()

    genai.configure(api_key=os.environ['GOOGLE_API_KEY'])
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(transcription)
    #await cl.Message(content=response.text).send()
    text_to_speech(response.text)
    elements = [
        cl.Audio(path="output_audio.mp3", display="inline",auto_play = True),
    ]
    await cl.Message(
        content="Question",
        elements=elements,
    ).send()

@cl.on_message
async def handle_message(message):
    if message.content.startswith("oauth:"):
        user_name = message.content.split(":")[1]
        try:
            cl.user_session.set('user_name', user_name)
        except cl.ChainlitContextException:
            print("Chainlit context is not available.")
    if message.content == "":
        pass
    else:
        await cl.Message(content = "Please give input through voice").send()

@cl.on_chat_start
async def greet_user():
    user_name = cl.user_session.get('user_name', 'there')
    greeting = f"Hello {user_name}, I'm your virtual assistant! How can I assist you today?"
    await cl.Message(content=greeting).send()


