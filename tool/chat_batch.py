from concurrent.futures import ThreadPoolExecutor, as_completed
import queue
import time
from typing import Callable, Dict, Optional
from config.model_config import model_dict

from tool.chat import chat_llm_stream


def _notify_progress(on_progress: Optional[Callable[[Dict[str, int]], None]],
                     total: int, processed: int) -> None:
    """集中式进度通知：统一格式减少重复代码。"""
    if on_progress:
        on_progress({
            "total": total,
            "processed": processed,
        })


def _notify_item(on_item: Optional[Callable[[Dict[str, object]], None]],
                 index: int, text: str, flag: bool = False) -> None:
    """集中式单项通知：统一回调负载减少重复代码。"""
    if on_item:
        on_item({
            "index": index,
            "text": text,
            "flag": flag,
        })


def chat_llm_batch(
        text_list: list[str],
        input_model: str,
        prompt: str,
        input_top_p: float = 0.7,
        input_temperature: float = 0.9,
        on_progress: Optional[Callable[[Dict[str, int]], None]] = None,
        on_item: Optional[Callable[[Dict[str, object]], None]] = None,
        max_concurrent: int = 10,
) -> str:
    """
    并发批量对话，将多条文本输入分别与模型交互并汇总结果。

    Args:
        text_list (list[str]): 需要处理的文本列表，每项作为一次对话的输入。
        input_model (str): 模型名称，需存在于 `model_dict` 中。
        prompt (str): 系统提示词，用于指导模型行为。
        input_top_p (float): nucleus sampling 参数，范围 [0, 1]。
        input_temperature (float): 输出多样性温度，范围 [0, 1]。
        on_progress (Optional[Callable[[Dict[str, int]], None]]): 进度回调，仅包含总数与已处理。
        on_item (Optional[Callable[[Dict[str, object]], None]]): 单项回调，包含索引、文本、标记 `flag`。
        max_concurrent (int): 并发线程数量上限（将进行有效性与上限校验）。

    Returns:
        str: 按原始顺序合并的所有结果文本，使用双换行分隔。
    """
    result_queue: queue.Queue[tuple[int, str]] = queue.Queue()
    completed_count = 0
    failed_count = 0
    total_tasks = len(text_list)
    max_concurrent = model_dict.get(input_model).get("max_concurrent")

    def process_item_with_retry(item: str, index: int, max_retries: int = 3, retry_delay: int = 1) -> None:
        """
        带重试机制的单个文本处理函数（流式）。

        Args:
            item (str): 单条文本输入。
            index (int): 文本在原始列表中的索引，用于结果排序。
            max_retries (int): 最大重试次数。
            retry_delay (int): 初始重试延迟（秒），采用指数退避。
        """

        nonlocal completed_count, failed_count

        for attempt in range(max_retries):
            try:
                accum_text = ""
                # 流式获取增量内容，并实时刷新输出/回调
                for chunk in chat_llm_stream(
                        item,
                        input_model,
                        prompt,
                        input_top_p,
                        input_temperature,
                ):
                    if chunk:
                        accum_text += chunk
                        _notify_item(on_item, index, accum_text, flag=False)

                # 单项完成，入队并刷新进度
                result_queue.put((index, accum_text))
                completed_count += 1
                _notify_progress(on_progress, total_tasks, completed_count)
                # 最终完成态通知（兼容仅在完成时更新的使用场景）
                _notify_item(on_item, index, accum_text, flag=False)

                return
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (2 ** attempt))
                else:
                    result_queue.put((index, f"错误: {str(e)}"))
                    completed_count += 1
                    failed_count += 1
                    _notify_progress(on_progress, total_tasks, completed_count)
                    _notify_item(on_item, index, f"错误: {str(e)}", flag=True)

    # 初始化进度
    _notify_progress(on_progress, total_tasks, completed_count)

    with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
        futures = [executor.submit(process_item_with_retry, item, i)
                   for i, item in enumerate(text_list)]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"任务执行异常: {e}")

    results = [result_queue.get() for _ in range(len(text_list))]
    results.sort(key=lambda x: x[0])

    cleaned_results = []
    for result in results:
        cleaned_result = '\n'.join(line for line in result[1].split('\n') if line.strip())
        cleaned_results.append(cleaned_result)

    # 结束进度
    _notify_progress(on_progress, total_tasks, completed_count)

    return "\n\n".join(cleaned_results)
