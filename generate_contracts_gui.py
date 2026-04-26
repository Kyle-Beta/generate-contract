#!/usr/bin/env python3
"""
Windows/macOS 桌面版合同生成器。
"""
from __future__ import annotations

import os
import subprocess
import sys
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
        self.root.geometry("920x700")
        self.root.minsize(820, 620)

        self.excel_path = tk.StringVar()
        self.template_path = tk.StringVar()
        self.output_dir = tk.StringVar(value=str(Path.cwd() / "output_contracts"))
        self.name_field = tk.StringVar(value="")
        self.status_text = tk.StringVar(value="请选择 Excel 和 Word 模板文件。")
        self.record_count_text = tk.StringVar(value="未读取")
        self.field_count_text = tk.StringVar(value="未读取")
        self.template_name_text = tk.StringVar(value="未选择")
        self.output_name_text = tk.StringVar(value=str(Path.cwd() / "output_contracts"))
        self.progress_value = tk.IntVar(value=0)

        self.fields: list[str] = []
        self.is_generating = False

        self._build_ui()
        self._bind_events()
        self._refresh_overview()

    def _build_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        container = ttk.Frame(self.root, padding=18)
        container.grid(sticky="nsew")
        container.columnconfigure(0, weight=1)
        container.rowconfigure(3, weight=1)

        header = ttk.Frame(container)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(0, weight=1)

        ttk.Label(
            header,
            text="合同批量生成器",
            font=("Microsoft YaHei UI", 20, "bold"),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="自动识别字段，实时查看生成进度，适合批量回归测试和正式交付。",
            foreground="#666666",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        overview = ttk.Frame(container)
        overview.grid(row=1, column=0, sticky="ew", pady=(16, 0))
        for i in range(3):
            overview.columnconfigure(i, weight=1)

        self._build_overview_card(
            overview, 0, "Excel 数据", self.record_count_text, self.field_count_text
        )
        self._build_overview_card(
            overview, 1, "模板状态", self.template_name_text, None
        )
        self._build_overview_card(
            overview, 2, "输出目录", self.output_name_text, None
        )

        config = ttk.LabelFrame(container, text="输入与配置", padding=14)
        config.grid(row=2, column=0, sticky="ew", pady=(16, 0))
        config.columnconfigure(1, weight=1)

        self._build_path_row(
            config, 0, "Excel 数据源", self.excel_path, self._choose_excel
        )
        self._build_path_row(
            config, 1, "Word 模板", self.template_path, self._choose_template
        )
        self._build_path_row(
            config, 2, "输出目录", self.output_dir, self._choose_output_dir
        )

        ttk.Label(config, text="文件名字段").grid(
            row=3, column=0, sticky="w", padx=(0, 10), pady=(12, 6)
        )
        self.name_field_combo = ttk.Combobox(
            config,
            textvariable=self.name_field,
            state="normal",
            values=[],
        )
        self.name_field_combo.grid(row=3, column=1, sticky="ew", pady=(12, 6))

        quick_actions = ttk.Frame(config)
        quick_actions.grid(row=3, column=2, sticky="e", pady=(12, 6))
        ttk.Button(
            quick_actions, text="读取字段", command=self._load_fields
        ).grid(row=0, column=0)
        ttk.Button(
            quick_actions, text="打开输出目录", command=self._open_output_dir
        ).grid(row=0, column=1, padx=(8, 0))

        ttk.Label(
            config,
            text="命名字段可留空；读取 Excel 后会自动填充可选字段。",
            foreground="#666666",
        ).grid(row=4, column=0, columnspan=3, sticky="w", pady=(4, 0))

        main_pane = ttk.Panedwindow(container, orient="horizontal")
        main_pane.grid(row=3, column=0, sticky="nsew", pady=(16, 0))

        fields_frame = ttk.LabelFrame(main_pane, text="Excel 字段预览", padding=12)
        log_frame = ttk.LabelFrame(main_pane, text="生成日志", padding=12)
        main_pane.add(fields_frame, weight=1)
        main_pane.add(log_frame, weight=2)

        fields_frame.columnconfigure(0, weight=1)
        fields_frame.rowconfigure(0, weight=1)
        self.fields_text = tk.Text(
            fields_frame,
            height=16,
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

        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        self.log_text = tk.Text(
            log_frame,
            height=16,
            wrap="word",
            state="disabled",
            font=("Consolas", 10),
        )
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_scroll = ttk.Scrollbar(
            log_frame, orient="vertical", command=self.log_text.yview
        )
        log_scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.configure(yscrollcommand=log_scroll.set)

        footer = ttk.Frame(container)
        footer.grid(row=4, column=0, sticky="ew", pady=(16, 0))
        footer.columnconfigure(0, weight=1)

        self.progress = ttk.Progressbar(
            footer,
            maximum=100,
            variable=self.progress_value,
            mode="determinate",
        )
        self.progress.grid(row=0, column=0, sticky="ew", padx=(0, 12))

        action_bar = ttk.Frame(footer)
        action_bar.grid(row=0, column=1, sticky="e")
        ttk.Button(
            action_bar, text="清空日志", command=self._clear_log
        ).grid(row=0, column=0)
        self.generate_button = ttk.Button(
            action_bar, text="开始生成", command=self._start_generation
        )
        self.generate_button.grid(row=0, column=1, padx=(8, 0))

        ttk.Label(
            container, textvariable=self.status_text, foreground="#1f4b99"
        ).grid(row=5, column=0, sticky="w", pady=(10, 0))

    def _build_overview_card(
        self,
        parent,
        column: int,
        title: str,
        primary_var: tk.StringVar,
        secondary_var: tk.StringVar | None,
    ):
        frame = ttk.LabelFrame(parent, text=title, padding=12)
        frame.grid(row=0, column=column, sticky="nsew", padx=(0, 12) if column < 2 else 0)
        ttk.Label(
            frame, textvariable=primary_var, font=("Microsoft YaHei UI", 13, "bold")
        ).grid(row=0, column=0, sticky="w")
        if secondary_var:
            ttk.Label(frame, textvariable=secondary_var, foreground="#666666").grid(
                row=1, column=0, sticky="w", pady=(6, 0)
            )

    def _build_path_row(self, parent, row, label, variable, browse_command):
        ttk.Label(parent, text=label).grid(
            row=row, column=0, sticky="w", padx=(0, 10), pady=6
        )
        entry = ttk.Entry(parent, textvariable=variable)
        entry.grid(row=row, column=1, sticky="ew", pady=6)
        ttk.Button(parent, text="浏览", command=browse_command).grid(
            row=row, column=2, padx=(10, 0), pady=6
        )
        return entry

    def _bind_events(self):
        self.excel_path.trace_add("write", lambda *_: self._on_excel_changed())
        self.template_path.trace_add("write", lambda *_: self._refresh_overview())
        self.output_dir.trace_add("write", lambda *_: self._refresh_overview())

    def _refresh_overview(self):
        template = self.template_path.get().strip()
        output_dir = self.output_dir.get().strip()
        self.template_name_text.set(Path(template).name if template else "未选择")
        self.output_name_text.set(output_dir or "未设置")

    def _set_text_widget(self, widget: tk.Text, content: str):
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert("1.0", content)
        widget.configure(state="disabled")

    def _append_log(self, line: str):
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, line.rstrip() + "\n")
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")

    def _clear_log(self):
        self._set_text_widget(self.log_text, "")

    def _choose_excel(self):
        path = filedialog.askopenfilename(
            title="选择 Excel 数据源",
            filetypes=[("Excel 文件", "*.xlsx *.xlsm *.xls"), ("所有文件", "*.*")],
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

    def _on_excel_changed(self):
        self._refresh_overview()
        excel = self.excel_path.get().strip()
        if not excel:
            self.fields = []
            self.name_field_combo.configure(values=[])
            self.record_count_text.set("未读取")
            self.field_count_text.set("未读取")
            self._set_text_widget(self.fields_text, "")
            return

        if not Path(excel).exists():
            return

        self._load_fields(silent=True)

    def _load_fields(self, silent: bool = False):
        excel = self.excel_path.get().strip()
        if not excel:
            if not silent:
                messagebox.showwarning("缺少 Excel", "请先选择 Excel 数据源文件。")
            return

        try:
            fields, count = list_excel_fields(excel)
        except Exception as exc:
            self.record_count_text.set("读取失败")
            self.field_count_text.set("请检查文件")
            if not silent:
                messagebox.showerror("读取失败", str(exc))
            return

        self.fields = fields
        self.record_count_text.set(f"{count} 条记录")
        self.field_count_text.set(f"{len(fields)} 个字段")
        self.name_field_combo.configure(values=fields)

        if fields and self.name_field.get().strip() not in fields:
            preferred = "合同编号" if "合同编号" in fields else fields[0]
            self.name_field.set(preferred)

        if not fields:
            self._set_text_widget(self.fields_text, "Excel 中没有数据行。")
            self.status_text.set("Excel 中没有可生成的数据。")
            return

        content = "\n".join(f"{{{{ {field} }}}}" for field in fields)
        self._set_text_widget(
            self.fields_text,
            f"共 {len(fields)} 个字段，共 {count} 条记录：\n\n{content}",
        )
        self.status_text.set("字段读取完成，可直接开始生成。")
        if not silent:
            self._append_log(f"已读取 Excel：{count} 条记录，{len(fields)} 个字段。")

    def _open_output_dir(self):
        output_dir = self.output_dir.get().strip()
        if not output_dir:
            messagebox.showwarning("缺少目录", "请先设置输出目录。")
            return

        path = Path(output_dir)
        path.mkdir(parents=True, exist_ok=True)

        try:
            if os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.run(["open", str(path)], check=False)
            else:
                subprocess.run(["xdg-open", str(path)], check=False)
        except Exception as exc:
            messagebox.showerror("打开失败", str(exc))

    def _set_generating(self, generating: bool):
        self.is_generating = generating
        self.generate_button.configure(state="disabled" if generating else "normal")

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

        self._clear_log()
        self._append_log("开始生成合同。")
        self.progress.configure(mode="determinate", maximum=100)
        self.progress_value.set(0)
        self._set_generating(True)
        self.status_text.set("正在生成合同，请稍候...")

        worker = threading.Thread(
            target=self._run_generation,
            args=(excel, template, output_dir, self.name_field.get().strip()),
            daemon=True,
        )
        worker.start()

    def _handle_progress(self, event: dict):
        total = max(event["total"], 1)
        index = event["index"]
        self.progress.configure(maximum=total)

        if event["stage"] == "processing":
            self.progress_value.set(index - 1)
            self.status_text.set(f"正在生成第 {index}/{total} 份合同...")
        elif event["stage"] == "success":
            self.progress_value.set(index)
            self._append_log(f"[{index:03d}/{total:03d}] 成功：{Path(event['output_path']).name}")
        elif event["stage"] == "error":
            self.progress_value.set(index)
            self._append_log(
                f"[{index:03d}/{total:03d}] 失败：{Path(event['output_path']).name} - {event['error']}"
            )

    def _run_generation(self, excel: str, template: str, output_dir: str, name_field: str):
        try:
            result = generate_contracts(
                excel,
                template,
                output_dir=output_dir,
                name_field=name_field or None,
                progress_callback=lambda event: self.root.after(
                    0, self._handle_progress, event
                ),
            )
            self.root.after(0, self._on_generation_success, result)
        except Exception as exc:
            detail = str(exc).strip() or traceback.format_exc(limit=1)
            self.root.after(0, self._on_generation_error, detail)

    def _on_generation_success(self, result: dict):
        self._set_generating(False)
        self.progress.configure(maximum=max(result["records"], 1))
        self.progress_value.set(result["records"])
        self.status_text.set(
            f"生成完成：成功 {result['success']} 份，失败 {result['failed']} 份。"
        )
        self._append_log(
            f"完成：成功 {result['success']} 份，失败 {result['failed']} 份。"
        )
        self._append_log(f"输出目录：{result['output_dir']}")

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
        self._set_generating(False)
        self.status_text.set("生成失败，请检查输入文件。")
        self._append_log(f"生成失败：{detail}")
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
