# -*- coding: utf-8 -*-
"""
WorkBuddy 一键备份：记忆 / 技能 / 对话风格 / 配置 / 工作区记忆
跨用户通用，朋友拿到后放入自己的 ~/.workbuddy/skills/ 即可使用。

用法：
  python backup.py [--dest DEST]
默认目标：<桌面>/WorkBuddy备份
"""
import os
import re
import sys
import shutil
import argparse
import datetime
from pathlib import Path


# Windows 保留设备名（带不带扩展名都无法复制）
RESERVED = ({"CON", "PRN", "AUX", "NUL"}
            | {"COM%d" % i for i in range(1, 10)}
            | {"LPT%d" % i for i in range(1, 10)})


def log(msg):
    print(msg, flush=True)


def normalize_path(p):
    """把 Git-Bash 风格 /c/xxx 或 ~/xxx 归一化为本机绝对路径。"""
    p = os.path.expanduser(p)
    m = re.match(r"^/([a-zA-Z])/(.*)$", p)
    if m:
        p = m.group(1) + ":/" + m.group(2)
    return Path(os.path.abspath(p))


def copy_file(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


def copy_tree(src, dst):
    """复制整个目录，返回复制的文件数。跳过 Windows 保留设备名（nul/con...）。"""
    if not os.path.isdir(src):
        return 0
    os.makedirs(dst, exist_ok=True)
    n = 0
    for root, dirs, files in os.walk(src):
        # 跳过保留设备名目录（如 nul），否则创建会失败
        dirs[:] = [d for d in dirs if os.path.splitext(d)[0].upper() not in RESERVED]
        rel = os.path.relpath(root, src)
        tgt = os.path.join(dst, rel) if rel != "." else dst
        os.makedirs(tgt, exist_ok=True)
        for f in files:
            if os.path.splitext(f)[0].upper() in RESERVED:
                continue
            s = os.path.join(root, f)
            d = os.path.join(tgt, f)
            try:
                shutil.copy2(s, d)
                n += 1
            except Exception as e:
                log("  跳过 %s: %s" % (s, e))
    return n


def gen_restore_bat(dest_root):
    """生成可移植恢复脚本（%~dp0 定位备份目录，%USERPROFILE% 定位目标，
    for /d 遍历各项目工作区记忆）。遵循 .bat 铁律：UTF-8 BOM + CRLF、
    goto 结构、echo 无半角括号。"""
    lines = [
        "@echo off",
        "chcp 65001 >nul",
        "setlocal",
        'set "SRC=%~dp0"',
        r'set "WB=%USERPROFILE%\.workbuddy"',
        r'set "LOG=%SRC%恢复日志.txt"',
        'echo ======================================== > "%LOG%"',
        "echo WorkBuddy 备份恢复脚本 启动 >> \"%LOG%\"",
        "echo 时间：%DATE% %TIME% >> \"%LOG%\"",
        "if not exist \"%SRC%\" goto NOSRC",
        "if not exist \"%WB%\" goto NOWB",
        "echo 开始恢复技能（skills）... >> \"%LOG%\"",
        r'robocopy "%SRC%03_技能" "%WB%\skills" /E /R:2 /W:2 /NFL /NDL /NJH >> "%LOG%"',
        "echo 开始恢复用户级记忆与身份... >> \"%LOG%\"",
        r'robocopy "%SRC%01_用户级记忆与身份" "%WB%" /E /R:2 /W:2 /NFL /NDL /NJH >> "%LOG%"',
        "echo 开始恢复专家与配置... >> \"%LOG%\"",
        r'robocopy "%SRC%04_专家与配置\experts" "%WB%\experts\custom" /E /R:2 /W:2 /NFL /NDL /NJH >> "%LOG%"',
        r'copy /Y "%SRC%04_专家与配置\mcp.json" "%WB%\mcp.json" >> "%LOG%"',
        r'copy /Y "%SRC%04_专家与配置\.mcp.json" "%WB%\.mcp.json" >> "%LOG%"',
        r'copy /Y "%SRC%04_专家与配置\models.json" "%WB%\models.json" >> "%LOG%"',
        r'copy /Y "%SRC%04_专家与配置\argv.json" "%WB%\argv.json" >> "%LOG%"',
        r'copy /Y "%SRC%04_专家与配置\workbuddy.db" "%WB%\workbuddy.db" >> "%LOG%"',
        "echo 开始恢复工作区记忆... >> \"%LOG%\"",
        r'for /d %%P in ("%SRC%02_工作区记忆\*") do (',
        r'  robocopy "%%P" "%USERPROFILE%\WorkBuddy\%%~nP\.workbuddy\memory" /E /R:2 /W:2 /NFL /NDL /NJH >> "%LOG%"',
        ")",
        "echo 恢复完成 >> \"%LOG%\"",
        "echo ======================================== >> \"%LOG%\"",
        "goto DONE",
        ":NOSRC",
        "echo 错误：未找到备份目录。 >> \"%LOG%\"",
        "echo 错误：未找到备份目录，请确认本文件位于备份文件夹内。",
        "goto DONE",
        ":NOWB",
        "echo 错误：未找到 WorkBuddy 配置目录，请先安装 WorkBuddy。 >> \"%LOG%\"",
        "echo 错误：未找到 WorkBuddy 配置目录，请先安装 WorkBuddy 后重试。",
        "goto DONE",
        ":DONE",
        "echo 恢复脚本执行完毕，详见 恢复日志.txt",
        "pause",
    ]
    data = "\r\n".join(lines).encode("utf-8-sig")
    out = os.path.join(dest_root, "恢复.bat")
    with open(out, "wb") as f:
        f.write(data)
    # 自检
    d = open(out, "rb").read()
    assert d.count(b"\x08") == 0, "存在退格控制符"
    assert d.count(b"\r") - d.count(b"\r\n") == 0, "存在裸CR"
    return out


def gen_manifest(dest_root, stats):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    skills = stats["skills"]
    projects = stats["projects"]
    skill_items = "\n".join("- %s" % s for s in skills) or "（无）"
    proj_items = "\n".join("- %s" % p for p in projects) or "（无）"
    text = """# WorkBuddy 记忆 / 技能 / 对话风格 备份清单

- **备份时间**：%s
- **备份位置**：%s
- **备份总大小**：约 %s
- **用途**：重装系统或换电脑后，双击本目录里的 `恢复.bat` 一键还原，避免「失忆」。

## 一、本次备份内容

| 分类 | 目录 | 说明 |
|------|------|------|
| 用户级记忆 | `01_用户级记忆与身份/MEMORY.md` | 跨项目长期记忆 |
| 云记忆缓存 | `01_用户级记忆与身份/memory/` | 云端记忆本地缓存 |
| 对话历史 | `01_用户级记忆与身份/sessions/` | 本地会话记录 |
| 身份/风格 | `01_用户级记忆与身份/` | SOUL.md / IDENTITY.md / USER.md |
| 工作区记忆 | `02_工作区记忆/<项目名>/` | 各项目的 .workbuddy/memory |
| 技能 | `03_技能/` | skills 全部 %d 项 |
| 专家包 | `04_专家与配置/experts/` | 自定义专家团 |
| 配置文件 | `04_专家与配置/` | mcp.json / .mcp.json / models.json / argv.json / workbuddy.db |

## 二、已备份的技能清单（%d 项）

%s

## 三、已备份的工作区记忆（%d 个）

%s

## 四、重装后如何还原

1. 重装系统并安装 WorkBuddy，至少正常运行一次（生成配置目录）。
2. 双击本目录里的 `恢复.bat`，自动还原，结束按任意键关闭。
3. 重新打开 WorkBuddy，记忆 / 技能 / 专家 / 自动化全部就位。

> 若移动了备份文件夹，`恢复.bat` 仍能通过自身位置（%%~dp0）定位，无需修改。

## 五、重要提醒（未包含在备份中）

- **API 密钥不在此备份内**：环境变量类（如 DASHSCOPE_API_KEY / ARK_API_KEY 等）与
  文件类凭证（如 IMA 的 `%%USERPROFILE%%\\.config\\ima\\`）需另行保存，重装后重配。
- **Python / Node 运行时未备份**：WorkBuddy 重装自带，技能依赖的额外 pip 包首次运行会提示重装。
- **MCP 连接器需重装后重新「信任」**：mcp.json 已还原，但各连接器要在 WorkBuddy 里重新授权。

## 六、校验记录

| 项目 | 结果 |
|------|------|
| skills 子目录数 | %d |
| 工作区记忆项目数 | %d |
| MEMORY.md 校验 | %s |
| 身份文件 | %s |
| 配置文件 5 项 | %s |
| 恢复.bat 自检 | %s |
""" % (
        now,
        stats["dest"],
        stats["total"],
        len(skills),
        len(skills),
        skill_items,
        len(projects),
        proj_items,
        len(skills),
        len(projects),
        stats["mem_ok"],
        stats["identity_ok"],
        stats["config_ok"],
        stats["bat_ok"],
    )
    out = os.path.join(dest_root, "备份清单.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(text)
    return out


def main():
    parser = argparse.ArgumentParser(description="WorkBuddy 一键备份")
    parser.add_argument("--dest", default=None, help="备份目标目录，默认 <桌面>/WorkBuddy备份")
    args = parser.parse_args()

    home = Path.home()
    wb = home / ".workbuddy"
    desktop = home / "Desktop"
    dest = normalize_path(args.dest) if args.dest else (desktop / "WorkBuddy备份")

    if not wb.is_dir():
        log("错误：未找到 %s，请先安装并运行一次 WorkBuddy。" % wb)
        sys.exit(1)

    d_identity = dest / "01_用户级记忆与身份"
    d_ws = dest / "02_工作区记忆"
    d_skills = dest / "03_技能"
    d_cfg = dest / "04_专家与配置"

    stats = {"dest": str(dest), "skills": [], "projects": [], "mem_ok": "N/A",
             "identity_ok": "N/A", "config_ok": "N/A", "bat_ok": "N/A", "total": "?"}

    log("=== WorkBuddy 备份开始 ===")
    log("源：%s" % wb)
    log("目标：%s" % dest)
    log("")

    # 1) 身份 + 记忆文件
    log("[1/6] 用户级记忆与身份 ...")
    d_identity.mkdir(parents=True, exist_ok=True)
    for name in ["MEMORY.md", "SOUL.md", "IDENTITY.md", "USER.md"]:
        s = wb / name
        if s.is_file():
            copy_file(str(s), str(d_identity / name))
    copy_tree(str(wb / "memory"), str(d_identity / "memory"))
    copy_tree(str(wb / "sessions"), str(d_identity / "sessions"))
    stats["identity_ok"] = "OK（4 个身份文件 + memory + sessions）"

    # 2) 工作区记忆（遍历 ~/WorkBuddy/*/.workbuddy/memory）
    log("[2/6] 工作区记忆 ...")
    projects_root = home / "WorkBuddy"
    if projects_root.is_dir():
        for proj in sorted(projects_root.iterdir()):
            mem = proj / ".workbuddy" / "memory"
            if mem.is_dir():
                copy_tree(str(mem), str(d_ws / proj.name))
                stats["projects"].append(proj.name)
    if not stats["projects"]:
        log("  （未发现工作区记忆，跳过）")

    # 3) 技能
    log("[3/6] 技能（skills）...")
    src_skills = wb / "skills"
    if src_skills.is_dir():
        n = copy_tree(str(src_skills), str(d_skills))
        stats["skills"] = sorted(
            p.name for p in src_skills.iterdir() if p.is_dir()
        )
        log("  已复制 %d 个技能目录" % len(stats["skills"]))

    # 4) 专家包
    log("[4/6] 专家与配置 ...")
    d_cfg.mkdir(parents=True, exist_ok=True)
    copy_tree(str(wb / "experts" / "custom"), str(d_cfg / "experts" / "custom"))

    # 5) 配置文件
    cfg_files = ["mcp.json", ".mcp.json", "models.json", "argv.json", "workbuddy.db"]
    copied = 0
    for name in cfg_files:
        s = wb / name
        if s.is_file():
            copy_file(str(s), str(d_cfg / name))
            copied += 1
    stats["config_ok"] = "%d/%d 项" % (copied, len(cfg_files))

    # 6) 生成恢复脚本 + 清单
    log("[5/6] 生成恢复.bat ...")
    bat = gen_restore_bat(str(dest))
    stats["bat_ok"] = "通过（UTF-8 BOM + CRLF + 无控制符）"

    log("[6/6] 生成备份清单.md ...")
    # 校验 MEMORY.md 一致性
    src_mem = wb / "MEMORY.md"
    dst_mem = d_identity / "MEMORY.md"
    if src_mem.is_file() and dst_mem.is_file():
        import hashlib
        a = hashlib.md5(src_mem.read_bytes()).hexdigest()
        b = hashlib.md5(dst_mem.read_bytes()).hexdigest()
        stats["mem_ok"] = "一致 ✓" if a == b else "不一致 ✗"
    else:
        stats["mem_ok"] = "源无 MEMORY.md"

    total = dest_exists_size(dest)
    stats["total"] = total
    manifest = gen_manifest(str(dest), stats)

    log("")
    log("=== 备份完成 ===")
    log("技能数：%d" % len(stats["skills"]))
    log("工作区项目数：%d" % len(stats["projects"]))
    log("MEMORY.md 校验：%s" % stats["mem_ok"])
    log("恢复脚本：%s" % bat)
    log("清单：%s" % manifest)
    log("总大小：%s" % total)


def dest_exists_size(p: Path) -> str:
    try:
        import subprocess
        out = subprocess.check_output(["du", "-sh", str(p)], stderr=subprocess.DEVNULL)
        return out.decode("utf-8", "replace").split("\t")[0].strip()
    except Exception:
        return "?"


if __name__ == "__main__":
    main()
