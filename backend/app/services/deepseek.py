from __future__ import annotations

import httpx

from app.core.config import get_settings


class DeepSeekClient:
    def __init__(self) -> None:
        self.settings = get_settings()

    def status(self) -> dict[str, str | bool]:
        configured = bool(self.settings.deepseek_api_key)
        return {
            'configured': configured,
            'model': self.settings.deepseek_model,
            'base_url': self.settings.deepseek_base_url,
            'message': 'DeepSeek API key configured.' if configured else 'DEEPSEEK_API_KEY is not configured.',
        }

    async def chat(self, messages: list[dict]) -> dict:
        if not self.settings.deepseek_api_key:
            return {
                'status': 'disabled',
                'reason': 'DEEPSEEK_API_KEY is not configured',
                'model': self.settings.deepseek_model,
            }

        payload = {
            'model': self.settings.deepseek_model,
            'messages': messages,
        }
        headers = {
            'Authorization': f'Bearer {self.settings.deepseek_api_key}',
            'Content-Type': 'application/json',
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.settings.deepseek_base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    async def test_prompt(self, prompt: str) -> dict[str, str]:
        payload = await self.chat(
            [
                {'role': 'system', 'content': 'Ты помощник по проверке AI-интеграции торговой платформы.'},
                {'role': 'user', 'content': prompt},
            ]
        )
        if payload.get('status') == 'disabled':
            return {
                'status': 'disabled',
                'model': self.settings.deepseek_model,
                'text': 'DeepSeek API key is not configured. Fallback mode is active.',
            }
        choices = payload.get('choices') if isinstance(payload, dict) else None
        if choices:
            content = choices[0].get('message', {}).get('content', '').strip()
            if content:
                return {
                    'status': 'completed',
                    'model': self.settings.deepseek_model,
                    'text': content,
                }
        return {
            'status': 'empty',
            'model': self.settings.deepseek_model,
            'text': 'DeepSeek returned no content.',
        }
