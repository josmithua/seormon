from math import ceil
import os
import subprocess
from pathlib import Path
import sys
import argparse

from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WHISPER1_MAX_AUDIO_DURATION_SEC = 1500  # 25 minutes
GPT40_MAX_AUDIO_SIZE_BYTES = 26_214_400  # 25 MB

client = OpenAI(api_key=OPENAI_API_KEY)


def transcribe_audio(audio_file: Path) -> str:
    """Transcribe the audio file using OpenAI's Whisper model."""

    with audio_file.open("rb") as file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=file,
        )

    return transcription.text


def get_audio_length(audio_file: Path) -> float:
    """Get the length of the audio file in seconds using ffprobe."""
    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(audio_file),
    ]
    result = subprocess.check_output(command, text=True)
    original_length_sec = float(result.strip())
    return original_length_sec


def change_audio_speed(audio_file: Path, speed: float, out_file: Path):
    """Change the speed of the audio file using ffmpeg."""
    command = [
        "ffmpeg",
        "-i",  # input file
        str(audio_file),
        "-filter:a",  # audio filter
        f"atempo={speed}",  # change audio speed
        "-y",  # overwrite output file
        "-loglevel",
        "error",  # log only errors
        str(out_file),  # output file
    ]
    subprocess.run(command, check=True)


def summarize_text(text: str, additional_instructions: str | None = None) -> str:
    """
    Summarize the text using OpenAI's GPT-4 model.

    Args:
        text: The text to summarize
        additional_instructions: Optional additional instructions for the AI
    """
    # Default instruction if none provided
    instruction = "Start it with a question to the listener."

    # Use provided instructions if available
    if additional_instructions:
        instruction = additional_instructions

    response = client.responses.create(
        model="gpt-4.1",
        input=[
            {
                "role": "user",
                "content": (
                    "The following is a transcript of a sunday sermon. "
                    "Please summarize it in a brief paragraph. "
                    f"{instruction}. "
                    "Also generate an SEO keyphrase that can be used to help people search for this sermon on the internet:\n\n"
                    f"{text}"
                ),
            }
        ],
        store=False,
    )
    return response.output_text


def process_audio_file(audio_file: Path) -> Path:
    """Process the audio file, speeding it up if necessary."""
    if not audio_file.exists():
        raise FileNotFoundError(f"Audio file does not exist: {audio_file}")

    length_sec = get_audio_length(audio_file)
    print(f"Audio length: {length_sec} seconds")

    if length_sec <= WHISPER1_MAX_AUDIO_DURATION_SEC:
        print("Audio is short enough, no need to change speed.")
        return audio_file

    print("Audio is too long for AI transcription service.")
    new_speed = ceil(length_sec / WHISPER1_MAX_AUDIO_DURATION_SEC * 10) / 10
    length_adjusted_audio_file = audio_file.with_suffix(f".x{new_speed}.mp3")

    if length_adjusted_audio_file.exists():
        print(f"Using existing sped up audio file: {length_adjusted_audio_file}")
        return length_adjusted_audio_file

    print(f"Increasing speed by {new_speed}x...")
    change_audio_speed(audio_file, new_speed, length_adjusted_audio_file)
    print(f"Done. New audio file: {length_adjusted_audio_file}")
    return length_adjusted_audio_file


def get_transcript(audio_file: Path) -> str:
    """Get transcript from audio file, using cached version if available."""
    transcription_file = audio_file.with_suffix(".transcript.txt")

    if transcription_file.exists():
        print(f"Using existing transcription: {transcription_file}")
        return transcription_file.read_text(encoding="utf-8")

    print(f"Transcribing audio file: '{audio_file}'...")
    transcript = transcribe_audio(audio_file)

    with transcription_file.open("w", encoding="utf-8") as f:
        f.write(transcript)
    print(f"Transcription saved to: {transcription_file}")

    return transcript


def generate_and_save_summary(
    audio_file: Path, transcript: str, additional_instructions: str | None = None
) -> None:
    """
    Generate and save a summary of the transcript.

    Args:
        audio_file: Path to the audio file
        transcript: The transcript text
        additional_instructions: Optional additional instructions for the AI
    """
    print("Summarizing sermon transcript...")
    summary = summarize_text(transcript, additional_instructions)

    summary_file = audio_file.with_suffix(".summary.txt")
    with summary_file.open("w", encoding="utf-8") as f:
        f.write(summary)

    print(f"Summary saved to: {summary_file}")
    print("Summary:", summary, sep="\n")


def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Process an audio file, transcribe it, and generate a summary."
    )

    parser.add_argument(
        "audio_file", type=str, help="Path to the audio file to process"
    )

    parser.add_argument(
        "--instructions",
        "-i",
        type=str,
        default=None,
        help="Additional instructions for the AI summary (default: 'Start it with a question to the listener.')",
    )

    return parser.parse_args()


def main():
    """CLI entry point."""
    try:
        # Parse command line arguments
        args = parse_arguments()
        audio_file_path = Path(args.audio_file)
        additional_instructions = args.instructions

        # Process the audio file (handle length issues)
        processed_audio = process_audio_file(audio_file_path)

        # Get the transcript (from cache or by transcribing)
        transcript = get_transcript(processed_audio)

        # Generate and save summary
        generate_and_save_summary(processed_audio, transcript, additional_instructions)

        return 0

    except FileNotFoundError as e:
        print(f"Error: {e}")
        return 1
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
