import webbrowser
import threading
import queue
import gradio as gr
import config.model_config as model_config
from typing import Iterator, Optional, Tuple
from config.function_config import function_dict
from tool.chat import chat_llm_stream
from tool.chat_batch import chat_llm_batch
from tool.text_process import text_split

# ==== Shared Defaults & UI Helpers ====
DEFAULT_TOP_P = 0.7
DEFAULT_TEMPERATURE = 0.9

model_choices = list(model_config.model_dict.keys())


def create_param_sliders(initial_top_p: float = DEFAULT_TOP_P,
                         initial_temperature: float = DEFAULT_TEMPERATURE):
    """
    创建参数滑块：返回一组带统一默认值与样式的 `top_p` 与 `temperature` 滑块。

    Returns:
        tuple[gr.Slider, gr.Slider]: (top_p 滑块, temperature 滑块)
    """
    top_p_slider = gr.Slider(0, 1, value=initial_top_p, step=0.1, interactive=True, label="top_p")
    temperature_slider = gr.Slider(0, 2, value=initial_temperature, step=0.1, interactive=True, label="temperature")
    return top_p_slider, temperature_slider


def format_progress_md(status: dict | None = None) -> str:
    """
    渲染批量进度面板的 Markdown 文本。

    Args:
        status (Optional[dict]): 进度字典，包含 `total` 与 `processed` 等键。

    Returns:
        str: 进度面板 Markdown 字符串。
    """
    total = (status or {}).get("total", 0)
    processed = (status or {}).get("processed", 0)
    return (
        f"**批量处理进度{processed}/{total}**"
    )


def MFG_respond(
        input_text: str,
        input_model: str,
        input_function: str = "NONE",
        self_prompt_text: Optional[str] = None,
        input_top_p: float = 0.7,
        input_temperature: float = 0.9,
) -> Iterator[str]:
    """
    使用指定功能或自定义提示词，进行单次对话并以流式方式返回模型输出。

    Args:
        input_text (str): 用户输入的文本。
        input_model (str): 模型名称，需存在于 `model_config.model_dict` 中。
        input_function (str): 预设功能键，用于从 `function_dict` 选择系统提示词。
        self_prompt_text (Optional[str]): 自定义系统提示词，若提供则覆盖预设功能提示词。
        input_top_p (float): nucleus sampling 参数，范围 [0, 1]。
        input_temperature (float): 输出多样性温度，范围 [0, 1]。

    Yields:
        str: 累积的模型输出文本（逐步追加）。
    """
    prompt = function_dict[input_function]
    if self_prompt_text:
        prompt = self_prompt_text

    output_text = ""
    for chunk in chat_llm_stream(input_text, input_model, prompt, input_top_p, input_temperature):
        output_text += chunk
        yield output_text


def MFG_clear() -> Tuple[str, str]:
    """
    清空 MultiFunctionGPT 标签页的输入与输出。

    Returns:
        tuple[str, str]: 置空后的输入文本与输出文本。
    """
    return "", ""


def MFG_init() -> Tuple[str, str, float, float]:
    """
    初始化 MultiFunctionGPT 标签页，设置默认输入与采样参数。

    Returns:
        tuple[str, str, float, float]: 空输入、空输出、默认 `top_p` 与 `temperature`。
    """
    return "", "", DEFAULT_TOP_P, DEFAULT_TEMPERATURE


def BA_respond(
        prompt: str,
        text: str,
        function: str,
        input_model: str,
        input_top_p: float = 0.7,
        input_temperature: float = 0.9,
) -> Iterator[Tuple[str, str]]:
    """
    批量代理入口：根据功能类型将输入文本切分为列表并并发处理。

    Args:
        prompt (str): 自定义系统提示词，若提供则覆盖预设功能提示词。
        text (str): 需要批量处理的原始文本（多行或长文本）。
        function (str): 批量功能类型，支持 "列表任务" 或 "长任务"。
        input_model (str): 模型名称，需存在于 `model_config.model_dict` 中。
        input_top_p (float): nucleus sampling 参数，范围 [0, 1]。
        input_temperature (float): 输出多样性温度，范围 [0, 1]。

    Yields:
        tuple[str, str]: (输出文本, 右下角进度面板 HTML)。输出文本在处理结束时返回最终结果，进度面板会实时刷新。
    """
    # 依据模型配置的 max_tokens 作为文本切分的最大长度
    max_length = model_config.model_dict[input_model]["max_tokens"]

    if function == "列表任务":
        text_list = text.split("\n")
        text_list = [i.strip() for i in text_list if i.strip() != ""]
    elif function == "长任务":
        text_list = text_split(text, max_length - len(prompt))
    else:
        text_list = [text]

    # 渲染进度面板 Markdown（在页面内显示）

    progress_queue: queue.Queue[str | None] = queue.Queue()
    output_queue: queue.Queue[str] = queue.Queue()
    final_result: dict = {"text": None}
    buffered_results: dict[int, str] = {}

    def on_progress(status: dict) -> None:
        progress_queue.put(format_progress_md(status))

    def worker() -> None:
        try:
            def on_item(ev: dict) -> None:
                index = int(ev.get("index", 0))
                text_val = str(ev.get("text", ""))
                buffered_results[index] = text_val
                # 生成当前所有已完成/进行中的有序增量文本（不再被最前项阻塞）
                merged_parts: list[str] = []
                for i in range(len(text_list)):
                    part = buffered_results.get(i, "")
                    if part:
                        merged_parts.append(part)
                if merged_parts:
                    output_queue.put("\n\n".join(merged_parts))

            res = chat_llm_batch(
                text_list,
                input_model,
                prompt,
                input_top_p,
                input_temperature,
                on_progress=on_progress,
                on_item=on_item,
            )
            final_result["text"] = res
        except Exception as e:
            final_result["text"] = f"错误: {str(e)}"
        finally:
            # 通知生成器结束
            progress_queue.put(None)  # type: ignore

    threading.Thread(target=worker, daemon=True).start()

    # 初始面板
    current_output: str = ""
    current_progress: str = format_progress_md({
        "total": len(text_list),
        "processed": 0,
    })
    yield current_output, current_progress

    # 实时刷新面板与输出
    while True:
        try:
            updated = False
            # 先尝试获取输出增量
            try:
                new_output = output_queue.get(timeout=0.05)
                if new_output:
                    current_output += new_output
                    updated = True
            except queue.Empty:
                pass

            # 再尝试获取进度更新
            try:
                md = progress_queue.get(timeout=0.05)
                if md is None:
                    break
                current_progress = md
                updated = True
            except queue.Empty:
                pass

            if updated:
                yield current_output, current_progress
        except queue.Empty:
            # 无更新，继续等待
            if final_result["text"] is not None:
                break

    # 返回最终结果与最终面板
    final_text = final_result["text"] or ""
    yield final_text, format_progress_md({
        "total": len(text_list),
        "processed": len(text_list),
    })


def BA_clear() -> Tuple[str, str, str, str]:
    """
    清空 BatchAgent 标签页的输入、提示词与输出。

    Returns:
        tuple[str, str, str, str]: 空输入、空提示词、空输出、默认进度面板。
    """
    return "", "", "", format_progress_md()


def MC_respond_single(
        input_text: str,
        input_model: str,
        prompt_text: str,
        input_top_p: float,
        input_temperature: float,
) -> Iterator[str]:
    """
    单模型比较：对输入文本执行一次流式对话并逐步返回结果。

    Args:
        input_text (str): 用户输入文本。
        input_model (str): 模型名称。
        prompt_text (str): 系统提示词。
        input_top_p (float): nucleus sampling 参数。
        input_temperature (float): 输出多样性温度。

    Yields:
        str: 累积的模型输出文本。
    """
    output_text = ""
    for chunk in chat_llm_stream(input_text, input_model, prompt_text, input_top_p, input_temperature):
        output_text += chunk
        yield output_text


def MC_respond_compare(
        input_text: str,
        model1: str,
        model2: str,
        model3: str,
        prompt_text: str,
        input_top_p1: float,
        input_temperature1: float,
        input_top_p2: float,
        input_temperature2: float,
        input_top_p3: float,
        input_temperature3: float,
) -> Iterator[Tuple[str, str, str]]:
    """
    多模型并行比较：同时对三个模型进行流式生成，逐步返回各自的累积输出。

    Args:
        input_text (str): 用户输入文本。
        model1 (str): 模型1名称。
        model2 (str): 模型2名称。
        model3 (str): 模型3名称。
        prompt_text (str): 系统提示词。
        input_top_p1 (float): 模型1的 top_p。
        input_temperature1 (float): 模型1的 temperature。
        input_top_p2 (float): 模型2的 top_p。
        input_temperature2 (float): 模型2的 temperature。
        input_top_p3 (float): 模型3的 top_p。
        input_temperature3 (float): 模型3的 temperature。

    Yields:
        tuple[str, str, str]: 三个模型当前的累积输出文本。
    """
    # 使用独立线程与队列实现非阻塞的三路流式聚合
    import threading
    import queue as _queue

    q1: _queue.Queue[str | None] = _queue.Queue()
    q2: _queue.Queue[str | None] = _queue.Queue()
    q3: _queue.Queue[str | None] = _queue.Queue()

    def worker(model: str, top_p: float, temperature: float, out_q: _queue.Queue[str | None]) -> None:
        try:
            for chunk in chat_llm_stream(input_text, model, prompt_text, top_p, temperature):
                if chunk:
                    out_q.put(chunk)
        finally:
            # 使用 None 作为完成标记
            out_q.put(None)

    threading.Thread(target=worker, args=(model1, input_top_p1, input_temperature1, q1), daemon=True).start()
    threading.Thread(target=worker, args=(model2, input_top_p2, input_temperature2, q2), daemon=True).start()
    threading.Thread(target=worker, args=(model3, input_top_p3, input_temperature3, q3), daemon=True).start()

    text1, text2, text3 = "", "", ""
    done1 = done2 = done3 = False

    while not (done1 and done2 and done3):
        updated = False
        try:
            v1 = q1.get(timeout=0.05)
            if v1 is None:
                done1 = True
            else:
                text1 += v1
                updated = True
        except _queue.Empty:
            pass

        try:
            v2 = q2.get(timeout=0.05)
            if v2 is None:
                done2 = True
            else:
                text2 += v2
                updated = True
        except _queue.Empty:
            pass

        try:
            v3 = q3.get(timeout=0.05)
            if v3 is None:
                done3 = True
            else:
                text3 += v3
                updated = True
        except _queue.Empty:
            pass

        if updated:
            yield text1, text2, text3


def MC_clear() -> Tuple[str, str, str, str, str]:
    """
    清空 ModelComparison 标签页的输入、各输出与提示词。

    Returns:
        tuple[str, str, str, str, str]: 空输入、三个空输出、空提示词。
    """
    return "", "", "", "", ""


def MC_clear_single() -> str:
    """
    清空单个模型的输出框。

    Returns:
        str: 空字符串。
    """
    return ""


# ===== Unified Gradio App with Tabs =====
with gr.Blocks(title="MyChatGPT", theme=gr.themes.Soft()) as interface:
    with gr.Tab("MultiFunctionGPT"):
        with gr.Row():
            with gr.Column():
                MFG_input_text = gr.Textbox(label="问题", placeholder="请输入问题...", lines=25, show_copy_button=True)
                with gr.Row():
                    MFG_submit_button = gr.Button("提交")
                    MFG_clear_button = gr.Button("清空")
                    MFG_init_button = gr.Button("初始化")
                MFG_function = gr.Radio(list(function_dict.keys()), label="功能", value="NONE")
                MFG_model = gr.Dropdown(label="AI模型", choices=model_choices, value=model_choices[0])
                with gr.Accordion("参数", open=False):
                    MFG_top_p, MFG_temperature = create_param_sliders()
            with gr.Column():
                MFG_output_text = gr.Textbox(label="回复", placeholder="等待回复...", lines=30, show_copy_button=True)
                MFG_self_prompt_text = gr.Textbox(label="提示词", placeholder="自定义提示词...\n具有最高优先级",
                                                  lines=5,
                                                  value=None)

        MFG_inputs = [MFG_input_text, MFG_model, MFG_function, MFG_self_prompt_text, MFG_top_p, MFG_temperature]
        MFG_outputs = [MFG_output_text]

        MFG_submit_button.click(MFG_respond, inputs=MFG_inputs, outputs=MFG_outputs)
        MFG_clear_button.click(MFG_clear, inputs=[], outputs=[MFG_input_text, MFG_output_text])
        MFG_init_button.click(MFG_init, inputs=[],
                              outputs=[MFG_input_text, MFG_output_text, MFG_top_p, MFG_temperature])

    with gr.Tab("BatchAgent"):
        with gr.Row():
            with gr.Column():
                BA_input_text = gr.Textbox(label="问题", placeholder="请输入问题...", lines=25, show_copy_button=True)
                with gr.Row():
                    BA_submit_button = gr.Button("提交")
                    BA_clear_button = gr.Button("清空")
                BA_self_prompt = gr.Textbox(label="提示词", placeholder="提示词...", lines=5, value=None)
                BA_function = gr.Radio(["列表任务", "长任务"], label="功能", value="长任务")
                BA_model = gr.Dropdown(label="AI模型", choices=model_choices,
                                       value=model_choices[0])
                with gr.Accordion("参数", open=False):
                    BA_top_p, BA_temperature = create_param_sliders()
            with gr.Column():
                BA_output_text = gr.Textbox(label="回复", placeholder="等待回复...", lines=35, show_copy_button=True)
                BA_progress = gr.Markdown(value=format_progress_md(), label="进度")

        BA_inputs = [BA_self_prompt, BA_input_text, BA_function, BA_model, BA_top_p, BA_temperature]
        BA_outputs = [BA_output_text, BA_progress]
        BA_submit_button.click(BA_respond, inputs=BA_inputs, outputs=BA_outputs)
        BA_clear_button.click(BA_clear, inputs=[], outputs=[BA_input_text, BA_self_prompt, BA_output_text, BA_progress])

    with gr.Tab("ModelComparison"):
        with gr.Row():
            with gr.Column():
                MC_input_text = gr.Textbox(label="问题", placeholder="请输入问题...", lines=25, show_copy_button=True)
                MC_prompt_text = gr.Textbox(label="提示词", placeholder="提示词...", lines=5)

                with gr.Row():
                    MC_submit_all_button = gr.Button("全部提交")
                    MC_clear_all_button = gr.Button("全部清空")
                    MC_init_button = gr.Button("初始化")

                with gr.Accordion("参数", open=False):
                    MC_top_p, MC_temperature = create_param_sliders()

            with gr.Column():
                gr.Markdown("### 模型1")
                MC_output_1 = gr.Textbox(label="回复", placeholder="等待回复...", lines=30, show_copy_button=True)
                MC_model_1 = gr.Dropdown(label="模型1", choices=model_choices,
                                         value=model_choices[0])
                with gr.Accordion("参数", open=False):
                    MC_top_p_1, MC_temperature_1 = create_param_sliders()

                with gr.Row():
                    MC_submit_button_1 = gr.Button("提交")
                    MC_clear_button_1 = gr.Button("清空")

            with gr.Column():
                gr.Markdown("### 模型2")
                MC_output_2 = gr.Textbox(label="回复", placeholder="等待回复...", lines=30, show_copy_button=True)
                MC_model_2 = gr.Dropdown(label="模型2", choices=model_choices,
                                         value=model_choices[1] if len(model_choices) > 1 else model_choices[0])
                with gr.Accordion("参数", open=False):
                    MC_top_p_2, MC_temperature_2 = create_param_sliders()

                with gr.Row():
                    MC_submit_button_2 = gr.Button("提交")
                    MC_clear_button_2 = gr.Button("清空")

            with gr.Column():
                gr.Markdown("### 模型3")
                MC_output_3 = gr.Textbox(label="回复", placeholder="等待回复...", lines=30, show_copy_button=True)
                MC_model_3 = gr.Dropdown(label="模型3", choices=model_choices,
                                         value=model_choices[2] if len(model_choices) > 2 else model_choices[0])
                with gr.Accordion("参数", open=False):
                    MC_top_p_3, MC_temperature_3 = create_param_sliders()
                with gr.Row():
                    MC_submit_button_3 = gr.Button("提交")
                    MC_clear_button_3 = gr.Button("清空")

        MC_all_inputs = [MC_input_text, MC_model_1, MC_model_2, MC_model_3, MC_prompt_text,
                         MC_top_p_1, MC_temperature_1, MC_top_p_2, MC_temperature_2, MC_top_p_3, MC_temperature_3]
        MC_all_outputs = [MC_output_1, MC_output_2, MC_output_3]
        MC_submit_all_button.click(MC_respond_compare, inputs=MC_all_inputs, outputs=MC_all_outputs)
        MC_clear_all_button.click(MC_clear, inputs=[],
                                  outputs=[MC_input_text, MC_output_1, MC_output_2, MC_output_3, MC_prompt_text])

        MC_model_inputs_1 = [MC_input_text, MC_model_1, MC_prompt_text, MC_top_p_1, MC_temperature_1]
        MC_submit_button_1.click(MC_respond_single, inputs=MC_model_inputs_1, outputs=[MC_output_1])
        MC_clear_button_1.click(MC_clear_single, inputs=[], outputs=[MC_output_1])

        MC_model_inputs_2 = [MC_input_text, MC_model_2, MC_prompt_text, MC_top_p_2, MC_temperature_2]
        MC_submit_button_2.click(MC_respond_single, inputs=MC_model_inputs_2, outputs=[MC_output_2])
        MC_clear_button_2.click(MC_clear_single, inputs=[], outputs=[MC_output_2])

        MC_model_inputs_3 = [MC_input_text, MC_model_3, MC_prompt_text, MC_top_p_3, MC_temperature_3]
        MC_submit_button_3.click(MC_respond_single, inputs=MC_model_inputs_3, outputs=[MC_output_3])
        MC_clear_button_3.click(MC_clear_single, inputs=[], outputs=[MC_output_3])

if __name__ == "__main__":
    webbrowser.open("http://127.0.0.1:7861")
    interface.launch(server_name='127.0.0.1', server_port=7861)
