# SEOrmon

SEOrmon (Sermon + SEO) is a command-line tool that processes sermon audio files, transcribes them using OpenAI's Whisper API, and generates AI-powered summaries with SEO keyphrases using GPT-4.

## Features

- Process audio files (MP3 format)
- Automatically handle long audio files by speeding them up to fit within Whisper API limits
- Generate transcripts of sermon audio (with caching to avoid re-transcription)
- Create AI-powered summaries with customizable instructions
- Generate SEO keyphrases for better discoverability

## Requirements

- Python 3.12 or higher
- FFmpeg (for audio processing)
- FFprobe (for audio length detection)
- OpenAI API key

## Installation

1. Clone this repository
2. Install the dependencies:

With uv:

```bash
uv sync
```

3. Set your OpenAI API key as an environment variable:

```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

Process a local audio file:

```bash
uv run python main.py path/to/sermon.mp3
```

Add custom instructions for the summary:

```bash
uv run python main.py path/to/sermon.mp3 --instructions "Include three main points from the sermon"
```

Or use the short flag:

```bash
uv run python main.py path/to/sermon.mp3 -i "Focus on practical applications"
```

## How it Works

1. **Audio Processing**: The tool first checks if the audio file exists and determines its length. If the audio is too long for the Whisper API (over 25 minutes), it speeds up the audio to fit within the limits.

2. **Transcription**: The audio is transcribed using OpenAI's Whisper model. Transcriptions are cached to disk, so subsequent runs with the same audio file won't need to re-transcribe.

3. **Summary Generation**: The transcript is summarized using OpenAI's GPT-4 model. The summary includes an SEO keyphrase and follows any custom instructions provided.

4. **Output**: The summary is saved to a text file alongside the original audio file and printed to the console.

## Files Created

For an input file `sermon.m4a`, the tool will create:

- `sermon.transcript.txt` - The full transcript
- `sermon.summary.txt` - The AI-generated summary with SEO keyphrase

If the audio needs to be sped up, it will also create:

- `sermon.x{speed}.mp3` - The sped-up version of the audio

## Dependencies

- openai - For API access to Whisper and GPT-4
- ffmpeg/ffprobe - For audio manipulation and analysis

## License

[Add your license information here]
