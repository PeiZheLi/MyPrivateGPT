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

model_dict = {
    "glm-4-plus": {"supplier": "zhipuai", "type": "llm"},
    "glm-4-long": {"supplier": "zhipuai", "type": "llm"},
    "glm-4v-plus": {"supplier": "zhipuai", "type": "mllm"},
    "qwen-max": {"supplier": "aliai", "type": "llm"},
    # "qwen-vl-max": {"supplier": "aliai", "type": "mllm"},
    "yi-large": {"supplier": "lingyiai", "type": "llm"},
    # "yi-vision": {"supplier": "lingyiai", "type": "mllm"},
    "moonshot-v1-8k": {"supplier": "kimiai", "type": "llm"},
    "qwq-32b-preview": {"supplier": "aliai", "type": "llm"},
    # "llama3.3-70b-instruct": {"supplier": "aliai", "type": "llm"},
    # "llama3.2-90b-vision-instruct": {"supplier": "aliai", "type": "mllm"},
    "glm-4-flash": {"supplier": "zhipuai", "type": "llm"}, # 免费
    "glm-4v-flash": {"supplier": "zhipuai", "type": "mllm"}, # 免费
    "qwen2.5:3b": {"supplier": "ollama", "type": "llm"},
    "llama3.2:3b": {"supplier": "ollama", "type": "llm"},
}