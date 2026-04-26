# 首次发布操作顺序

## 1. 本地整理

在项目根目录确认这些文件已经是最终版本：

- [VERSION](/Users/huangkai/Desktop/generate_contracts_tool/VERSION:1)
- [version_info.txt](/Users/huangkai/Desktop/generate_contracts_tool/version_info.txt:1)
- [installer.iss](/Users/huangkai/Desktop/generate_contracts_tool/installer.iss:1)
- [app.ico](/Users/huangkai/Desktop/generate_contracts_tool/app.ico:1)
- [README_windows.md](/Users/huangkai/Desktop/generate_contracts_tool/README_windows.md:1)

建议先对照 [RELEASE_CHECKLIST.md](/Users/huangkai/Desktop/generate_contracts_tool/RELEASE_CHECKLIST.md:1) 过一遍。

## 2. 初始化 Git 仓库

如果当前目录还不是 Git 仓库，在项目根目录执行：

```bash
git init
git add .
git commit -m "Initial release prep"
```

如果已经是 Git 仓库，只需要正常提交：

```bash
git add .
git commit -m "Prepare Windows release"
```

## 3. 关联 GitHub 仓库

创建一个新的 GitHub 仓库后，在本地执行：

```bash
git remote add origin <你的仓库地址>
git branch -M main
git push -u origin main
```

示例：

```bash
git remote add origin https://github.com/yourname/generate-contracts-tool.git
git branch -M main
git push -u origin main
```

## 4. 触发 Windows 自动构建

代码推送到 `main` 后，GitHub Actions 会自动运行：

- [build-windows.yml](/Users/huangkai/Desktop/generate_contracts_tool/.github/workflows/build-windows.yml:1)

检查 Actions 页面，确认它成功生成：

- `contract-generator-exe`
- `contract-generator-windows-package`
- `contract-generator-installer`

## 5. 发布正式版本

确认 [VERSION](/Users/huangkai/Desktop/generate_contracts_tool/VERSION:1) 中的版本号，例如：

```text
1.1.0
```

然后在本地打 tag 并推送：

```bash
git tag v1.1.0
git push origin v1.1.0
```

这会触发：

- [release.yml](/Users/huangkai/Desktop/generate_contracts_tool/.github/workflows/release.yml:1)

## 6. 检查 GitHub Release

Release 成功后，到 GitHub 仓库的 Releases 页面确认以下文件都已附带：

- `合同批量生成器.exe`
- `合同批量生成器_windows.zip`
- `合同批量生成器_Setup.exe`

## 7. 对外分发建议

给普通用户优先提供：

- `合同批量生成器_Setup.exe`

给不想安装的用户提供：

- `合同批量生成器.exe`

给需要示例文件的用户提供：

- `合同批量生成器_windows.zip`

## 8. 后续发版规则

每次发新版本时，建议按这个顺序操作：

1. 更新 `VERSION`
2. 更新 `version_info.txt`
3. 更新 `installer.iss`
4. 提交代码并推送 `main`
5. 创建新 tag，例如 `v1.1.1`
6. 等待 GitHub Release 自动完成
