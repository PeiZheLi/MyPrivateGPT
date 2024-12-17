from openai import OpenAI
from ollama import Client
from function_prompt import function_dict
from model_config import supplier_dict
import base64


def build_openai(input_text, model, model_supplier, model_type, input_function, self_prompt_text,
                 input_image, additional_text, input_top_p, input_temperature):
    # 构建api和url
    client = OpenAI(api_key=supplier_dict[model_supplier]["api"],
                    base_url=supplier_dict[model_supplier]["url"], )

    # 构建prompt
    prompt = function_dict[input_function]
    if self_prompt_text:
        prompt = self_prompt_text

    # 构建message
    if additional_text:
        input_text = f"\n附加信息\n{additional_text}\n" + input_text

    # 构建多模态message
    if model_type == "mllm":
        if input_image:
            img_path = input_image
            with open(img_path, 'rb') as img_file:
                img_base = base64.b64encode(img_file.read()).decode('utf-8')
            input_text = [{"type": "text", "text": input_text}, ]
            input_text.append({"type": "image_url", "image_url": {"url": img_base}})
            # 使用另外两个多模态模型就用这一行
            # input_text.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_base}"}})


    # 构建一次对话请求
    completion = client.chat.completions.create(model=model,
                                                messages=[{"role": "system", "content": prompt},
                                                          {"role": "user", "content": input_text}, ],
                                                top_p=input_top_p,
                                                temperature=input_temperature,
                                                stream=True, )
    for chunk in completion:
        yield chunk.choices[0].delta.content or ""


def build_ollama(input_text, model, model_supplier, model_type, input_function, self_prompt_text,
                 input_image, additional_text, input_top_p, input_temperature):
    # 构建api和url
    client = Client(host=supplier_dict[model_supplier]["host"],
                    headers=supplier_dict[model_supplier]["headers"], )

    # 构建prompt
    prompt = function_dict[input_function]
    if self_prompt_text:
        prompt = self_prompt_text

    # 构建message
    if additional_text:
        input_text = f"\n附加信息\n{additional_text}\n" + input_text

    # 构建一次对话请求
    completion = client.chat(model=model,
                             messages=[{"role": "system", "content": prompt},
                                       {"role": "user", "content": input_text}, ],
                             stream=True, )

    # 返回结果
    for chunk in completion:
        yield chunk.message.content or ""


if __name__ == "__main__":
    completion = build_openai(input_text="你好",
                              model="glm-4-plus",
                              model_supplier="zhipuai",
                              model_type="llm",
                              input_function="None",
                              self_prompt_text=None,
                              input_image=None,
                              additional_text=None,
                              input_top_p=0.7,
                              input_temperature=0.9, )
    for chunk in completion:
        print(chunk.choices[0].delta.content)
