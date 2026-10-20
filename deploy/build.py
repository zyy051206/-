# -*- coding: utf-8 -*-
"""把作品集整理成可直接部署到 Cloudflare Pages 的 public/ 目录。

用法：  python deploy/build.py
输出：  个人作品集/public/

会排除 .git、deploy、README.md 等不属于站点的内容。
public/ 是生成物，每次运行都会重建。
"""

import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEPLOY = os.path.join(ROOT, "deploy")
OUT = os.path.join(ROOT, "public")

SKIP_DIRS = {".git", ".github", "public", "deploy", "node_modules", "__pycache__", ".idea", ".vscode"}
SKIP_FILES = {"README.md", ".gitattributes", ".gitignore", ".DS_Store", "Thumbs.db"}

# 这些由 deploy/ 提供，需要覆盖到输出根目录
FROM_DEPLOY = ["_headers", "404.html"]


def ignore(directory, names):
    # README.md 只在项目根目录排除：reports/ 下的 README 是报告页面直接链接的附件。
    at_root = os.path.abspath(directory) == ROOT
    skip = set()
    for name in names:
        full = os.path.join(directory, name)
        if os.path.isdir(full):
            if name in SKIP_DIRS:
                skip.add(name)
        elif os.path.isfile(full):
            if name.startswith(".") or name in (".DS_Store", "Thumbs.db"):
                skip.add(name)
            elif at_root and name in SKIP_FILES:
                skip.add(name)
    return skip


def main():
    if os.path.exists(OUT):
        if not os.path.exists(os.path.join(OUT, "index.html")):
            sys.exit("public/ 已存在且不像生成物，先手动确认再删除：" + OUT)
        shutil.rmtree(OUT)
    os.makedirs(OUT)

    copied = 0
    for name in sorted(os.listdir(ROOT)):
        if name in SKIP_DIRS or name in SKIP_FILES or name.startswith("."):
            continue
        src = os.path.join(ROOT, name)
        dst = os.path.join(OUT, name)
        if os.path.isdir(src):
            shutil.copytree(src, dst, ignore=ignore)
            copied += sum(len(files) for _, _, files in os.walk(dst))
        else:
            shutil.copy2(src, dst)
            copied += 1

    for name in FROM_DEPLOY:
        src = os.path.join(DEPLOY, name)
        if os.path.exists(src):
            shutil.copy2(src, os.path.join(OUT, name))
            copied += 1
        else:
            print("警告：deploy/%s 不存在，已跳过" % name)

    total = sum(
        os.path.getsize(os.path.join(dp, f))
        for dp, _, fs in os.walk(OUT)
        for f in fs
    )
    print("输出目录 : %s" % OUT)
    print("文件数量 : %d" % copied)
    print("总大小   : %.1f MB" % (total / 1048576))
    print("入口检查 : %s" % ("index.html 存在" if os.path.exists(os.path.join(OUT, "index.html")) else "缺少 index.html"))


if __name__ == "__main__":
    main()