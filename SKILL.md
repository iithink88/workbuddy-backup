---
name: workbuddy-backup
version: 1.0.0
description: 一键备份 WorkBuddy 的「记忆 / 技能 / 对话风格 / 配置 / 工作区记忆」到指定目录，并生成可移植的一键恢复脚本。当用户说「备份 WorkBuddy」「重装前备份」「导出我的记忆和技能」「把记忆技能存一份」时使用。跨用户通用，朋友拿到技能文件夹放入自己的 ~/.workbuddy/skills/ 即可使用。
type: skill
---

# WorkBuddy 一键备份

把 WorkBuddy 的核心资产（记忆、技能、人设/对话风格、专家团、配置文件、各项目工作区记忆）
完整复制到一个备份目录，并生成 `恢复.bat`（重装后双击即还原）和 `备份清单.md`。

## 何时使用

- 用户要重装系统 / 换电脑，担心 WorkBuddy「失忆」
- 用户说「备份我的 WorkBuddy」「把记忆和技能存一份」「导出技能」
- 用户想把这套备份流程分享给朋友

## 备份范围（不含可重装的运行时）

| 目标子目录 | 内容 | 来源 |
|------|------|------|
| `01_用户级记忆与身份/` | `MEMORY.md` + `memory/`(云记忆缓存) + `sessions/`(对话历史) + `SOUL.md`/`IDENTITY.md`/`USER.md`(风格) | `~/.workbuddy/` |
| `02_工作区记忆/<项目名>/` | 各项目的 `.workbuddy/memory/` 全部日志 | `~/WorkBuddy/*/.workbuddy/memory/` |
| `03_技能/` | `skills/` 全部技能目录 | `~/.workbuddy/skills/` |
| `04_专家与配置/` | `experts/custom/` 专家团 + `mcp.json`/`.mcp.json`/`models.json`/`argv.json`/`workbuddy.db` | `~/.workbuddy/` |

> 不备份 `~/.workbuddy/binaries/`（Python/Node 运行时，WorkBuddy 重装自带）。
> API 密钥在环境变量或 `~/.config/` 内，**不在本备份中**，需另行保存（见清单提醒）。

## 执行步骤

1. **确认目标路径**：默认备份到 `<用户桌面>/WorkBuddy备份`。
   若用户指定了其他路径（如 `D:\2026\202607\WorkBuddy备份`），用 `--dest` 传入。
   若用户没说，直接问一句「备份到桌面默认位置，还是指定别的盘？」再继续。

2. **运行备份脚本**（务必用 WorkBuddy 托管的 Python，路径依赖少）：
   ```bash
   PY="C:/Users/lenovo/.workbuddy/binaries/python/versions/3.13.12/python.exe"
   # 朋友机器上路径类似：~/.workbuddy/binaries/python/versions/<版本>/python.exe
   "$PY" "<技能目录>/scripts/backup.py" [--dest <目标目录>]
   ```

3. **校验输出**：脚本结束会打印技能数、工作区项目数、MEMORY.md 校验（一致 ✓）、
   恢复脚本路径、清单路径、总大小。确认无报错即可。

4. **交付**：把生成的目标目录（含 `恢复.bat` 与 `备份清单.md`）告诉用户，
   并用 `present_files` 展示 `备份清单.md` 与 `恢复.bat`。

## 给朋友用的分发方式

- 把整个技能文件夹 `~/.workbuddy/skills/workbuddy-backup/` 复制给对方，
  对方放入自己的 `~/.workbuddy/skills/` 后，对 WorkBuddy 说「备份我的 WorkBuddy」即可。
- 已随备份生成 `恢复.bat` 用 `%~dp0` 定位备份目录、`%USERPROFILE%` 定位目标，
  跨用户名/跨盘符均可移动，无需修改。

## 注意事项

- 恢复.bat 遵循 Windows .bat 编写铁律（UTF-8 BOM + CRLF、goto 结构、无半角括号），
  双击不会闪退；若还原失败，看同目录 `恢复日志.txt`。
- 重装后恢复顺序：先装 WorkBuddy 并运行一次 → 双击 `恢复.bat`。
- MCP 连接器（IMA、腾讯文档等）还原后需在 WorkBuddy 里重新「信任/授权」。
