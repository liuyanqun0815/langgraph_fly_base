from langchain.schema import runnable

import fasttext

from langchain_experimental.data_anonymizer import PresidioReversibleAnonymizer

from sale_app.config.log import Logger

logger = Logger("fly_base")
model = fasttext.load_model("load_model/lid.176.ftz")

nlp_config = {
    "nlp_engine_name": "spacy",
    "models": [
        {"lang_code": "en", "model_name": "en_core_web_md"},
        {"lang_code": "zh", "model_name": "zh_core_web_sm"},
    ],
}
anonymizer = PresidioReversibleAnonymizer(
    analyzed_fields=["PERSON", "PHONE_NUMBER", "EMAIL_ADDRESS"],
    languages_config=nlp_config,
)

anonymizer.load_deanonymizer_mapping("deanonymizer_mapping.json")


def detect_language(text: str) -> dict:
    language = model.predict(text)[0][0].replace("__label__", "")
    if language is None or language != "en":
        language = "zh"
        logger.info(f"detect language: {language}")
    return {"text": text, "language": language}


# 敏感信息脱敏方法
def sensitive_info_anonymize(text: str) -> str:
    chain = runnable.RunnableLambda(detect_language) | (
        lambda x: anonymizer.anonymize(x["text"], language=x["language"])
    )
    return chain.invoke(text)
