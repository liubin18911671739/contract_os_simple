"""
LLM Service - ZhipuAI unified client
Provides chat, embedding, and reranking capabilities
"""

import asyncio
import logging
import re
import time
from typing import Any, Dict, List

import httpx
from zhipuai import ZhipuAI

from ..config import settings

logger = logging.getLogger(__name__)

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

        Raises:
            RuntimeError: If API call fails or returns empty response
        """
        async with _api_semaphore:
            start_time = time.time()
            # Calculate input token count (rough estimate: 1 token ≈ 2 chars for Chinese)
            input_chars = sum(len(m.get("content", "")) for m in messages)
            input_tokens_est = input_chars // 2

            logger.debug(
                f"LLM chat request: model={self.chat_model}, "
                f"messages={len(messages)}, input_chars={input_chars}, "
                f"temperature={temperature}"
            )

            try:
                response = self.client.chat.completions.create(
                    model=self.chat_model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                content = response.choices[0].message.content

                elapsed = time.time() - start_time
                output_chars = len(content) if content else 0
                output_tokens_est = output_chars // 2

                logger.info(
                    f"LLM chat success: model={self.chat_model}, "
                    f"input_tokens≈{input_tokens_est}, output_tokens≈{output_tokens_est}, "
                    f"time={elapsed:.2f}s"
                )

                if content is None:
                    logger.error("LLM returned empty response (None)")
                    raise RuntimeError("LLM returned empty response (None)")
                if not content.strip():
                    logger.error("LLM returned empty response (whitespace only)")
                    raise RuntimeError("LLM returned empty response (whitespace only)")
                return content
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    f"LLM chat failed after {elapsed:.2f}s: {str(e)}",
                    exc_info=True,
                )
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
            try:
                response_text = await self.chat(messages, temperature)
            except RuntimeError as e:
                # If LLM API failed (e.g., empty response), log and return fallback
                logger.error(f"LLM API call failed on attempt {attempt + 1}: {str(e)}")
                if attempt == max_retries:
                    logger.error("All retry attempts exhausted, using fallback structure")
                    return self._get_fallback_response()
                # Don't retry for API failures, just use fallback
                return self._get_fallback_response()

            logger.debug(
                f"LLM response (attempt {attempt + 1}): {response_text[:200]}..."
            )

            # Try to extract JSON from response
            try:
                # Try direct parse first (strip whitespace to handle common formatting issues)
                result = json.loads(response_text.strip())
                logger.debug(f"Successfully parsed JSON on attempt {attempt + 1}")
                return result
            except json.JSONDecodeError as e:
                # Only log at debug level if it's a whitespace/prefix issue
                if response_text.strip() != response_text and response_text.strip().startswith("{"):
                    logger.debug(f"JSON decode failed (had leading/trailing whitespace), trying fallback strategies")
                else:
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
            start_time = time.time()
            total_chars = sum(len(t) for t in texts)

            logger.debug(
                f"Embedding request: model={self.embed_model}, "
                f"texts={len(texts)}, total_chars={total_chars}"
            )

            try:
                # ZhipuAI API supports batch embedding
                response = self.client.embeddings.create(
                    model=self.embed_model,
                    input=texts,
                )

                # Extract embeddings
                embeddings = [item.embedding for item in response.data]

                elapsed = time.time() - start_time
                logger.info(
                    f"Embedding success: model={self.embed_model}, "
                    f"count={len(embeddings)}, dim={len(embeddings[0]) if embeddings else 0}, "
                    f"time={elapsed:.2f}s"
                )

                return embeddings
            except Exception as e:
                elapsed = time.time() - start_time
                logger.error(
                    f"Embedding failed after {elapsed:.2f}s: {str(e)}",
                    exc_info=True,
                )
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
        Rerank documents by relevance to query using ZhipuAI Rerank API

        Note: ZhipuAI Python SDK doesn't have built-in rerank support,
        so we use direct HTTP call to the API.

        API: https://open.bigmodel.cn/api/paas/v4/rerank

        Args:
            query: Query text
            documents: List of document dicts
            top_n: Number of top results to return
            text_field: Field name containing text to rerank on

        Returns:
            List of reranked documents with scores
        """
        async with _api_semaphore:
            start_time = time.time()
            query_preview = query[:100] + "..." if len(query) > 100 else query

            logger.debug(
                f"Rerank request: model={self.rerank_model}, "
                f"documents={len(documents)}, top_n={top_n}, "
                f"query='{query_preview}'"
            )

            # Extract texts from documents
            texts = [doc.get(text_field, "") for doc in documents]

            if not texts:
                logger.warning("Rerank: No documents to rerank")
                return []

            try:
                # Use direct HTTP call to ZhipuAI rerank API
                # The SDK doesn't have rerank support, so we call the API directly
                async with httpx.AsyncClient(timeout=30.0) as http_client:
                    response = await http_client.post(
                        "https://open.bigmodel.cn/api/paas/v4/rerank",
                        headers={
                            "Authorization": f"Bearer {settings.zhipu_api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": self.rerank_model,
                            "query": query,
                            "documents": texts,
                            "top_n": top_n,
                        },
                    )

                    response.raise_for_status()
                    result = response.json()

                    # Parse results - ZhipuAI returns results with index and relevance_score
                    reranked = []
                    if "results" in result:
                        for item in result["results"]:
                            idx = item.get("index")
                            score = item.get("relevance_score", 0.0)
                            if idx is not None and idx < len(documents):
                                doc = documents[idx].copy()
                                doc["_rerank_score"] = score
                                reranked.append(doc)

                    elapsed = time.time() - start_time
                    top_score = reranked[0]['_rerank_score'] if reranked else 0.0
                    logger.info(
                        f"Rerank success: model={self.rerank_model}, "
                        f"returned={len(reranked)}/{len(documents)}, "
                        f"top_score={top_score:.3f}, "
                        f"time={elapsed:.2f}s"
                    )

                    return reranked

            except httpx.HTTPStatusError as e:
                elapsed = time.time() - start_time
                logger.warning(
                    f"Rerank HTTP error after {elapsed:.2f}s: {e.response.status_code} - {e.response.text[:200]}, "
                    f"returning original order (top {top_n})"
                )
                return documents[:top_n]
            except Exception as e:
                elapsed = time.time() - start_time
                logger.warning(
                    f"Rerank failed after {elapsed:.2f}s: {str(e)}, "
                    f"returning original order (top {top_n})"
                )
                return documents[:top_n]


# Global LLM service instance
_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    """Get or create global LLM service instance"""
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service
