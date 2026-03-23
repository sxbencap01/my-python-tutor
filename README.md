---
license: apache-2.0
sdk: gradio
app_file: app.py
pinned: false
---

# AI 导师系统 (ModelScope 版)

这是一个部署在魔搭空间 (ModelScope Space) 的 AI 导师系统。

## 部署说明

1. **API Key 设置**: 
   - 在魔搭空间的“设置 (Settings)” -> “变量与机密 (Variables and Secrets)”中添加一个名为 `API_KEY` 的环境变量，值为您的硅基流动 API Key。
   - 可选：添加 `LLM_MODEL` 环境变量来更换模型（默认为 Qwen3-235B）。

2. **本地测试**:
   ```bash
   pip install -r requirements.txt
   python app.py
   ```

3. **魔搭部署**:
   - 将所有代码上传到魔搭仓库。
   - 魔搭会自动识别 `requirements.txt` 并安装依赖。
   - `app.py` 会在端口 7860 启动服务。

## 文件结构

- `app.py`: Flask 后端服务
- `templates/`: 前端界面
- `requirements.txt`: 依赖列表
- `llm_service.py`: LLM 调用接口
- `knowledge_manager.py`: 知识状态管理
- `code_analyzer.py`: 代码分析与执行
