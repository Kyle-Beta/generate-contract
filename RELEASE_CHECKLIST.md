# 发布前检查清单

## 版本

- 确认 [VERSION](/Users/huangkai/Desktop/generate_contracts_tool/VERSION:1) 已更新
- 确认 [version_info.txt](/Users/huangkai/Desktop/generate_contracts_tool/version_info.txt:1) 中的 `FileVersion` 和 `ProductVersion` 已同步
- 确认 [installer.iss](/Users/huangkai/Desktop/generate_contracts_tool/installer.iss:1) 中的 `MyAppVersion` 已同步

## 应用资源

- 确认 [app.ico](/Users/huangkai/Desktop/generate_contracts_tool/app.ico:1) 为最终图标
- 确认示例文件 [sample_data.xlsx](/Users/huangkai/Desktop/generate_contracts_tool/sample_data.xlsx:1) 和 [contract_template.docx](/Users/huangkai/Desktop/generate_contracts_tool/contract_template.docx:1) 可正常打开
- 确认 [README_windows.md](/Users/huangkai/Desktop/generate_contracts_tool/README_windows.md:1) 中的说明仍然准确

## 功能验证

- 用示例 Excel 和模板实际生成一次合同
- 验证重复文件名时不会覆盖已有文件
- 验证选择 Excel 后能自动刷新“文件名字段”下拉内容
- 验证生成后的正文、表格、页眉、页脚都能替换

## 打包验证

- 在 Windows 上运行 [build_windows.bat](/Users/huangkai/Desktop/generate_contracts_tool/build_windows.bat:1)
- 确认生成 `dist\合同批量生成器.exe`
- 如需安装包，运行 `ISCC.exe installer.iss`
- 确认生成 `dist\合同批量生成器_Setup.exe`
- 双击安装版并验证桌面快捷方式、启动和卸载流程
- 在 macOS 上运行 `pyinstaller generate_contracts_macos.spec --noconfirm`
- 确认生成 `dist/合同批量生成器.app`
- 确认生成 `dist/contract-generator-macos.zip`

## 仓库检查

- 确认 [`.gitignore`](/Users/huangkai/Desktop/generate_contracts_tool/.gitignore:1) 已生效
- 不要提交 `build/`、`dist/`、`output_contracts/`、`myenv/`
- 不要提交 Office 临时文件，例如 `~$sample_data.xlsx`

## GitHub 发布

- 提交代码并推送到仓库默认分支
- 推送 tag，例如 `v1.1.11`
- 检查 GitHub Actions 中 `build-windows.yml` 和 `release.yml` 是否执行成功
- 检查 GitHub Release 页面是否附带以下文件：
- `contract-generator.exe`
- `contract-generator-windows.zip`
- `contract-generator-setup.exe`
- `contract-generator-macos.zip`
