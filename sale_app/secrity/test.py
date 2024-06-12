import langdetect
from langchain.schema import runnable
from langchain_experimental.data_anonymizer import PresidioReversibleAnonymizer


def detect_language(text: str) -> dict:
    language = langdetect.detect(text)
    print(language)
    return {"text": text, "language": language}


nlp_config = {
    "nlp_engine_name": "spacy",
    "models": [
        {"lang_code": "en", "model_name": "en_core_web_md"},
        {"lang_code": "zh-cn", "model_name": "zh_core_web_sm"},
        {"lang_code": "ko", "model_name": "ko_core_news_sm"}
    ],
}
anonymizer = PresidioReversibleAnonymizer(
    analyzed_fields=["PERSON", "LOCATION"],
    languages_config=nlp_config,
)
# print(anonymizer.anonymize("Yo soy Sofía"))


chain = runnable.RunnableLambda(detect_language) | (
    lambda x: anonymizer.anonymize(x["text"], language=x["language"])
)

data = chain.invoke("我叫刘艳群")
print(anonymizer.anonymizer_mapping)
# anonymizer.save_deanonymizer_mapping("deanonymizer_mapping.json")
anonymizer.load_deanonymizer_mapping("deanonymizer_mapping.json")
print(anonymizer.anonymizer_mapping)
print(data)
print(anonymizer.deanonymize(data))
