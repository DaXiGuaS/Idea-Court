# 想法法庭 / Idea Court

**你的想法，撑不过三分钟。**

一个 AI 分饰 5 个角色，从各自的角度围攻你的想法。你可以当场反驳，最后得到一份带票数的判决书。

---

## 它能做什么

两种模式：

| 模式 | 评审团 | 适合问 |
|---|---|---|
| **做产品** | 产品经理、后端工程师、测试、老板、真实用户 | 我想做一个 App / 工具 |
| **做个决定** | 精算师、风险官、情绪观察员、过来人、反方 | 我想买 XX、要不要跳槽、要不要报课 |

你可以反驳，票数会重新统计。有些想法会被翻盘，有些会被戳穿。

---

## 快速开始

### 1. 准备环境

需要 Python 3.10 以上。

```bash
python -m venv .venv
```

Windows：

```bash
.venv\Scripts\activate
```

macOS / Linux：

```bash
source .venv/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

如果下载很慢，可以临时用国内镜像：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. 配置 API Key

复制配置模板：

```bash
cp .env.example .env
```

打开 `.env`，填入你的 DeepSeek API Key：

```ini
DEEPSEEK_API_KEY=你的key
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-chat
LLM_TIMEOUT=60
```

> 模型名和接口地址以你实际使用的服务商为准。

### 4. 启动

```bash
uvicorn main:app --reload
```

Windows 用户也可以直接**双击项目根目录的 `run.bat`**，效果一样。

浏览器打开 <http://127.0.0.1:8000>

---

## 怎么玩

1. 选一个模式
2. 输入你的想法，或者点一个预置案例
3. 看 5 位评审逐条发言
4. 不服？在判决书下方写反驳，票数会重新统计
5. 点「生成分享卡」下载一张竖版判决书

---

## 技术栈

| 层 | 选型 |
|---|---|
| Web 服务 | FastAPI |
| 流程编排 | LangGraph |
| 大模型 | DeepSeek（OpenAI 兼容接口） |
| 输出约束 | Pydantic |
| 前端 | 原生 HTML / CSS / JS（无构建、无 npm） |

---

## 项目结构

```
.
├── main.py          # FastAPI 接口
├── graph.py         # LangGraph 编排 + 票数统计
├── reviewer.py      # LLM 调用（JSON mode + 重试）
├── prompts.py       # 评审角色设定
├── models.py        # 数据模型
├── config.py        # 配置读取
├── static/
│   └── index.html   # 前端
├── .env.example
└── requirements.txt
```

---

## 几个设计取舍

**为什么用 JSON mode，而不是 `with_structured_output`？**
DeepSeek 的 function calling 是否触发并不稳定，`response_format={"type": "json_object"}` 更可靠。拿到 JSON 后再用 Pydantic 校验。

**为什么票数由程序统计？**
大模型数数是弱项。它只负责发言和给出自己的投票，票数由 Python 累加。

**为什么温度设为 0.4？**
五个角色的语气差异靠提示词里写死的人设保证，不该靠高温度。温度太高会导致同样的输入投票来回跳。

**为什么每个角色只问一个维度？**
如果让每个角色自由发挥，五个人会说出同一句"这没意思"。把维度写死、并明确禁止越界，才能让评审真正分开。

---

## 已知限制

- 单机本地运行，没有用户系统，适合演示
- LLM 输出仍有随机性，同样的输入可能得到不同票数
- 每次评审调用一次大模型，通常需要 5–15 秒
