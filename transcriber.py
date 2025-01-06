from io import BytesIO
import ffmpeg
from faster_whisper import WhisperModel
from srt import Subtitle,timedelta_to_srt_timestamp
from datetime import timedelta
from typing import List, Optional
from tqdm import tqdm
from math import floor,ceil

class Transcriber:
    """
    A class for audio transcription using Faster-Whisper for subtitle generation
    """

    def __init__(
        self,
        source_language: Optional[str] = None,
        task: str = "transcribe",
        whisper_model_size: str = 'large-v3',
    ):
        """
        Initializes the Subtitler class.

        Args:
            source_language (Optional[str]): Language of the source video. Will autodetect if not specified.
                                             Defaults to None.
            task (Optional[str]): "transcribe" to transcribe in original language.
                                  "translate" to translate to english. Defaults to "transcribe"
            whisper_model_size (Optional[str]): Model size for transcription: large-v3,medium,....
                                                Defaults to "large-v3"
        """
        self.source_language = source_language
        self.task = task
        device = "cuda"
        compute_type = "int8_float16"

        # Initialize Whisper model
        self.transcriber = WhisperModel(whisper_model_size, device=device, compute_type=compute_type)

    def transcribe(self, video_path: str) -> List[Subtitle]:
        """
        Transcribes audio from the given video file into Segments.

        Args:
            video_path (str): Path to the input video file.

        Returns:
            List[Subtitle]: Start time, end time, and text.
        """

        # Extract audio data using ffmpeg
        process = (
            ffmpeg
            .input(video_path)
            .output("pipe:1", format="wav", acodec="pcm_s16le", loglevel="quiet")
            .run(capture_stdout=True, capture_stderr=True)
        )
        audio_data = BytesIO(process[0])

        # Transcribe audio
        segments, info = self.transcriber.transcribe(
            audio_data,
            beam_size=5,
            language=self.source_language,
            task=self.task,
            condition_on_previous_text=True,
            log_prob_threshold=-0.5,
            no_speech_threshold = 0.7,
        )
        subtitle_list = []
        segment_index = 0
        with tqdm(total=floor(info.duration), unit=" seconds", leave = False,desc="Transcribing...") as pbar:
            for segment in segments:
                pbar.update(ceil(segment.end-segment.start))
                current_sub=Subtitle(index=segment_index,
                                    start=timedelta(seconds=segment.start),
                                    end=timedelta(seconds=segment.end),
                                    content=segment.text,
                                    )
                # If the model produces segments with repeated text,
                # set the end_time of the previous segment instead of appending a new sub
                if segment_index > 1 and current_sub.content == subtitle_list[-1].content: 
                    subtitle_list[-1].end=current_sub.end
                else:
                    segment_index += 1
                    subtitle_list.append(current_sub)
        return subtitle_list
