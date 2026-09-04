from sale_app.core.embedding.splade_embedding_model import _patch_transformers_compat


class _FakeTokenizer:
    def __init__(self):
        self.calls = []

    def __call__(self, texts, **kwargs):
        self.calls.append((texts, kwargs))
        return {"input_ids": texts}


def test_patch_transformers_compat_adds_batch_encode_plus():
    class FakeSplade:
        class model:
            tokenizer = _FakeTokenizer()

    splade_ef = FakeSplade()
    _patch_transformers_compat(splade_ef)
    result = splade_ef.model.tokenizer.batch_encode_plus(["a", "b"], padding=True)
    assert result == {"input_ids": ["a", "b"]}
    assert splade_ef.model.tokenizer.calls[0][1]["padding"] is True
