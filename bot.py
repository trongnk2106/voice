import os, aiohttp, asyncio, signal, logging
from vocode.streaming.streaming_conversation import StreamingConversation
from vocode.helpers import create_streaming_microphone_input_and_speaker_output
from vocode.streaming.transcriber import *
from vocode.streaming.models.transcriber import*
from vocode.streaming.transcriber.deepgram_transcriber import DeepgramTranscriber
from vocode.streaming.agent import *
from vocode.streaming.agent.chat_gpt_agent import ChatGPTAgent
from vocode.streaming.synthesizer import*
from vocode.streaming.models.synthesizer import ElevenLabsSynthesizerConfig
from vocode.streaming.models.agent import *
from vocode.streaming.synthesizer.eleven_labs_synthesizer import ElevenLabsSynthesizer
from vocode.streaming.models.message import BaseMessage

os.environ['DEEPGRAM_API_KEY'] = "be20bb9495d5a71c8943f6ea3a7377319de7fff9"
os.environ['OPENAI_API_KEY'] = "sk-AIzaSyCb9J5fggG9u4qcucgqSHgr-j6jYeg-p9o"
os.environ['ELEVENLABS_API_KEY'] = "sk_26e8c20e45eec86fd1567a6df04c5384de245a30d2a460f4"

logging.basicConfig()
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

async def main():
    assert os.getenv('DEEPGRAM_API_KEY'), "Missing DEEPGRAM_API_KEY"
    assert os.getenv('OPENAI_API_KEY'), "Missing OPENAI_API_KEY"
    assert os.getenv('ELEVENLABS_API_KEY'), "Missing ELEVENLABS_API_KEY"

    async with aiohttp.ClientSession() as session:
        microphone_input, speaker_output = create_streaming_microphone_input_and_speaker_output(
            use_default_devices=True,
            # # logger=logger,
            # output_file='output_audio.wav'
        )
        print("Microphone and speaker initialized")

        elevenlabs_config = ElevenLabsSynthesizerConfig.from_output_device(
            output_device=speaker_output,
            api_key=os.getenv('ELEVENLABS_API_KEY')
        )

        conversation = StreamingConversation(
            output_device=speaker_output,
            transcriber=DeepgramTranscriber(
                DeepgramTranscriberConfig.from_input_device(
                    microphone_input, endpointing_config=PunctuationEndpointingConfig()
                )),
            agent=ChatGPTAgent(
                ChatGPTAgentConfig(
                    initial_message=BaseMessage(text="Ahoy! I be Alex, yer trusty pirate companion!"),
                    prompt_preamble="Speak like a pirate and engage in a hearty conversation about the pirate life with Alex the chatbot.",
                )),
            synthesizer=ElevenLabsSynthesizer(elevenlabs_config),
            # # logger=logger,
        )

        async def shutdown(signal, loop):
            await conversation.terminate()
            loop.stop()

        loop = asyncio.get_running_loop()

        def signal_handler(sig):
            loop.call_soon_threadsafe(asyncio.create_task, shutdown(sig, loop))

        for s in (signal.SIGINT, signal.SIGTERM):
            signal.signal(s, signal_handler)

        await conversation.start()
        print("Conversation started, press Ctrl+C to end")

        while conversation.is_active():
            chunk = await microphone_input.get_audio()
            result = conversation.receive_audio(chunk)
            if asyncio.iscoroutine(result):
                await result
            elif result is not None:
                print(f"Unexpected result from receive_audio: {result}")

if __name__ == "__main__":
    loop = asyncio.ProactorEventLoop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())