from typing import Iterator, Optional
from openai import OpenAI
from config.model_config import supplier_dict, model_dict


def chat_llm(
        input_text: str,
        input_model: str,
        prompt: Optional[str],
        input_top_p: float = 0.7,
        input_temperature: float = 0.9,
) -> str:
    """
    非流式单次对话接口：与 OpenAI 兼容服务交互，返回完整文本。

    Args:
        input_text (str): 用户输入文本。
        input_model (str): 模型名称，对应 `model_dict` 的键。
        prompt (Optional[str]): 系统提示词；若为空则使用默认助手提示词。
        input_top_p (float): nucleus sampling 参数，范围 [0, 1]。
        input_temperature (float): 输出多样性温度，范围 [0, 1]。

    Returns:
        str: 模型返回的完整文本内容。
    """
    model_supplier = model_dict[input_model]["supplier"]

    client = OpenAI(
        api_key=supplier_dict[model_supplier]["api"],
        base_url=supplier_dict[model_supplier]["url"],
    )

    if not prompt:
        prompt = "You are a helpful assistant."

    completion = client.chat.completions.create(
        model=input_model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": input_text},
        ],
        top_p=input_top_p,
        temperature=input_temperature,
        max_tokens=model_dict[input_model]["max_tokens"],
        stream=False,
    )

    return str(completion.choices[0].message.content)


def chat_llm_stream(
        input_text: str,
        input_model: str,
        prompt: Optional[str],
        input_top_p: float = 0.7,
        input_temperature: float = 0.9,
) -> Iterator[str]:
    """
    流式对话接口：以增量方式返回模型输出，适合 UI 实时展示。

    Args:
        input_text (str): 用户输入文本。
        input_model (str): 模型名称。
        prompt (Optional[str]): 系统提示词；若为空则使用默认助手提示词。
        input_top_p (float): nucleus sampling 参数。
        input_temperature (float): 输出多样性温度。

    Yields:
        str: 模型返回的增量文本内容。
    """
    model_supplier = model_dict[input_model]["supplier"]

    client = OpenAI(
        api_key=supplier_dict[model_supplier]["api"],
        base_url=supplier_dict[model_supplier]["url"],
    )

    if not prompt:
        prompt = "You are a helpful assistant."

    completion = client.chat.completions.create(
        model=input_model,
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": input_text},
        ],
        top_p=input_top_p,
        temperature=input_temperature,
        max_tokens=model_dict[input_model]["max_tokens"],
        stream=True,
    )

    for chunk in completion:
        yield chunk.choices[0].delta.content or ""
