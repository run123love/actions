from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, MutableMapping
import os


@dataclass
class Context:
    g: MutableMapping[str, Any]

    def close(self):
        print(self.g)


@dataclass
class MixContext:
    ctx: Context = field(repr=False)

    def __enter__(self):
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any):
        self.ctx.close()


class MixSharedState(abc.ABC):
    ctx: Context

    def init_state(self, field: str | None = None, suffix: Any = None):
        self._g = self.ctx.g
        self.field = field or type(self).__name__
        if suffix:
            self.field = f"{self.field}_{suffix}"
        if self.field in self._g:
            raise ValueError(f"Field {self.field} already exists in global state")
        self._g[self.field] = {}

    @property
    def state(self) -> MutableMapping[str, Any]:
        return self._g[self.field]

    def set(self, key: str, value: Any):
        self.state[key] = value

    def get(self, key: str) -> Any:
        return self.state.get(key)
    
    def get_or_set(self, key: str, default: Any) -> Any:
        return self.state.setdefault(key, default)


@dataclass
class MakeDirs(MixContext, MixSharedState):
    paths: list[str]
    uuid: Any | None = None

    def __post_init__(self):
        self.init_state(suffix=self.uuid)
        self.created_dirs: list[str] = self.get_or_set("created_dirs", [])

    def handle(self):
        for path in self.paths:
            if os.path.exists(path):
                continue
            os.mkdir(path)
            print(f"Created directory {path}")
            self.created_dirs.append(path)

    def rollback(self):
        while self.created_dirs:
            path = self.created_dirs.pop()
            if os.path.exists(path):
                os.rmdir(path)
                print(f"Removed directory {path}")


cmd = MakeDirs(Context({}), paths=["/tmp/a", "/tmp/b"], uuid=1)
print(cmd)
with cmd:
    cmd.handle()
with cmd:
    cmd.rollback()

