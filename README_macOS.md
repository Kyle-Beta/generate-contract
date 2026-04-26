# 合同批量生成器 macOS 版本

这是本项目的 macOS 桌面版交付说明。

## 构建产物

macOS 构建现在会区分两种架构：

- Intel Mac: `contract-generator-macos-intel.zip`
- Apple Silicon Mac: `contract-generator-macos-apple-silicon.zip`

其中 Release 和 Actions 下载时建议直接使用对应 zip 包。

本地打包时仍会先生成：

- `合同批量生成器.app`

## 本地打包

在 macOS 上执行：

```bash
python3 -m pip install -r requirements.txt pyinstaller
pyinstaller generate_contracts_macos.spec --noconfirm
ditto -c -k --sequesterRsrc --keepParent "dist/合同批量生成器.app" "dist/contract-generator-macos-intel.zip"
```

如果要指定 Intel 架构：

```bash
MACOS_TARGET_ARCH=x86_64 pyinstaller generate_contracts_macos.spec --noconfirm
```

如果要指定 Apple Silicon 架构：

```bash
MACOS_TARGET_ARCH=arm64 pyinstaller generate_contracts_macos.spec --noconfirm
```

## GitHub Actions

项目已提供 macOS 构建工作流：

```text
.github/workflows/build-macos.yml
```

会上传两个 Artifact：

- `contract-generator-macos-app-x64`
- `contract-generator-macos-zip-x64`
- `contract-generator-macos-app-arm64`
- `contract-generator-macos-zip-arm64`

## GitHub Release

推送版本 tag 后，Release 工作流会额外附带：

- `contract-generator-macos-intel.zip`
- `contract-generator-macos-apple-silicon.zip`

## 图标

macOS 构建会自动使用项目根目录的：

```text
app.ico
```

工作流会在构建前自动把 `app.ico` 转成临时 `app.icns`，不需要再单独维护一份 macOS 图标文件。
