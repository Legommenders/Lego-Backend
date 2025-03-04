import json

from typing import Protocol, cast


class SupportsWrite(Protocol):
    def write(self, __s: str) -> object:
        ...


def json_load(filepath: str):
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def json_loads(s: str):
    return json.loads(s)


def json_dumps(obj) -> str:
    return json.dumps(obj, indent=2, ensure_ascii=False)


def json_save(obj, filepath: str):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(obj, cast(SupportsWrite, f), indent=2, ensure_ascii=False)
