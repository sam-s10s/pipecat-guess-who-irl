#
# Copyright (c) 2024–2025, Daily
#
# SPDX-License-Identifier: BSD 2-Clause License
#

import argparse
import json
import os
import random
import re

from dotenv import load_dotenv
from loguru import logger
from pipecat.adapters.schemas.function_schema import FunctionSchema
from pipecat.adapters.schemas.tools_schema import ToolsSchema
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.llm_response import (
    LLMUserAggregatorParams,
)
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.services.elevenlabs.tts import ElevenLabsTTSService
from pipecat.services.llm_service import FunctionCallParams
from pipecat.services.openai.base_llm import BaseOpenAILLMService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.services.speechmatics.stt import (
    SpeechmaticsSTTService,
)
from pipecat.transcriptions.language import Language
from pipecat.transports.base_transport import BaseTransport, TransportParams
from pipecat.transports.services.daily import DailyParams

load_dotenv()

AGENT_CONTEXT = open("agent.md", "r").read()
CHARACTERS = re.sub(r" {2,}", " ", open("characters.md", "r").read())
CHARACTER_NAMES = json.loads(open("characters.json", "r").read())


async def select_character(params: FunctionCallParams):
    selected_character = random.choice(CHARACTER_NAMES)
    logger.info(f"Selected character: {selected_character}")
    await params.result_callback({"your_character": selected_character})


async def process_opponent_answer(params: FunctionCallParams):
    if params.arguments["guess"] == "true":
        logger.debug("the agent wants to guess!")
        await params.result_callback(
            {"response": "Please respond immediately with your guess."}
        )
    else:
        await params.result_callback(None)


transport_params = {
    "daily": lambda: DailyParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        vad_analyzer=SileroVADAnalyzer(),
    ),
    "webrtc": lambda: TransportParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        vad_analyzer=SileroVADAnalyzer(),
    ),
}


async def run_example(
    transport: BaseTransport, _: argparse.Namespace, handle_sigint: bool
):
    """Run example using Speechmatics STT."""
    logger.info("Starting bot")

    stt = SpeechmaticsSTTService(
        api_key=os.getenv("SPEECHMATICS_API_KEY"),
        base_url="wss://preview.rt.speechmatics.com/v2",
        params=SpeechmaticsSTTService.InputParams(
            language=Language.EN,
            end_of_utterance_silence_trigger=0.5,
            enable_diarization=True,
            additional_vocab=[{"content": name} for name in CHARACTER_NAMES],
        ),
    )

    llm = OpenAILLMService(
        api_key=os.getenv("OPENAI_API_KEY"),
        params=BaseOpenAILLMService.InputParams(temperature=0.75),
    )

    tts = ElevenLabsTTSService(
        api_key=os.getenv("ELEVENLABS_API_KEY"),
        voice_id="97U3B7htAA7UsCIDST8b",
        model="eleven_turbo_v2_5",
    )

    llm.register_function("select_character", select_character)
    llm.register_function("process_opponent_answer", process_opponent_answer)

    select_character_function = FunctionSchema(
        name="select_character",
        description="use this tool to select a random character for you to play as.",
        properties={},
        required=[],
    )

    process_opponent_answer_function = FunctionSchema(
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

    tools = ToolsSchema(
        standard_tools=[select_character_function, process_opponent_answer_function]
    )

    messages = [
        {"role": "system", "content": AGENT_CONTEXT.format(characters=CHARACTERS)},
    ]

    context = OpenAILLMContext(messages, tools=tools)
    context_aggregator = llm.create_context_aggregator(
        context,
        user_params=LLMUserAggregatorParams(aggregation_timeout=0.005),
    )

    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            context_aggregator.user(),
            llm,
            tts,
            transport.output(),
            context_aggregator.assistant(),
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
        ),
    )

    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Client connected")
        messages.append(
            {"role": "system", "content": "Introduce yourself and ask for their name."}
        )
        await task.queue_frames([context_aggregator.user().get_context_frame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        await task.cancel()

    runner = PipelineRunner(handle_sigint=handle_sigint)

    await runner.run(task)


if __name__ == "__main__":
    from pipecat.examples.run import main

    main(run_example, transport_params=transport_params)
