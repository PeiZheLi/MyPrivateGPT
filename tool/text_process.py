import re


def text_split(text: str, max_length: int = 10240) -> list[str]:
    """
    智能文本切分：依据自然段与句界进行长度约束的切分。

    优先保持文本的完整性与可读性，切分优先级：
    1) 换行符 `\n` 2) 句子结束符[。？！.?!] 3) 强制按长度切分。

    Args:
        text (str): 需要切分的原始文本。
        max_length (int): 单段最大长度上限，默认 10240。

    Returns:
        list[str]: 切分后的文本块列表，按原始顺序排列。
    """

    # 预留 10% 安全缓冲，避免超长边界导致模型截断
    max_length = max_length * 0.9

    # 按换行符分割成段落
    paragraphs = text.split('\n')
    chunks = []
    current_chunk = ""

    for paragraph in paragraphs:
        if not paragraph.strip():
            continue

        # 尝试将当前段落合并到当前块
        potential_chunk = current_chunk + ('\n' if current_chunk else '') + paragraph

        if len(potential_chunk) <= max_length:
            # 合并后不超过长度限制，直接合并
            current_chunk = potential_chunk
        else:
            # 合并后超过长度限制，需要处理
            if current_chunk:
                chunks.append(current_chunk)

            if len(paragraph) <= max_length:
                # 段落长度符合要求
                current_chunk = paragraph
            else:
                # 段落过长，需要进一步切分
                sub_chunks = _split_long_paragraph(paragraph, max_length)

                # 将除最后一个子块外的所有子块加入结果
                if len(sub_chunks) > 1:
                    chunks.extend(sub_chunks[:-1])

                # 将最后一个子块作为新的current_chunk，等待与下一段落合并
                current_chunk = sub_chunks[-1] if sub_chunks else ""

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def _split_long_paragraph(paragraph: str, max_length: int) -> list[str]:
    """
    切分过长段落：在最大长度内优先以内/外句界进行分割，否则按长度截断。

    Args:
        paragraph (str): 单个段落文本。
        max_length (int): 单段最大长度上限。

    Returns:
        list[str]: 该段落切分得到的子块列表。
    """

    chunks = []
    remaining = paragraph

    while len(remaining) > max_length:
        search_text = remaining[:max_length]

        sentence_pattern = r'[。？！.?!]'
        matches = list(re.finditer(sentence_pattern, search_text))

        # 默认按最大长度切分，若存在句界则优先用句界位置
        split_pos = 0
        if matches:
            last_match = matches[-1]
            split_pos_candidate = last_match.end()
            if split_pos_candidate <= max_length:
                split_pos = split_pos_candidate

        # 确保至少切分一个字符，防止无限循环
        if split_pos == 0:
            split_pos = max_length

        chunk = remaining[:split_pos]
        remaining = remaining[split_pos:]

        chunks.append(chunk)

    if remaining:
        chunks.append(remaining)

    return chunks
