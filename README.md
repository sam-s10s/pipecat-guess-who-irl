# Speechmatics + Pipecat Guess Who? "In Real Life"

A voice-powered AI agent that plays the classic game of _Guess Who?_ using [Speechmatics](https://www.speechmatics.com/) for real-time speech recognition, [Pipecat](https://github.com/pipecat-ai/pipecat) for conversational AI pipeline orchestration, and OpenAI for intelligent gameplay.

Perfect companion when you want to play _Guess Who?_ and nobody to play with!

## About This Demo

This demo showcases how to build a conversational AI game using:

- **Speechmatics STT** for accurate real-time speech-to-text with speaker diarization
- **Pipecat framework** for managing the conversational AI pipeline
- **OpenAI ChatGPT** for intelligent game logic and responses
- **ElevenLabs TTS** for natural voice synthesis

The agent can understand speech, maintain game state, ask strategic questions, and make educated guesses about your chosen character.

### Naughty LLMs!

LLMs are pretty good at playing games, but they can find it hard to understand rules. You might think that Guess Who? is simple - it is for us humans - but LLMs have trouble in not asking out of turn.

For example, when the agent asks you "Are you female?" and you then answer "No" and prepare your own question to the agent, it will most likely dive straight into a further question. That's not playing by the rules! No amount of prompting or model switching managed to prevent this from creeping into the gameplay, especially after a few turns.

To overcome this, I created a function call to validate my reply. This will either return nothing (which prevents the LLM from asking a follow up question), or if it thinks it knows the answer, then it will have a go.

```python
FunctionSchema(
    name="process_opponent_answer",
    description="use this tool to process an answer from the opponent.",
    properties={
        "guess": {
            "type": "string",
            "enum": ["true", "false"],
            "description": "if you think you can guess the character, say true, otherwise say false.",
        },
    },
    required=["guess"],
)
```

### Character Names

Another challenge is that some of the characters in the game could be standard English words. To combat this, I take advantage of a feature of the Speechmatics STT and pass through the list of characters as vocabulary for it to be aware of. This fixed it!

```python
# Load the character names from a JSON file
CHARACTER_NAMES = json.loads(load_file("characters.json", __file__))

# Pass the names through as additional vocab
stt = SpeechmaticsSTTService(
    ...,
    additional_vocab=[AdditionalVocabEntry(content=name) for name in CHARACTER_NAMES],
)
```

## Prerequisites

You'll need API keys for the following services:

- **Speechmatics API key** - Get yours at [portal.speechmatics.com](https://portal.speechmatics.com)
- **ElevenLabs API key** - For voice synthesis at [elevenlabs.io](https://elevenlabs.io)
- **OpenAI API key** - For ChatGPT models at [platform.openai.com](https://platform.openai.com)

You will also need a board game:

- **Guess Who?** - [Amazon UK](https://www.amazon.co.uk/dp/B0BZ8PRZ6T)

## Quick Start

```shell
# Clone and navigate to the project
git clone <repository-url>
cd pipecat-guess-who-irl

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure API keys
cp dot-env.template .env
# Edit .env with your API keys

# Run the demo
python agent.py
```

## Configuration

Edit the `.env` file with your API credentials:

```env
SPEECHMATICS_API_KEY=your-speechmatics-api-key-here
ELEVENLABS_API_KEY=your-elevenlabs-api-key-here
OPENAI_API_KEY=your-openai-api-key-here
```

If you have a different board game to me, you will need to edit `characters.json` and `characters.md` to match your version of the game.

## How to Play

1. Start the application with `python agent.py`
2. Go to `http://localhost:7860/` in your browser
3. Think of a character from the board Guess Who? game
4. The AI will ask yes/no questions about your character
5. Answer with "yes" or "no"
6. The AI will try to guess your character!

## Run using Daily

If you are unable to use WebRTC directly (depending on your system's security), you can use the Daily platform instead. You will need to have a [Daily account](https://daily.co) and create a room that the agent can join.

Add the following to your `.env` file:

```env
DAILY_API_KEY=your-daily-api-key-here
DAILY_SAMPLE_ROOM_URL=your-daily-room-url-here
```

Now run the agent with the `--transport daily` flag:

```shell
# Run using Daily
python agent.py --transport daily
```

## Technical Details

- Uses Speechmatics' WebSocket API for real-time transcription
- Leverages speaker diarization to distinguish between user and agent speech
- Built on the Pipecat framework for robust conversational AI pipelines
- Supports both Daily.co and WebRTC transport layers

## Resources

- [Speechmatics API Documentation](https://docs.speechmatics.com/api-ref/realtime-transcription-websocket)
- [Pipecat Framework](https://github.com/pipecat-ai/pipecat)
- [Speechmatics STT Plugin](https://github.com/pipecat-ai/pipecat/blob/main/src/pipecat/services/speechmatics/stt.py)

## Copyright

The game _Guess Who?_ is a trademark and copyright of Hasbro, Inc. This conversational AI agent is an unofficial, fan-made implementation created purely for entertainment and educational purposes. No copyright infringement is intended. This project is not affiliated with, endorsed by, or connected to Hasbro, Inc. in any way.

This AI implementation is provided as-is for fun and learning purposes only. ❤️
