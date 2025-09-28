from typing import Any, Dict

# 供应商配置 - 包含API密钥和基础URL
supplier_dict: Dict[str, Dict[str, str]] = {
    "aliai": {
        "api": "<YOUR_API_KEY>",
        "url": "https://dashscope.aliyuncs.com/compatible-mode/v1"
    },
    "deepseek": {
        "api": "<YOUR_API_KEY>",
        "url": "https://api.deepseek.com/v1"
    },
    "kimiai": {
        "api": "<YOUR_API_KEY>",
        "url": "https://api.moonshot.cn/v1"
    },
    "zhipuai": {
        "api": "<YOUR_API_KEY>",
        "url": "https://open.bigmodel.cn/api/paas/v4"
    },

}

# 模型配置 - 映射模型名称到供应商
model_dict: Dict[str, Dict[str, Any]] = {
    "glm-4.5": {
        "supplier": "zhipuai",
        "max_tokens": 8192,
        "max_concurrent": 10,
    },
    "qwen3-max": {
        "supplier": "aliai",
        "max_tokens": 8192,
        "max_concurrent": 10,

    },
    "kimi-k2-0905-preview": {
        "supplier": "kimiai",
        "max_tokens": 8192,
        "max_concurrent": 10,

    },
    "deepseek-chat": {
        "supplier": "deepseek",
        "max_tokens": 4096,
        "max_concurrent": 100,
    },
    "deepseek-reasoner": {
        "supplier": "deepseek",
        "max_tokens": 8192,
        "max_concurrent": 100,
    },
}
