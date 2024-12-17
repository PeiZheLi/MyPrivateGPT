# PrivateGPT

This project is primarily developed based on Gradio, drawing inspiration from the [gpt_academic](https://github.com/binary-husky/gpt_academic) project, to create an extremely lightweight private Chat assistant. 
The invocation of large models is mainly done through API calls, and it also supports calling local Ollama models.
Currently, the multimodal functionality only supports image calls. The project structure is clear, the logic is straightforward, making it easy to customize and avoiding a mess!!!!

## Installation

It is recommended to use a venv virtual environment, and you can directly run [run.bat](.\run.bat) later.

```shell
pip install -r requirements.txt
```

## Usage

Configure your API in [model_config.py](.\model_config.py). You can leave unused fields blank.

```Python
supplier_dict = {
    "zhipuai": {"api": "",
                "url": "https://open.bigmodel.cn/api/paas/v4", },
    "aliai": {"api": "",
              "url": "https://dashscope.aliyuncs.com/compatible-mode/v1", },
    "lingyiai": {"api": "",
                 "url": "https://api.lingyiwanwu.com/v1", },
    "kimiai": {"api": "",
               "url": "https://api.moonshot.cn/v1", },
    "ollama": {"host": "http://localhost:11434",
               "headers": {'x-some-header': 'some-value'}, },
}
```

Additionally, you can add configurations for models you wish to use below.

```Python
model_dict = {
    "glm-4-plus": {"supplier": "zhipuai", "type": "llm"},
    "glm-4-long": {"supplier": "zhipuai", "type": "llm"},
    ...
}
```

Now you can run [index.py](.\index.py) to enter the main interface.

![demo](.\docs\demo.png)

You can now enjoy using it!

## Additional Notes

- You can choose the corresponding functions to meet your needs. If you think my functions are not good enough, you can add your own functions in [function_prompt.py](.\function_prompt.py) (essentially prompts). I'm sure you'll figure it out easily.
- You can also change the top_p and temperature in the hidden tabs of other parameters.
- At any time, if you define a prompt in the bottom right corner (which has the highest priority), it will override any function you choose.

## Advanced Settings

You can add functions to call large models from other platforms in [model_chat.py](.\model_chat.py). After adding them, you need to register your added functions in [model_switch.py](.\model_switch.py).

```Python
build_functions_dict = {
    "zhipuai": build_openai,
    "aliai": build_openai,
    "lingyiai": build_openai,
    "kimiai": build_openai,
    "ollama": build_ollama,
    ...
}
```

I'm sure you'll figure it out easily.