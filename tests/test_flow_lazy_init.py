import importlib


def test_import_flow_graph_does_not_set_chain():
    mod = importlib.import_module("sale_app.core.mutil.flow_graph")
    importlib.reload(mod)
    assert getattr(mod, "_chain", None) is None
