"""
LLM Service - ZhipuAI unified client
Provides chat, embedding, and reranking capabilities
"""

import asyncio
import re
from typing import Any, Dict, List

from zhipuai import ZhipuAI

from ..config import settings

# Semaphore for API concurrency control
_api_semaphore = asyncio.Semaphore(settings.max_api_concurrent)


class LLMService:
    """Unified LLM service using ZhipuAI"""

    def __init__(self):
        self.client = ZhipuAI(api_key=settings.zhipu_api_key)
        self.chat_model = settings.zhipu_chat_model
        self.embed_model = settings.zhipu_embed_model
        self.rerank_model = settings.zhipu_rerank_model

    async def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 2000,
    ) -> str:
        """
        Send chat completion request

        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text response
        """
        async with _api_semaphore:
            try:
                response = self.client.chat.completions.create(
                    model=self.chat_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content
            except Exception as e:
                raise RuntimeError(f"LLM chat failed: {str(e)}")

    async def chat_with_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_retries: int = 2,
    ) -> Dict[str, Any]:
        """
        Send chat completion request expecting JSON response
        Automatically retries if response is not valid JSON
        Falls back to default structure if all retries fail

        Args:
            messages: List of message dicts
            temperature: Sampling temperature
            max_retries: Maximum retry attempts

        Returns:
            Parsed JSON dict or fallback default structure
        """
        import json
        import logging

        logger = logging.getLogger(__name__)

        for attempt in range(max_retries + 1):
            response_text = await self.chat(messages, temperature)
            logger.debug(
                f"LLM response (attempt {attempt + 1}): {response_text[:200]}..."
            )

            # Try to extract JSON from response
            try:
                # Try direct parse first
                result = json.loads(response_text)
                logger.debug(f"Successfully parsed JSON on attempt {attempt + 1}")
                return result
            except json.JSONDecodeError as e:
                logger.warning(f"JSON decode failed on attempt {attempt + 1}: {str(e)}")

                # Try multiple extraction strategies
                result = self._try_extract_json(response_text)
                if result:
                    logger.info(
                        f"Successfully extracted JSON using fallback strategy on attempt {attempt + 1}"
                    )
                    return result

                # If last attempt, return fallback instead of raising
                if attempt == max_retries:
                    logger.error(
                        f"Failed to parse JSON after {max_retries} retries. Using fallback structure."
                    )
                    logger.debug(f"Failed response: {response_text[:1000]}")
                    return self._get_fallback_response()

                # Add retry prompt with more specific instructions
                messages.append(
                    {
                        "role": "assistant",
                        "content": response_text,
                    }
                )
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "Your response was not valid JSON. Please respond ONLY with valid JSON format. "
                            "Do not include any explanatory text outside the JSON. "
                            "The response must start with '{' and end with '}'."
                        ),
                    }
                )

    def _try_extract_json(self, text: str) -> Dict[str, Any] | None:
        """
        Try multiple strategies to extract JSON from text

        Args:
            text: Text that may contain JSON

        Returns:
            Parsed JSON dict or None
        """
        import json
        import re

        strategies = [
            # Strategy 1: Find JSON between curly braces
            lambda t: self._extract_braces(t),
            # Strategy 2: Extract from ```json code block
            lambda t: self._extract_from_markdown(t, "json"),
            # Strategy 3: Extract from any ``` code block
            lambda t: self._extract_from_markdown(t, None),
            # Strategy 4: Try to fix common JSON issues
            lambda t: self._fix_and_parse(t),
        ]

        for strategy in strategies:
            try:
                result = strategy(text)
                if result:
                    return result
            except Exception:
                continue

        return None

    def _extract_braces(self, text: str) -> Dict[str, Any] | None:
        """Extract JSON from first complete { } pair"""
        import json

        # Find first { and last }
        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end != -1 and end > start:
            try:
                json_str = text[start : end + 1]
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass

        return None

    def _extract_from_markdown(
        self, text: str, lang: str | None
    ) -> Dict[str, Any] | None:
        """Extract JSON from markdown code block"""
        import json

        if lang:
            pattern = f"```{lang}\\s*([\\s\\S]*?)```"
        else:
            pattern = "```\\s*([\\s\\S]*?)```"

        import re

        match = re.search(pattern, text, re.DOTALL)

        if match:
            try:
                code = match.group(1).strip()
                return json.loads(code)
            except json.JSONDecodeError:
                pass

        return None

    def _fix_and_parse(self, text: str) -> Dict[str, Any] | None:
        """Try to fix common JSON issues and parse"""
        import json

        fixes = [
            # Remove trailing commas
            lambda t: re.sub(r",\\s*([}\\]])", r"\\1", t),
            # Fix single quotes to double quotes
            lambda t: t.replace("'", '"'),
            # Remove comments
            lambda t: re.sub(r"//.*", "", t),
            # Extract JSON if embedded in text
            lambda t: self._extract_braces(t),
        ]

        for fix in fixes:
            try:
                fixed_text = fix(text)
                return json.loads(fixed_text)
            except Exception:
                continue

        return None

    def _get_fallback_response(self) -> Dict[str, Any]:
        """
        Return a safe fallback structure when LLM fails to produce valid JSON

        Returns:
            Default risk analysis structure
        """
        return {
            "risks": [
                {
                    "risk_level": "INFO",
                    "risk_type": "LLM_ERROR",
                    "confidence": 0.0,
                    "summary": "LLM分析失败，需要人工审查。LLM分析出现问题，无法生成结构化风险数据，请手动检查合同条款。",
                    "kb_evidence": [],
                }
            ]
        }

    async def embed(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for texts

        Args:
            texts: List of text strings

        Returns:
            List of embedding vectors
        """
        async with _api_semaphore:
            try:
                # ZhipuAI API supports batch embedding
                response = self.client.embeddings.create(
                    model=self.embed_model,
                    input=texts,
                )

                # Extract embeddings
                embeddings = [item.embedding for item in response.data]
                return embeddings
            except Exception as e:
                raise RuntimeError(f"Embedding generation failed: {str(e)}")

    async def embed_single(self, text: str) -> List[float]:
        """
        Generate embedding for a single text

        Args:
            text: Text string

        Returns:
            Embedding vector
        """
        embeddings = await self.embed([text])
        return embeddings[0]

    async def rerank(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_n: int = 6,
        text_field: str = "text",
    ) -> List[Dict[str, Any]]:
        """
        Rerank documents by relevance to query

        Args:
            query: Query text
            documents: List of document dicts
            top_n: Number of top results to return
            text_field: Field name containing text to rerank on

        Returns:
            List of reranked documents with scores
        """
        async with _api_semaphore:
            try:
                # Extract texts from documents
                texts = [doc.get(text_field, "") for doc in documents]

                # Call rerank API
                response = self.client.model_api.invoke(
                    model=self.rerank_model,
                    data={
                        "query": query,
                        "documents": texts,
                        "top_n": top_n,
                    },
                )

                # Parse results
                results = response.get("results", [])

                # Reorder documents and add scores
                reranked = []
                for result in results:
                    idx = result["index"]
                    score = result["relevance_score"]
                    doc = documents[idx].copy()
                    doc["_rerank_score"] = score
                    reranked.append(doc)

                return reranked
            except Exception as e:
                # If rerank fails, return original documents
                print(f"Warning: Rerank failed ({str(e)}), returning original order")
                return documents[:top_n]


# Global LLM service instance
_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    """Get or create global LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
