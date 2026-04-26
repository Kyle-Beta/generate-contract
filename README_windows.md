# 合同批量生成器

这是一个面向 Windows 的桌面应用，用于根据 Excel 数据源和 Word 模板批量生成合同文件。

## 使用方式

1. 双击打开 `合同批量生成器.exe`
2. 选择 Excel 数据源文件
3. 选择 Word 模板文件
4. 选择输出目录
5. 如需按某一列命名文件，在“文件名字段”中填写对应列名
6. 点击“读取字段”可查看 Excel 中可用占位符
7. 点击“开始生成”

## Excel 要求

- 第一行为字段名
- 第二行起每一行代表一份合同
- 支持 `.xlsx`、`.xlsm`、`.xls`

## Word 模板要求

- 模板格式必须为 `.docx`
- 占位符写法为 `{{字段名}}`
- 正文、表格、页眉、页脚中的占位符都会被替换

示例：

```text
甲方：{{甲方名称}}
乙方：{{乙方名称}}
签约日期：{{签约日期}}
```

## 文件命名规则

- 如果填写了“文件名字段”，会优先使用该列值作为输出文件名
- 如果未填写，则按 `合同_001.docx`、`合同_002.docx` 递增命名
- 如果出现重名，程序会自动追加后缀，避免覆盖已有文件

## 打包方式

在 Windows 上运行：

```bat
build_windows.bat
```

打包成功后会生成：

```text
dist\合同批量生成器.exe
```

如果你安装了 Inno Setup，也可以进一步生成安装包：

```bat
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
```

安装包输出为：

```text
dist\合同批量生成器_Setup.exe
```

## GitHub Actions 自动打包

如果项目放在 GitHub 仓库中，可以直接使用已提供的工作流：

```text
.github/workflows/build-windows.yml
```

macOS 对应工作流：

```text
.github/workflows/build-macos.yml
```

触发方式：

- 推送到 `main` 或 `master`
- 发起 Pull Request
- 在 GitHub Actions 页面手动点击运行

构建完成后，Actions 会上传两个 Artifact：

- `contract-generator-exe`
- `contract-generator-windows-package`
- `contract-generator-installer`

其中压缩包里默认包含：

- `合同批量生成器.exe`
- `README_windows.md`
- `sample_data.xlsx`
- `contract_template.docx`

安装版 Artifact 对应：

- `合同批量生成器_Setup.exe`

它会把程序安装到 `Program Files`，并可选创建桌面快捷方式。

## 自定义图标

如果你希望 `.exe` 带图标，只需要把一个 Windows 图标文件放到项目根目录，并命名为：

```text
app.ico
```

下次执行 `build_windows.bat` 时会自动带上该图标。

## 版本信息

Windows 可执行文件的版本信息来自项目根目录下的：

```text
version_info.txt
```

如果你要修改产品名、版本号、公司名，可以直接编辑这个文件后重新打包。

项目根目录还有一个统一版本文件：

```text
VERSION
```

建议发布新版本时同时更新：

- `VERSION`
- `version_info.txt`
- `installer.iss`

## GitHub Release 自动发布

项目已提供 Release 工作流：

```text
.github/workflows/release.yml
```

触发方式：

- 推送 tag，例如 `v1.1.0`
- 在 GitHub Actions 页面手动运行

执行后会自动创建 GitHub Release，并附带以下文件：

- `contract-generator.exe`
- `contract-generator-windows.zip`
- `contract-generator-setup.exe`
- `contract-generator-macos.zip`
