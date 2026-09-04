from pathlib import Path

from sale_app.util.file_utils import find_project_root


def test_find_project_root_from_flow_graph_module():
    root = find_project_root(__file__)
    assert root is not None
    root_path = Path(root)
    assert (root_path / "app" / "main.py").is_file()
    assert (root_path / "config.py").is_file()
