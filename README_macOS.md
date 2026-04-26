# 合同批量生成器 macOS 版本

这是本项目的 macOS 桌面版交付说明。

## 构建产物

macOS 构建会生成：

- `合同批量生成器.app`
- `contract-generator-macos.zip`

其中 Release 和 Actions 下载时建议直接使用：

- `contract-generator-macos.zip`

## 本地打包

在 macOS 上执行：

```bash
python3 -m pip install -r requirements.txt pyinstaller
pyinstaller generate_contracts_macos.spec --noconfirm
ditto -c -k --sequesterRsrc --keepParent "dist/合同批量生成器.app" "dist/contract-generator-macos.zip"
```

## GitHub Actions

项目已提供 macOS 构建工作流：

```text
.github/workflows/build-macos.yml
```

会上传两个 Artifact：

- `contract-generator-macos-app`
- `contract-generator-macos-zip`

## GitHub Release

推送版本 tag 后，Release 工作流会额外附带：

- `contract-generator-macos.zip`

## 图标

如果你希望 macOS `.app` 使用专用图标，请在项目根目录放置：

```text
app.icns
```

如果没有该文件，构建仍可进行，只是不带专用 macOS 图标。
