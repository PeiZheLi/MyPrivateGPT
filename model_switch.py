from model_chat import *
from model_config import model_dict

build_functions_dict = {
    "zhipuai": build_openai,
    "aliai": build_openai,
    "lingyiai": build_openai,
    "kimiai": build_openai,
    "ollama": build_ollama,
}


def chat_llm(input_text, input_model, input_function, self_prompt_text,
             input_image, additional_text,
             input_top_p, input_temperature):
    model_info = model_dict[input_model]
    model_supplier = model_info["supplier"]
    model_type = model_info["type"]

    completion = build_functions_dict[model_supplier](
        input_text, input_model, model_supplier, model_type, input_function,
        self_prompt_text, input_image, additional_text, input_top_p, input_temperature
    )

    for chunk in completion:
        yield chunk
