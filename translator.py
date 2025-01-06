from srt import Subtitle
from transformers import pipeline
from typing import List
from tqdm import tqdm

class Translator:
    """
    A class for subtitle translation using nllb or helsinki-opus-mt models 
    via huggingface transformers pipelines
    """

    def __init__(
        self,
        source_language: str = "en",
        target_language: str = "es",
        translation_model: str = "helsinki",
    ):
        """
        Initializes the Translator class.

        Args:
            source_language (Optional[str]): Source Language. Defaults to "en". If you use nllb model you should specify
                                             it following the right format: i.e: "eng_Latn"
            target_language (Optional[str]): Target language. Defaults to "es". If you use nllb model you should specify
                                             it following the right format: i.e: "spa_Latn"
            translation_model (Optional[str]): Model type to use for transcription: "helsinki" or "nllb" are supported.
                                               Defaults to helsinki.
        """
        self.source_language = source_language
        self.target_language = target_language
        self.translation_model = translation_model
        if translation_model == "nllb":
            translator_model_id = "facebook/nllb-200-distilled-600M" 
            self.translator = pipeline("translation", model=translator_model_id)
        else:
            translator_model_id = f"Helsinki-NLP/opus-mt-{source_language}-{target_language}"
            self.translator = pipeline("translation", model=translator_model_id)


    def translate(self, subtitle_list: List[Subtitle]) -> List[Subtitle]:
        texts=[subtitle.content[:400] for subtitle in subtitle_list]
        translations: List[Dict] = []
        if self.translation_model == "nllb":
            translations = self.translator(texts, src_lang=self.source_language, tgt_lang=self.target_language, batch_size=8)
        else:
            translations = self.translator(texts, batch_size=8)
        for subtitle,translation in tqdm(zip(subtitle_list,translations),leave=False,desc="Translating..."):
                subtitle.content=translation['translation_text']
        return subtitle_list

