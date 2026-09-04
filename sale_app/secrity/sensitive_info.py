from pathlib import Path
import urllib.request

import langdetect
from langchain_core.runnables import RunnableLambda
from langchain_experimental.data_anonymizer import PresidioReversibleAnonymizer

from sale_app.config.log import Logger

logger = Logger("fly_base")

_fasttext_model = None
_anonymizer = None

NLP_CONFIG = {
    "nlp_engine_name": "spacy",
    "models": [
        {"lang_code": "en", "model_name": "en_core_web_md"},
        {"lang_code": "zh", "model_name": "zh_core_web_sm"},
    ],
}

FASTTEXT_MODEL_DIR = Path(__file__).resolve().parents[2] / "load_model"
FASTTEXT_MODEL_PATH = FASTTEXT_MODEL_DIR / "lid.176.ftz"
FASTTEXT_MODEL_URL = "https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.ftz"


def ensure_fasttext_model(model_path: Path = FASTTEXT_MODEL_PATH) -> Path:
    """首次使用时自动下载 fastText 语言识别模型。"""
    if model_path.is_file():
        return model_path

    model_path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = model_path.with_suffix(f"{model_path.suffix}.download")
    logger.info(f"Downloading fastText model to {model_path}")

    try:
        urllib.request.urlretrieve(FASTTEXT_MODEL_URL, temp_path)
        temp_path.replace(model_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise

    logger.info(f"fastText model ready at {model_path}")
    return model_path


def _get_fasttext_model():
    global _fasttext_model
    if _fasttext_model is None:
        import fasttext

        ensure_fasttext_model()
        _fasttext_model = fasttext.load_model(str(FASTTEXT_MODEL_PATH))
    return _fasttext_model


def _get_anonymizer() -> PresidioReversibleAnonymizer:
    global _anonymizer
    if _anonymizer is None:
        _anonymizer = PresidioReversibleAnonymizer(
            analyzed_fields=["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS"],
            languages_config=NLP_CONFIG,
        )
    return _anonymizer


def detect_language(text: str) -> dict:
    language = None
    try:
        model = _get_fasttext_model()
        language = model.predict(text)[0][0].replace("__label__", "")
    except Exception as exc:
        logger.info(f"fastText unavailable, fallback to langdetect: {exc}")
        language = langdetect.detect(text)

    if language is None or language != "en":
        language = "zh"
        logger.info(f"detect language: {language}")
    return {"text": text, "language": language}


def sensitive_info_anonymize(text: str) -> str:
    chain = RunnableLambda(detect_language) | (
        lambda x: _get_anonymizer().anonymize(x["text"], language=x["language"])
    )
    return chain.invoke(text)
