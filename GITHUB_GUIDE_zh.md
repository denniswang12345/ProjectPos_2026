# GitHub 上传和提交指南

仓库已由你创建： https://github.com/denniswang12345/ProjectPos_2026

## 先在电脑上运行

解压 ProjectPos_2026.zip。在项目文件夹空白处右键，选择“在终端中打开”。如果没有 Python，安装 Python 3.10 或更新版本。运行：

```powershell
python --version
python pos.py --demo
python -m unittest discover -s tests -v
```

若 python 不可用而 py 可用，用 py 替换 python。演示不需要第三方依赖，不会修改你的正式数据库。正常交互用 `python pos.py`。

## 上传时保留个人开发分支

压缩包不包含隐藏的 .git 历史目录。下面的命令适用于“解压后的项目文件夹”，并假设远程仓库没有初始 README 提交。不要在其他项目文件夹执行。

先执行 `git --version`。如果没有 Git，可安装 Git for Windows，或使用 GitHub Desktop。下面以已安装 Git 的 PowerShell 为例。

```powershell
Start-Transcript -Path .\GIT_COMMAND_HISTORY.txt -Append
git init -b main
git config user.name "Wang Hao"
git config user.email "1551921411@qq.com"
git add README.md .gitignore
git commit -m "Initialize POS assignment project"
git switch -c feature/wanghao-pos
git add .
git commit -m "Add cash sale and original-receipt return implementation and submission artifacts"
python -m unittest discover -s tests -v
git switch main
git merge --no-ff feature/wanghao-pos -m "Merge POS implementation and assignment artifacts"
git remote add origin https://github.com/denniswang12345/ProjectPos_2026.git
git push -u origin main
git push -u origin feature/wanghao-pos
git log --all --graph --decorate --oneline
git log --all --format="%h %an <%ae> %ad %s" --date=iso
Stop-Transcript
```

第一次推送时 Git 可能打开 GitHub 登录窗口，按窗口提示登录授权即可。不要把密码或 Token 发到聊天里。若登录遇到错误，发错误文本即可。仓库地址含 .git 或不含 .git 均可以。

`GIT_COMMAND_HISTORY.txt` 是你实际执行的命令记录。完成后检查它只含与作业相关的信息，再单独提交：

```powershell
git switch feature/wanghao-pos
git add GIT_COMMAND_HISTORY.txt
git commit -m "Record actual local and remote Git command evidence"
git switch main
git merge --no-ff feature/wanghao-pos -m "Merge command evidence"
git push origin main
git push origin feature/wanghao-pos
```

不要删除 feature/wanghao-pos 分支。不要编造组员或补造之前几天的提交。你可以在录制时展示 GitHub 页面上的 main 和个人分支，以及上述实际日志。

## 如果已有 README 或出现拒绝推送

先运行 `git ls-remote origin` 查看远端是否已有提交；网络不通时它也可能失败。若出现 non-fast-forward、unrelated histories 或其他错误，不要使用强制推送，保留错误信息后再处理。更直观的办法是用 GitHub Desktop 克隆现有仓库，将项目文件复制进去，创建个人分支，提交、推送，再通过 Pull Request 合并并保留分支。

## 上传完成后检查

1. 刷新仓库网页，应能看到 pos.py、tests、docs、submission 和 README。
2. 分支选择器应包含 main 与 feature/wanghao-pos。
3. 下载或克隆后再次运行演示与测试。
4. 报告中的 GitHub URL 已填好；视频链接尚需录制上传后补入。
5. 将真实 Git 命令记录及网页截图补入报告的 Git evidence 部分，重新导出 PDF。

当前工作环境访问 GitHub 曾超时，因此交付时不把本地完成写成远程上传成功。LOCAL_GIT_HISTORY.txt（如有）仅证明本地实际提交，不能替代你完成的 GitHub 推送记录。

官方说明：
https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github
