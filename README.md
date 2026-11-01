# Minelyf Skills

可复用的 Codex skills：把日常工作方法整理成可安装、可分享的工具。

## 飞书灵绘 · feishu-linghui

在飞书文档中创建或修改**原生可编辑画板**，适合数据信息图、流程、现状总结和规划。支持局部改字，并提供保留文档评论的操作指引。

### 安装

将本仓库的 `skills/feishu-linghui` 文件夹复制到你的 Codex skills 目录（默认 `~/.codex/skills/`）。不要同时启用功能相同的旧版 `feishu-board`，以免重复匹配。

### 使用

在 Codex 中输入：

> 使用 $feishu-linghui，把这段报告整理成飞书文档中的可编辑画板。

也可以要求修改已有画板中的文字或增加一行。提供目标文档或画板及授权使用的资料。

### 环境与示例

需要 Python 3、Node.js/npx，以及已登录并有目标文档编辑权限的 `lark-cli`。生成本地 SVG 不需要飞书账号；写入飞书需要登录和权限。转换工具会由 npx 按脚本中指定的版本范围下载。

在临时工作目录中运行 skill 的 `examples/data_brief.py`，即可生成 `diagram.svg`；再运行 `scripts/board.py render diagram.svg` 进行渲染和排版检查。示例的所有名称和数字均为虚构数据。

### 隐私

仓库仅保存通用指引、脚本和虚构示例。请勿提交登录凭据、画板 token、内部文档链接、真实业务数据和导出文件。飞书访问凭据由本机 CLI 管理。
