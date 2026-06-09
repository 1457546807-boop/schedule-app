# 空余时间统计工具

上传课表截图 → AI 自动识别空闲节次 → 导出 CSV

## 项目结构

```
schedule-app/
├── app.py            # Flask 后端
├── requirements.txt  # 依赖
├── Procfile          # Render 启动命令
└── static/
    └── index.html    # 前端页面
```

## 本地运行（测试用）

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-你的key
python app.py
# 打开 http://localhost:5000
```

## 部署到 Render（免费，队友可直接访问）

1. 把这个文件夹推到 GitHub（新建一个仓库，把所有文件上传进去）

2. 去 https://render.com 注册账号（免费）

3. 点 "New +" → "Web Service" → 连接你的 GitHub 仓库

4. 填写配置：
   - Name: schedule-app（随意）
   - Environment: Python 3
   - Build Command: pip install -r requirements.txt
   - Start Command: gunicorn app:app
   - Instance Type: Free

5. 点 "Advanced" → "Add Environment Variable"
   - Key:   ANTHROPIC_API_KEY
   - Value: sk-ant-你的实际key

6. 点 Deploy → 等 2 分钟 → 得到一个 https://xxxx.onrender.com 链接

把链接发给队友，他们打开就能用，不需要填 API Key。
