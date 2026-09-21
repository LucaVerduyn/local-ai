"""Ollama HTTP client with streaming support."""

from __future__ import annotations

import json
import logging
from collections.abc import Callable, Iterator
from typing import Any

import httpx

from local_ai.core.exceptions import OllamaConnectionError, OllamaError
from local_ai.core.models import OllamaModelInfo

logger = logging.getLogger(__name__)

CancelCallback = Callable[[], bool]


class OllamaClient:
    """Client for the local Ollama HTTP API."""

    def __init__(self, base_url: str, *, timeout: float = 120.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _client(self, *, timeout: float | None = None) -> httpx.Client:
        return httpx.Client(base_url=self.base_url, timeout=timeout or self.timeout)

    def is_available(self) -> bool:
        try:
            with self._client(timeout=5.0) as client:
                response = client.get("/api/tags")
                return response.status_code == 200
        except httpx.HTTPError:
            return False

    def list_models(self) -> list[OllamaModelInfo]:
        try:
            with self._client(timeout=15.0) as client:
                response = client.get("/api/tags")
                response.raise_for_status()
                payload = response.json()
        except httpx.ConnectError as exc:
            raise OllamaConnectionError(
                f"Cannot connect to Ollama. Is it running? Tried {self.base_url}"
            ) from exc
        except httpx.HTTPError as exc:
            raise OllamaError(f"Failed to list models: {exc}") from exc

        models: list[OllamaModelInfo] = []
        for item in payload.get("models", []):
            models.append(
                OllamaModelInfo(
                    name=item.get("name", ""),
                    size=int(item.get("size", 0)),
                    modified_at=str(item.get("modified_at", "")),
                    digest=str(item.get("digest", "")),
                    details=dict(item.get("details") or {}),
                )
            )
        return models

    def pull_model(self, name: str, *, on_progress: Callable[[str], None] | None = None) -> None:
        try:
            with (
                self._client(timeout=None) as client,
                client.stream("POST", "/api/pull", json={"name": name, "stream": True}) as response,
            ):
                response.raise_for_status()
                for line in response.iter_lines():
                    if not line:
                        continue
                    data = json.loads(line)
                    status = str(data.get("status", ""))
                    if on_progress and status:
                        on_progress(status)
                    if data.get("error"):
                        raise OllamaError(str(data["error"]))
        except httpx.ConnectError as exc:
            raise OllamaConnectionError(f"Cannot connect to Ollama at {self.base_url}") from exc
        except httpx.HTTPError as exc:
            raise OllamaError(f"Failed to pull model '{name}': {exc}") from exc

    def delete_model(self, name: str) -> None:
        try:
            with self._client(timeout=30.0) as client:
                response = client.request("DELETE", "/api/delete", json={"name": name})
                response.raise_for_status()
        except httpx.ConnectError as exc:
            raise OllamaConnectionError(f"Cannot connect to Ollama at {self.base_url}") from exc
        except httpx.HTTPError as exc:
            raise OllamaError(f"Failed to delete model '{name}': {exc}") from exc

    def embed(self, model: str, text: str) -> list[float]:
        try:
            with self._client(timeout=60.0) as client:
                response = client.post("/api/embeddings", json={"model": model, "prompt": text})
                response.raise_for_status()
                payload = response.json()
                embedding = payload.get("embedding")
                if not isinstance(embedding, list) or not embedding:
                    raise OllamaError("Ollama returned an empty embedding")
                return [float(x) for x in embedding]
        except httpx.ConnectError as exc:
            raise OllamaConnectionError(f"Cannot connect to Ollama at {self.base_url}") from exc
        except httpx.HTTPError as exc:
            raise OllamaError(f"Embedding failed: {exc}") from exc

    def chat_stream(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
        cancel_check: CancelCallback | None = None,
    ) -> Iterator[str]:
        """Yield streamed assistant tokens from /api/chat."""
        body: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "stream": True,
            "options": {"temperature": temperature},
        }
        try:
            with (
                self._client(timeout=None) as client,
                client.stream("POST", "/api/chat", json=body) as response,
            ):
                if response.status_code >= 400:
                    detail = response.read().decode("utf-8", errors="replace")
                    raise OllamaError(f"Chat request failed ({response.status_code}): {detail}")
                for line in response.iter_lines():
                    if cancel_check and cancel_check():
                        logger.info("Chat stream cancelled by user")
                        break
                    if not line:
                        continue
                    data = json.loads(line)
                    if data.get("error"):
                        raise OllamaError(str(data["error"]))
                    message = data.get("message") or {}
                    content = message.get("content")
                    if content:
                        yield str(content)
                    if data.get("done"):
                        break
        except httpx.ConnectError as exc:
            raise OllamaConnectionError(f"Cannot connect to Ollama at {self.base_url}") from exc
        except httpx.HTTPError as exc:
            raise OllamaError(f"Chat stream failed: {exc}") from exc

    def chat(
        self,
        *,
        model: str,
        messages: list[dict[str, str]],
        temperature: float = 0.7,
    ) -> str:
        return "".join(self.chat_stream(model=model, messages=messages, temperature=temperature))
