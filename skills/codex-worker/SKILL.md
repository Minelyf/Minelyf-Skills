---
name: codex-worker
metadata:
  version: "0.1.0"
description: >
  当主 Agent 需要把代码编写、文件修改、命令执行、环境排障、构建测试或持续返工委派给完全访问模式下的 Codex CLI 时启用。
  主 Agent 负责高层架构、产品判断、视觉与交互审美、细节规范和最终验收，Codex 负责具体落地，同一任务的返工必须续接原会话。
---

# Codex 委派协作

## 角色分工

- **主 Agent** 负责整体设计、架构与产品取舍、视觉和交互把关，并将方向拆成可执行的细节约束，独立验收交付物。
- **Codex** 负责写代码、改文件、跑命令、构建测试和修 bug。它擅长执行，对全局取舍和审美的判断往往需要主 Agent 补足。派单时写清高层方向、关键细节、禁止事项和可验证的通过条件。
- 纯问答由主 Agent 直接处理。用户明确要求主 Agent 亲自设计细节时，由主 Agent 完成该部分。

## 运行模式与会话续接

本机需已安装并登录 Codex CLI。每次启动和续接都必须带 `--dangerously-bypass-approvals-and-sandbox`，非 Git 目录还必须带 `--skip-git-repo-check`。始终使用非交互的完全访问模式，禁止降级到半交互或受限沙箱模式。Brief 中的权限与操作范围以用户授权为准。

```text
codex exec --dangerously-bypass-approvals-and-sandbox [-C <dir>] [--skip-git-repo-check] "<brief>"
codex exec resume --dangerously-bypass-approvals-and-sandbox [--skip-git-repo-check] <SESSION_ID> "<返工反馈与明确改动要求>"
```

首次运行记录输出中的 `session id: <UUID>`。同一任务的返工、修 bug、追加需求或验收打回均须使用原 ID 执行 `resume`。并行时用不同任务名并显式传递对应的 ID，禁止用 `--last`。直接调用 CLI 续接时，先进入原工作目录。仅在切换到完全无关的新任务，或原上下文已彻底污染、必须推倒重来时，才新开会话。

## 五步工作流

1. 主 Agent 先调研需求、现有实现和约束，确定高层设计与取舍。
2. 按 [Brief 与返工模板](references/brief-template.md) 写派单说明，列出细节、红线、验收方法和通过条件。
3. 通过 [会话脚本](scripts/codex_session.py) 或 `codex exec` 启动或续接，跟进执行情况并向用户同步进展。
4. 主 Agent 独立看 diff、核对测试结果，涉及界面时检查实际截图，逐项对照验收标准。禁止仅凭 Codex 的口头汇报验收。
5. 有未通过项就将观察结果和具体改动要求发回原会话，复验到全部通过再交付。

## 会话脚本

脚本仅使用 Python 3 标准库。以下命令在 Skill 目录中执行，`--cwd` 和提示文件路径替换成实际值。

```bash
python3 scripts/codex_session.py start --task settings-screen --cwd /path/to/project --prompt-file /path/to/brief.md
python3 scripts/codex_session.py resume --task settings-screen --prompt-file /path/to/feedback.md
python3 scripts/codex_session.py list
python3 scripts/codex_session.py show --task settings-screen
python3 scripts/codex_session.py start --task build-check --dry-run --prompt "运行构建检查并报告结果"
```

脚本实时转发 CLI 输出，识别并保存会话 ID，同时记录工作目录和非 Git 目录选项，供续接时复用。也可用 `resume --session-id <UUID>` 指定已知会话。提示支持 `--prompt`、`--prompt-file` 或标准输入。

`--dry-run` 只打印命令，适用于 `start` 和 `resume`。`--state-file <path>` 可覆盖默认的 `${TMPDIR:-/tmp}/codex-worker-sessions.json`，状态文件只保留在本机。`clear --task <name>` 只移除本地任务映射，Codex 会话历史仍可通过原 ID 续接。
