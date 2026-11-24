---
name: codex-worker
metadata:
  version: "0.2.0"
description: >
  当主 Agent 需要把重型代码编写、多文件改动、复杂排障、构建测试、部署或持续返工委派给完全访问模式下的 Codex CLI 时启用。
  采用快慢分层：轻量查询、1-3 条现成 CLI 命令闭环的操作与单文件小改由主 Agent 直接完成；主 Agent 负责高层架构、产品判断、视觉与交互审美和最终验收，Codex 负责重型执行落地，按复杂度分级推理档位，同一任务的返工必须续接原会话。
---

# Codex 委派协作

## 角色分工与快慢分层

避免事无巨细都派给 Codex 造成冷启动与深度推理耗时：

- **主 Agent 直接完成（不委派）**：
  - 纯问答、读代码、查状态、导日志与只读统计分析；
  - 1～3 条现成 CLI 命令即可闭环的轻量运维、配置修改与回读验证；
  - 单文件极小改动（约 ≤30 行的文档、配置、文案或一眼可定位的小修）；
  - 用户明确要求主 Agent 亲自完成的设计或细节编辑。
- **委派给 Codex 执行（重型落地）**：
  - 新功能实现、多文件代码改动、重构与复杂修 Bug；
  - 编写/补全单测、端到端/浏览器回归测试与环境排障；
  - 复杂批量数据处理脚本、长耗时任务、构建发布与多轮返工调优。
- **主 Agent 仍始终负责**：整体设计、架构与产品取舍、视觉和交互把关，以及独立验收交付物。

## 运行模式、分级推理与会话续接

本机需已安装并登录 Codex CLI。每次启动和续接都必须带 `--dangerously-bypass-approvals-and-sandbox`，非 Git 目录还必须带 `--skip-git-repo-check`。始终使用非交互的完全访问模式，禁止降级到半交互或受限沙箱模式。派单中的权限与操作范围以用户授权为准。

按任务复杂度显式指定推理档位，避免常规执行默认高档位拖慢：

- 常规编码、单测、构建部署：`-c model_reasoning_effort="medium"`（需要更稳妥时用 `"high"`）。
- 复杂架构重构、疑难根因排查、高风险并发/安全改动：`-c model_reasoning_effort="xhigh"`。

```text
codex exec -c model_reasoning_effort="medium" --dangerously-bypass-approvals-and-sandbox [-C <dir>] [--skip-git-repo-check] "<brief>"
codex exec resume -c model_reasoning_effort="medium" --dangerously-bypass-approvals-and-sandbox [--skip-git-repo-check] <SESSION_ID> "<返工反馈与明确改动要求>"
```

首次运行记录输出中的 `session id: <UUID>`。同一任务的返工、修 bug、追加需求或验收打回均须使用原 ID 执行 `resume`。并行时用不同任务名并显式传递对应的 ID，禁止用 `--last`。直接调用 CLI 续接时，先进入原工作目录。仅在切换到完全无关的新任务，或原上下文已彻底污染、必须推倒重来时，才新开会话。

## 五步工作流

1. 主 Agent 先调研需求、现有实现和约束，确定高层设计与取舍，并判断是否值得委派（轻量活直接自己完成）。
2. 按任务体量准备派单说明：大改动、架构/界面或多模块任务按 [Brief 与返工模板](references/brief-template.md) 写完整派单说明；中等改动或单次构建测试直接用精炼 prompt 写明改动点、红线与通过条件即可。
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
