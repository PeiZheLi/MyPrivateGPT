# PrivateGPT

这个项目主要基于Gradio进行开发，参考借鉴了[gpt_academic](https://github.com/binary-husky/gpt_academic)项目，完成了一个及其轻量化的私人Chat助手。
大模型的调用主要基于api的方式调用，同时支持调用本地的ollam模型。
目前的多模态功能仅支持图片的调用。
本项目结构清晰，逻辑明确，方便自定义，拒绝屎山！！！
## 安装
建议使用venv虚拟环境，这样，就可以在后续直接使用[run.bat](.\run.bat)进行运行
```shell
pip install -r requirements.txt
```
## 使用
在[model_config.py](.\model_config.py)当中配置你的api，不用的可以不填

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
同时，你还可以在下面自行添加配置你想使用的模型
```Python
model_dict = {
    "glm-4-plus": {"supplier": "zhipuai", "type": "llm"},
    "glm-4-long": {"supplier": "zhipuai", "type": "llm"},
    ...
}
```
此时就可以运行[index.py](.\index.py)，进入主界面了
![demo](.\docs\demo.png)
此时你就可以愉快的使用了！
## 补充说明
- 你可以选择对应的功能来实现相应的需求，如果你觉得我的功能不够好，你可以在[function_prompt.py](.\function_prompt.py)里面添加你自己的功能（本质上是提示词），相信聪明如你应该一看就会
- 你还可以再其它参数的隐藏选项卡里面更改top_p和temperature
- 在任何时候，如过你定义了右下角提示词（它具有最高优先级)，他将覆盖你选择的任何功能
## 高级设置
你可以在[model_chat.py](.\model_chat.py)里面添加调用其他平台大模型的函数
添加完成以后，你需要在[model_switch.py](.\model_switch.py)中注册你添加的函数
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
相信聪明如你应该一看就会