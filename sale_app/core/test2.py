

import langdetect
from langchain.schema import runnable


import fasttext
from langchain_experimental.data_anonymizer import PresidioReversibleAnonymizer

model = fasttext.load_model("load_model/lid.176.bin")

nlp_config = {
    "nlp_engine_name": "spacy",
    "models": [
        {"lang_code": "en", "model_name": "en_core_web_md"},
        {"lang_code": "zh-cn", "model_name": "zh_core_web_sm"},
        {"lang_code": "ko", "model_name": "ko_core_news_sm"}
    ],
}
anonymizer = PresidioReversibleAnonymizer(
    analyzed_fields=["姓名"],
    languages_config=nlp_config,
)

def detect_language(text: str) -> dict:
    language = model.predict(text)[0][0].replace("__label__", "")
    print(language)
    return {"text": text, "language": language}


chain = runnable.RunnableLambda(detect_language) | (
    lambda x: anonymizer.anonymize(x["text"], language=x["language"])
)