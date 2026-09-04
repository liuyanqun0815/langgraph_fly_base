import importlib.metadata


def test_langgraph_is_1x():
    version = importlib.metadata.version("langgraph")
    assert version.startswith("1.")


def test_langchain_core_is_1x():
    import langchain_core

    assert langchain_core.__version__.startswith("1.")


def test_fastapi_importable():
    import fastapi

    assert fastapi.__version__
