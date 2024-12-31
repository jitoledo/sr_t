#!/usr/bin/env python3
from pathlib import Path
from datetime import timedelta
import argparse
from transcriber import Transcriber
from translator import Translator
from srt import compose, parse, Subtitle
from typing import List,Union



def write_srt(subtitle_path: Union[Path,str], subtitles:List[Subtitle]) -> None :
    with open(subtitle_path,"w") as f:
        f.write(compose(subtitles))

def read_srt(subtitle_path: Union[Path,str]) -> List[Subtitle]:
    with open(subtitle_path,"r") as f:
        contents="".join(f.readlines())
    subtitles=list(parse(contents))
    return subtitles
def enforce_min_duration(subtitles: List[Subtitle], min_duration: timedelta) -> List[Subtitle]:
    for subtitle in subtitles:
        if subtitle.end - subtitle.start < min_duration:
            subtitle.end = subtitle.start + min_duration
    return subtitles

def main():
    parser = argparse.ArgumentParser(description="Subtitle generation and translation tool.")

    parser.add_argument(
        "--mode", 
        choices=["transcribe", "transcribe-translate", "translate"], 
        required=True, 
        help="Operation mode: 'transcribe' for transcription, 'transcribe-translate' for transcription and translation, or 'translate' to translate an existing SRT file."
    )
    parser.add_argument("files", nargs="+", help="List of input video or SRT files to process.")
    parser.add_argument("--target-lang", help="Target language code (e.g., 'en', 'es', 'spa_Latn'). Required for translation and transcribe-translate modes.")
    parser.add_argument("--source-lang", help="Source language code for audio transcription or translation. For 'translate', it's the subtitle language. Optional for 'transcribe'.")
    parser.add_argument("--whisper-model", default="large-v3", help="Whisper model size (default: 'large-v3').")
    parser.add_argument(
        "--translation-model", 
        choices=["helsinki", "nllb"], 
        default="helsinki", 
        help="Translation model type: 'helsinki' (default) or 'nllb'. Target language code should match the selected model format."
    )
    parser.add_argument(
        "--min-subtitle-duration_s", 
        type=float, 
        default=2.0, 
        help="Minimum duration (in seconds) for each subtitle entry. Defaults to 2 seconds."
    )

    args = parser.parse_args()

    files = [Path(file) for file in args.files]
    target_lang = args.target_lang
    source_lang = args.source_lang
    whisper_model = args.whisper_model
    translation_model = args.translation_model
    min_subtitle_duration_s = timedelta(seconds=args.min_subtitle_duration_s)

    if args.mode == "transcribe":
        # Transcribe video to subtitles
        print("Initializing...", end=" ")
        transcriber = Transcriber(source_language=source_lang, whisper_model_size=whisper_model)
        print("✔")
        for input_path in files:
            print(f"Transcribing {input_path}...", end=" ")
            subtitles = transcriber.transcribe(str(input_path))
            print("✔")
            subtitles = enforce_min_duration(subtitles, min_subtitle_duration_s)
            output_path = input_path.with_suffix(".srt")
            write_srt(output_path, subtitles)
            print(f"Transcription completed: {output_path}")

    elif args.mode == "transcribe-translate":
        # Transcribe video and translate subtitles
        if not target_lang:
            raise ValueError("--target-lang is required for transcribe-translate mode.")
        
        print("Initializing...", end=" ")
        translator_source_lang = "en" if translation_model == "helsinki" else "eng_Latn"
        if source_lang and source_lang == translator_source_lang:
            transcriber = Transcriber(whisper_model_size=whisper_model, task="transcribe")
        else:
            transcriber = Transcriber(whisper_model_size=whisper_model, task="translate")
        translator = Translator(source_language=translator_source_lang, target_language=target_lang, translation_model=translation_model)
        print("✔")
        for input_path in files:
            print(f"Transcribing {input_path}...", end=" ")
            subtitles = transcriber.transcribe(str(input_path))
            subtitles = enforce_min_duration(subtitles, min_subtitle_duration_s)
            print("✔")
            print(f"Translating {input_path}...", end=" ")
            translated_subtitles = translator.translate(subtitles)
            print("✔")
            output_path = input_path.with_name(f"{input_path.stem}.{target_lang}.srt")
            write_srt(output_path, translated_subtitles)
            print(f"Transcription and translation completed: {output_path}")

    elif args.mode == "translate":
        # Translate existing SRT file
        if not source_lang:
            raise ValueError("--source-lang is required for translate mode.")
        if not target_lang:
            raise ValueError("--target-lang is required for translate mode.")

        print("Initializing...", end=" ")
        translator = Translator(source_language=source_lang, target_language=target_lang, translation_model=translation_model)
        print("✔")
        for input_path in files:
            print(f"Translating {input_path}...", end=" ")
            subtitles = read_srt(input_path)
            translated_subtitles = translator.translate(subtitles)
            print("✔")
            output_path = input_path.with_name(f"{input_path.stem}.{target_lang}.srt")
            write_srt(output_path, translated_subtitles)
            print(f"Translation completed: {output_path}")

if __name__ == "__main__":
    main()

