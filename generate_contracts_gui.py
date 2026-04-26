#!/usr/bin/env python3
"""
Windows 桌面版合同生成器。
"""
from __future__ import annotations

import threading
import traceback
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from generate_contracts import generate_contracts, list_excel_fields


class ContractGeneratorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("合同批量生成器")
        self.root.geometry("760x560")
        self.root.minsize(700, 520)

        self.excel_path = tk.StringVar()
        self.template_path = tk.StringVar()
        self.output_dir = tk.StringVar(
            value=str(Path.cwd() / "output_contracts")
        )
        self.name_field = tk.StringVar()
        self.status_text = tk.StringVar(value="请选择 Excel 和 Word 模板文件。")

        self._build_ui()

    def _build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        container = ttk.Frame(self.root, padding=18)
        container.grid(sticky="nsew")
        container.columnconfigure(1, weight=1)
        container.rowconfigure(4, weight=1)

        title = ttk.Label(
            container,
            text="合同批量生成器",
            font=("Microsoft YaHei UI", 18, "bold"),
        )
        title.grid(row=0, column=0, columnspan=3, sticky="w")

        subtitle = ttk.Label(
            container,
            text="选择 Excel 数据源和 Word 模板，批量生成可交付的合同文档。",
            foreground="#555555",
        )
        subtitle.grid(row=1, column=0, columnspan=3, sticky="w", pady=(4, 18))

        self._build_path_row(
            container,
            row=2,
            label="Excel 数据源",
            variable=self.excel_path,
            browse_command=self._choose_excel,
        )
        self._build_path_row(
            container,
            row=3,
            label="Word 模板",
            variable=self.template_path,
            browse_command=self._choose_template,
        )
        self._build_path_row(
            container,
            row=4,
            label="输出目录",
            variable=self.output_dir,
            browse_command=self._choose_output_dir,
        )

        form = ttk.LabelFrame(container, text="生成选项", padding=14)
        form.grid(row=5, column=0, columnspan=3, sticky="ew", pady=(16, 0))
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="文件名字段").grid(
            row=0, column=0, sticky="w", padx=(0, 10)
        )
        self.name_field_entry = ttk.Entry(form, textvariable=self.name_field)
        self.name_field_entry.grid(row=0, column=1, sticky="ew")
        ttk.Button(
            form, text="读取字段", command=self._load_fields
        ).grid(row=0, column=2, padx=(10, 0))

        helper = ttk.Label(
            form,
            text="例如输入“乙方名称”，生成的文件名会优先使用该列的值。",
            foreground="#666666",
        )
        helper.grid(row=1, column=0, columnspan=3, sticky="w", pady=(8, 0))

        fields_frame = ttk.LabelFrame(container, text="Excel 字段", padding=14)
        fields_frame.grid(
            row=6, column=0, columnspan=3, sticky="nsew", pady=(16, 0)
        )
        fields_frame.columnconfigure(0, weight=1)
        fields_frame.rowconfigure(0, weight=1)
        container.rowconfigure(6, weight=1)

        self.fields_text = tk.Text(
            fields_frame,
            height=8,
            wrap="word",
            state="disabled",
            font=("Consolas", 10),
        )
        self.fields_text.grid(row=0, column=0, sticky="nsew")

        fields_scroll = ttk.Scrollbar(
            fields_frame, orient="vertical", command=self.fields_text.yview
        )
        fields_scroll.grid(row=0, column=1, sticky="ns")
        self.fields_text.configure(yscrollcommand=fields_scroll.set)

        actions = ttk.Frame(container)
        actions.grid(row=7, column=0, columnspan=3, sticky="ew", pady=(16, 0))
        actions.columnconfigure(0, weight=1)

        self.progress = ttk.Progressbar(actions, mode="indeterminate")
        self.progress.grid(row=0, column=0, sticky="ew", padx=(0, 12))

        self.generate_button = ttk.Button(
            actions, text="开始生成", command=self._start_generation
        )
        self.generate_button.grid(row=0, column=1)

        status = ttk.Label(
            container,
            textvariable=self.status_text,
            foreground="#1f4b99",
        )
        status.grid(row=8, column=0, columnspan=3, sticky="w", pady=(12, 0))

    def _build_path_row(
        self,
        parent,
        row: int,
        label: str,
        variable: tk.StringVar,
        browse_command,
    ):
        ttk.Label(parent, text=label).grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=6
        )
        entry = ttk.Entry(parent, textvariable=variable)
        entry.grid(row=row, column=1, sticky="ew", pady=6)
        ttk.Button(parent, text="浏览", command=browse_command).grid(
            row=row, column=2, padx=(10, 0), pady=6
        )

    def _choose_excel(self):
        path = filedialog.askopenfilename(
            title="选择 Excel 数据源",
            filetypes=[
                ("Excel 文件", "*.xlsx *.xlsm *.xls"),
                ("所有文件", "*.*"),
            ],
        )
        if path:
            self.excel_path.set(path)
            if not self.output_dir.get().strip():
                self.output_dir.set(str(Path(path).with_name("output_contracts")))

    def _choose_template(self):
        path = filedialog.askopenfilename(
            title="选择 Word 模板",
            filetypes=[("Word 文件", "*.docx"), ("所有文件", "*.*")],
        )
        if path:
            self.template_path.set(path)

    def _choose_output_dir(self):
        path = filedialog.askdirectory(title="选择输出目录")
        if path:
            self.output_dir.set(path)

    def _set_fields_text(self, content: str):
        self.fields_text.configure(state="normal")
        self.fields_text.delete("1.0", tk.END)
        self.fields_text.insert("1.0", content)
        self.fields_text.configure(state="disabled")

    def _load_fields(self):
        excel = self.excel_path.get().strip()
        if not excel:
            messagebox.showwarning("缺少 Excel", "请先选择 Excel 数据源文件。")
            return

        try:
            fields, count = list_excel_fields(excel)
        except Exception as exc:
            messagebox.showerror("读取失败", str(exc))
            return

        if not fields:
            self._set_fields_text("Excel 中没有数据行。")
            self.status_text.set("Excel 中没有可生成的数据。")
            return

        content = "\n".join(f"{{{{ {field} }}}}" for field in fields)
        self._set_fields_text(
            f"共 {len(fields)} 个字段，共 {count} 条记录：\n\n{content}"
        )
        self.status_text.set("字段读取完成。")

    def _start_generation(self):
        excel = self.excel_path.get().strip()
        template = self.template_path.get().strip()
        output_dir = self.output_dir.get().strip()

        if not excel:
            messagebox.showwarning("缺少 Excel", "请先选择 Excel 数据源文件。")
            return
        if not template:
            messagebox.showwarning("缺少模板", "请先选择 Word 模板文件。")
            return
        if not output_dir:
            messagebox.showwarning("缺少输出目录", "请先选择输出目录。")
            return

        self.generate_button.configure(state="disabled")
        self.progress.start(10)
        self.status_text.set("正在生成合同，请稍候...")

        worker = threading.Thread(
            target=self._run_generation,
            args=(excel, template, output_dir, self.name_field.get().strip()),
            daemon=True,
        )
        worker.start()

    def _run_generation(
        self,
        excel: str,
        template: str,
        output_dir: str,
        name_field: str,
    ):
        try:
            result = generate_contracts(
                excel,
                template,
                output_dir=output_dir,
                name_field=name_field or None,
            )
            self.root.after(0, self._on_generation_success, result)
        except Exception as exc:
            detail = str(exc).strip() or traceback.format_exc(limit=1)
            self.root.after(0, self._on_generation_error, detail)

    def _on_generation_success(self, result: dict):
        self.progress.stop()
        self.generate_button.configure(state="normal")
        self.status_text.set(
            f"生成完成：成功 {result['success']} 份，失败 {result['failed']} 份。"
        )

        message = (
            f"共处理 {result['records']} 条记录。\n"
            f"成功生成：{result['success']} 份\n"
            f"失败：{result['failed']} 份\n"
            f"输出目录：{result['output_dir']}"
        )
        if result["errors"]:
            preview = "\n".join(result["errors"][:5])
            message += f"\n\n部分错误：\n{preview}"
            if len(result["errors"]) > 5:
                message += "\n..."

        messagebox.showinfo("生成完成", message)

    def _on_generation_error(self, detail: str):
        self.progress.stop()
        self.generate_button.configure(state="normal")
        self.status_text.set("生成失败，请检查输入文件。")
        messagebox.showerror("生成失败", detail)


def main():
    root = tk.Tk()
    style = ttk.Style()
    try:
        style.theme_use("vista")
    except tk.TclError:
        pass
    ContractGeneratorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
