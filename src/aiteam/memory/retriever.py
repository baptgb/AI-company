"""AI Team OS — 记忆检索器.

提供关键词搜索、相关性排序和上下文字符串构建功能。
M1阶段使用简单关键词匹配，M2升级向量搜索。
"""

from __future__ import annotations

import re

from aiteam.types import Memory


def _tokenize(text: str) -> set[str]:
    """将文本拆分为小写关键词集合（支持中英文）."""
    # 英文按空格/标点拆分，中文按字符拆分
    tokens: set[str] = set()
    # 英文单词
    for word in re.findall(r"[a-zA-Z0-9_]+", text.lower()):
        if len(word) > 1:
            tokens.add(word)
    # 中文字符（每个字作为token + 连续中文作为短语）
    chinese_chars = re.findall(r"[\u4e00-\u9fff]+", text)
    for phrase in chinese_chars:
        tokens.add(phrase)
        for char in phrase:
            tokens.add(char)
    return tokens


def keyword_search(memories: list[Memory], query: str) -> list[Memory]:
    """简单的关键词匹配搜索.

    对每条记忆计算与查询的关键词命中数，返回命中数 > 0 的记忆。

    Args:
        memories: 待搜索的记忆列表。
        query: 搜索查询字符串。

    Returns:
        匹配的记忆列表（按命中数降序）。
    """
    query_tokens = _tokenize(query)
    if not query_tokens:
        return list(memories)

    scored: list[tuple[int, Memory]] = []
    for mem in memories:
        mem_tokens = _tokenize(mem.content)
        hits = len(query_tokens & mem_tokens)
        if hits > 0:
            scored.append((hits, mem))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [mem for _, mem in scored]


def rank_by_relevance(memories: list[Memory], query: str) -> list[Memory]:
    """按相关性排序记忆.

    M1阶段: 按关键词命中数排序。命中数为0的记忆排在末尾。

    Args:
        memories: 待排序的记忆列表。
        query: 查询字符串。

    Returns:
        排序后的记忆列表。
    """
    query_tokens = _tokenize(query)
    if not query_tokens:
        return list(memories)

    def _score(mem: Memory) -> int:
        mem_tokens = _tokenize(mem.content)
        return len(query_tokens & mem_tokens)

    return sorted(memories, key=_score, reverse=True)


def build_context_string(memories: list[Memory], max_tokens: int = 2000) -> str:
    """将记忆列表格式化为可注入prompt的上下文字符串.

    Args:
        memories: 记忆列表。
        max_tokens: 最大字符数限制（M1阶段以字符数近似token数）。

    Returns:
        格式化后的上下文字符串。
    """
    if not memories:
        return ""

    parts: list[str] = []
    current_length = 0
    header = "=== 相关记忆 ===\n"
    current_length += len(header)
    parts.append(header)

    for i, mem in enumerate(memories, 1):
        entry = f"[{i}] ({mem.scope.value}/{mem.scope_id}) {mem.content}\n"
        if current_length + len(entry) > max_tokens:
            break
        parts.append(entry)
        current_length += len(entry)

    return "".join(parts)
