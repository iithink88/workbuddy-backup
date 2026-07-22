# WorkBuddy 一键备份技能（workbuddy-backup）

一个 WorkBuddy 技能：把你的 **记忆 / 技能 / 对话风格 / 专家团 / 配置文件 / 各项目工作区记忆** 一键完整备份到指定目录，并自动生成**可移植的一键恢复脚本 `恢复.bat`** 和 **备份清单 `备份清单.md`**。

重装系统或换电脑前，用它给自己留个「不会失忆」的底。

## 功能

- 📝 **用户级记忆**：`MEMORY.md` + 云记忆缓存 + 对话历史
- 🎭 **对话风格**：`SOUL.md` / `IDENTITY.md` / `USER.md`
- 🧩 **全部技能**：`~/.workbuddy/skills/` 下所有技能
- 🤖 **专家团与配置**：`experts/custom/` + `mcp.json` / `models.json` / `argv.json` / `workbuddy.db`（含自动化日程）
- 🗂️ **各项目工作区记忆**：`~/WorkBuddy/*/.workbuddy/memory/` 全部日志
- ♻️ **一键恢复**：生成的 `恢复.bat` 用 `%~dp0` 定位备份、`%USERPROFILE%` 定位目标，换电脑/换盘符都能用
- ✅ **自动校验**：脚本结束打印技能数、工作区项目数、`MEMORY.md` 一致性校验

> ⚠️ 不备份可重装的运行时（`~/.workbuddy/binaries/`）。  
> ⚠️ **API 密钥不在备份范围内**：它们存在于环境变量或 `~/.config/` 目录（如 IMA 凭证）。重装后需另行配回。

## 朋友怎么装这个技能（3 种方式）

### 方式 1：拖文件进聊天框（最简单）
把本仓库的 `SKILL.md` 直接拖进 WorkBuddy 聊天框，它会自动安装。

### 方式 2：放文件夹进技能目录（推荐，含脚本）
把整个 `workbuddy-backup` 文件夹放进你的技能目录：

```
C:\Users\<你的用户名>\.workbuddy\skills\workbuddy-backup\
```

（macOS / Linux 路径：`~/.workbuddy/skills/workbuddy-backup/`）

### 方式 3：命令行（如果你装了 npx）
```bash
npx skills add <owner>/<repo>@workbuddy-backup
```

## 怎么用

安装好后，在 WorkBuddy 里说一句话即可：

> 「备份我的 WorkBuddy」

默认备份到 `<桌面>/WorkBuddy备份`。也可以指定路径：

> 「把 WorkBuddy 备份到 D:\备份\WorkBuddy」

WorkBuddy 会用托管 Python 跑 `scripts/backup.py`，结束后生成：

```
WorkBuddy备份/
├── 01_用户级记忆与身份/   # 记忆 + 对话风格
├── 02_工作区记忆/          # 各项目记忆日志
├── 03_技能/                # 所有技能
├── 04_专家与配置/          # 专家团 + 配置
├── 备份清单.md             # 清单与恢复步骤
└── 恢复.bat                # 一键还原（重装后双击）
```

## 重装后如何恢复

1. 装好系统 → 安装 WorkBuddy → 至少正常运行一次（生成配置目录）
2. 双击 `WorkBuddy备份\恢复.bat`，自动还原，按任意键关闭
3. 重新打开 WorkBuddy，记忆 / 技能 / 专家 / 自动化全部就位
4. 在 WorkBuddy 的「连接器」页面，重新「信任 / 授权」IMA、腾讯文档等 MCP 服务
5. 把 `~/.config\` 等保存的 API 凭证放回原处（或重新配置环境变量）

## 实现说明

- 备份脚本 `scripts/backup.py` 已处理 Windows 路径坑：Git-Bash 风格 `/c/...` 自动归一化为 `C:\...`；自动跳过 Windows 保留设备名文件（如 `nul`），避免 `[WinError 87]` 复制失败。
- 恢复脚本严格按 Windows `.bat` 编写铁律生成（UTF-8 BOM + CRLF、goto 结构、无半角括号），双击不会闪退。

## License

MIT — 放心分享给朋友。
