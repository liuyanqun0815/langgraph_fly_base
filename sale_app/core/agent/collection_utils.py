information_count = 4


def normalize_sequences(raw) -> list[int]:
    if not raw:
        return []
    return sorted({int(s) for s in raw if s is not None})


def is_collection_complete(state: dict) -> bool:
    """四项信息均已写入 state.information_sequences 时为 True。"""
    collected = normalize_sequences(state.get("information_sequences"))
    return len(collected) >= information_count
