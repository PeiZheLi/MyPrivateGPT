import gradio as gr
from model_config import model_dict
from model_switch import chat_llm
from function_prompt import function_dict


def respond(*args, **kwargs):
    response_generator = chat_llm(*args, **kwargs)
    output_text = ""
    for chunk in response_generator:
        output_text += chunk
        yield output_text


def clear():
    return "", ""


def init():
    return "", "", None, None, 0.7, 0.9


# 创建Gradio界面
with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column():
            gr.Markdown("# XXX的ChatGPT")
            input_text = gr.Textbox(label="问题", placeholder="请输入问题...", lines=10, show_copy_button=True)
            with gr.Row():
                text_button = gr.Button("提交")
                clear_button = gr.Button("清空")
                init_button = gr.Button("初始化")
            input_function = gr.Radio(list(function_dict.keys()), label="功能", value="None")
            with gr.Row():
                input_image = gr.Image(label="图片", type="filepath")
                additional_text = gr.Textbox(label="附加信息", placeholder="附加信息...", lines=10, value=None)
            input_model = gr.Dropdown(label="AI模型", choices=list(model_dict.keys()), value="glm-4-plus")
        with gr.Column():
            output_text = gr.Textbox(label="回复", placeholder="等待回复...", lines=30, show_copy_button=True)
            with gr.Accordion("其它参数", open=False):
                input_top_p = gr.Slider(0, 1, value=0.7, step=0.1, interactive=True, label="top_p", )
                input_temperature = gr.Slider(0, 1, value=0.9, step=0.1, interactive=True, label="temperature")
            self_prompt_text = gr.Textbox(label="提示词", placeholder="自定义提示词...", lines=5, value=None)

    inputs = [input_text, input_model, input_function, self_prompt_text, input_image, additional_text,
              input_top_p, input_temperature, ]
    outputs = [output_text, ]

    text_button.click(respond, inputs=inputs, outputs=outputs)
    clear_button.click(clear, inputs=[], outputs=[input_text, output_text])
    init_button.click(init, inputs=[], outputs=[input_text, output_text, input_image, additional_text,
                                                input_top_p, input_temperature, ])

demo.launch(server_name='127.0.0.1', server_port=7861)
