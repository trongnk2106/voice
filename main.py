import asyncio
import signal

from pydantic_settings import BaseSettings, SettingsConfigDict

from vocode.helpers import create_streaming_microphone_input_and_speaker_output
from vocode.logging import configure_pretty_logging
from vocode.streaming.agent.chat_gpt_agent import ChatGPTAgent
from vocode.streaming.models.agent import ChatGPTAgentConfig
from vocode.streaming.models.message import BaseMessage
from vocode.streaming.models.synthesizer import GoogleSynthesizerConfig, CoquiTTSSynthesizerConfig, GTTSSynthesizerConfig
from vocode.streaming.models.transcriber import (
    DeepgramTranscriberConfig,
    PunctuationEndpointingConfig,
)
from vocode.streaming.streaming_conversation import StreamingConversation
# from vocode.streaming.synthesizer.azure_synthesizer import AzureSynthesizer
from vocode.streaming.transcriber.deepgram_transcriber import DeepgramTranscriber
from vocode.streaming.synthesizer.eleven_labs_synthesizer import ElevenLabsSynthesizer
from vocode.streaming.models.synthesizer import ElevenLabsSynthesizerConfig

from loguru import logger
import os 
from dotenv import load_dotenv

_ = load_dotenv()


configure_pretty_logging()

class Settings(BaseSettings):
    """
    Settings for the streaming conversation quickstart.
    These parameters can be configured with environment variables.
    """

    openai_api_key: str = os.environ.get("OPENAI_API_KEY")
    # azure_speech_key: str = "ENTER_YOUR_AZURE_KEY_HERE"
    deepgram_api_key: str = os.environ.get("DEEPGRAM_API_KEY")
    elevenlabs_api_key: str = os.environ.get("ELEVENLABS_API_KEY")
    # azure_speech_region: str = "eastus"
    
    logger.info(f"openai_api_key: {openai_api_key}")
    logger.info(f"deepgram_api_key: {deepgram_api_key}")
    logger.info(f"elevenlabs_api_key: {elevenlabs_api_key}")

    # This means a .env file can be used to overload these settings
    # ex: "OPENAI_API_KEY=my_key" will set openai_api_key over the default above
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()

@logger.catch
async def main():
    (microphone_input,speaker_output,) = create_streaming_microphone_input_and_speaker_output(
        use_default_devices=False,
    #    use_blocking_speaker_output=True,  # this moves the playback to a separate thread, set to False to use the main thread
    )
    # elevenlabs_config = 
    conversation = StreamingConversation(
        output_device=speaker_output,
        transcriber=DeepgramTranscriber(
            DeepgramTranscriberConfig.from_input_device(
                microphone_input,
                endpointing_config=PunctuationEndpointingConfig(),
                api_key=settings.deepgram_api_key,
                language="vi",
                model='nova-2'
            ),
        ),
        agent=ChatGPTAgent(
            ChatGPTAgentConfig(
                model_name="gpt-4o-mini",
                openai_api_key=settings.openai_api_key,
                prompt_preamble="""You are an excellent translator, please translate the input language is VietNames language into English language, Only answer the translation part and do not include any other information.""",
            )
        ),
        # vo class ElevenLabsSynthesizer, comment tu dong 45 -> 61, sau do them : self.output_format = "pcm_24000"
        synthesizer=ElevenLabsSynthesizer(
            ElevenLabsSynthesizerConfig.from_output_device(output_device = speaker_output,
                                                            api_key=settings.elevenlabs_api_key,
                                                            voice_id="pMsXgVXv3BLzUgSXRplE"),
      
        )
        # logger=logger
    )
    await conversation.start()
    print("Conversation started, press Ctrl+C to end")
    signal.signal(signal.SIGINT, lambda _0, _1: asyncio.create_task(conversation.terminate()))
    while conversation.is_active():
        chunk = await microphone_input.get_audio()
        conversation.receive_audio(chunk)


if __name__ == "__main__":
    # print(os.environ.get("OPENAI_API_KEY"))
    asyncio.run(main())
