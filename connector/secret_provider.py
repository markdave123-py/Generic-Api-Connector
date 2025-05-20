from __future__ import annotations
import os, abc, pathlib


"""
SecretProvider abstraction + two concrete back-ends:

• EnvProvider -> current behaviour (reads os.environ)
• FileProvider -> reads Docker secrets from /run/secrets/<name>
                 (works with docker-compose secrets & Docker Swarm if there is need for change)

"""


class SecretProvider(abc.ABC):
    @abc.abstractmethod
    async def get(self, name: str) -> str:
        ...


class EnvProvider(SecretProvider):
    async def get(self, name: str) -> str:
        return os.environ[name]


class FileProvider(SecretProvider):
    _BASE = pathlib.Path(os.getenv("DOCKER_SECRETS_DIR", "/run/secrets"))

    async def get(self, name: str) -> str:
        path = self._BASE / name
        if not path.exists():
            raise FileNotFoundError(f"Docker secret {name!r} not found in {self._BASE}")
        return path.read_text().strip()
