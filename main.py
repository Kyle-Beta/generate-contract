#!/usr/bin/env python3
from __future__ import annotations

import datetime
import os
import subprocess
import sys
import traceback
import tkinter as tk
from tkinter import filedialog
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import flet as ft
from generate_contracts import generate_contracts, list_excel_fields


BG_COLOR = "#F5F7FB"
CARD_COLOR = "#FFFFFF"
PRIMARY = "#2563EB"
PRIMARY_HOVER = "#1D4ED8"
SUCCESS = "#16A34A"
ERROR = "#DC2626"
TEXT_PRIMARY = "#111827"
TEXT_SECONDARY = "#6B7280"
BORDER = "#E5E7EB"
INPUT_BG = "#F9FAFB"


@dataclass
class AppState:
    selected_excel_path: str = ""
    selected_template_path: str = ""
    output_dir: str = ""
    filename_field: str = "合同名称"
    filename_fields: list[str] = field(default_factory=lambda: ["合同名称"])
    is_generating: bool = False
    success_count: int = 0
    fail_count: int = 0
    total_count: int = 0
    progress_value: float = 0.0
    logs: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class UIRefs:
    badge_text: ft.Text | None = None
    badge_box: ft.Container | None = None
    excel_value: ft.Text | None = None
    template_value: ft.Text | None = None
    output_value: ft.Text | None = None
    field_dropdown: ft.Dropdown | None = None
    start_button: ft.FilledButton | None = None
    success_text: ft.Text | None = None
    fail_text: ft.Text | None = None
    total_text: ft.Text | None = None
    progress_bar: ft.ProgressBar | None = None
    progress_percent: ft.Text | None = None
    progress_status: ft.Text | None = None
    logs_list: ft.Column | None = None
    logs_empty: ft.Text | None = None
    window_width_text: ft.Text | None = None


@dataclass
class AppContext:
    page: ft.Page
    state: AppState = field(default_factory=AppState)
    refs: UIRefs = field(default_factory=UIRefs)
    excel_picker: ft.FilePicker | None = None
    template_picker: ft.FilePicker | None = None
    output_picker: ft.FilePicker | None = None


ctx: AppContext | None = None


def _get_ctx() -> AppContext:
    if ctx is None:
        raise RuntimeError("Context is not initialized.")
    return ctx


def _is_macos() -> bool:
    return sys.platform == "darwin"


def _is_windows() -> bool:
    return os.name == "nt"


def _align_center():
    align_mod = getattr(ft, "alignment", None)
    if align_mod is not None and hasattr(align_mod, "center"):
        return align_mod.center
    alignment_cls = getattr(ft, "Alignment", None)
    if alignment_cls is not None:
        return alignment_cls(0, 0)
    return None


def _align_center_right():
    align_mod = getattr(ft, "alignment", None)
    if align_mod is not None and hasattr(align_mod, "center_right"):
        return align_mod.center_right
    alignment_cls = getattr(ft, "Alignment", None)
    if alignment_cls is not None:
        return alignment_cls(1, 0)
    return None


def _display_name(path_value: str, placeholder: str) -> str:
    if not path_value:
        return placeholder
    path = Path(path_value)
    return path.name or path_value


def _append_log(status: str, file_name: str, message: str):
    c = _get_ctx()
    c.state.logs.append({"status": status, "file_name": file_name, "message": message})


def _app_log_dir() -> Path:
    if _is_windows():
        base = Path(os.environ.get("LOCALAPPDATA") or Path.home())
    elif _is_macos():
        base = Path.home() / "Library" / "Logs"
    else:
        base = Path.home() / ".local" / "state"
    path = base / "contract_generator"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_error_log(action: str, exc: Exception, context: dict[str, Any] | None = None) -> Path:
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    log_path = _app_log_dir() / f"error_{action}_{ts}.log"
    tb = traceback.format_exc()
    lines = [
        f"time: {datetime.datetime.now().isoformat()}",
        f"action: {action}",
        f"platform: {sys.platform}",
        f"exception: {type(exc).__name__}: {exc}",
        f"context: {context or {}}",
        "",
        "traceback:",
        tb,
    ]
    log_path.write_text("\n".join(lines), encoding="utf-8")
    return log_path


def _pick_file_macos(prompt: str) -> str:
    script = [
        "try",
        f'return POSIX path of (choose file with prompt "{prompt}")',
        "on error number -128",
        'return ""',
        "end try",
    ]
    result = subprocess.run(
        ["osascript"] + sum([["-e", line] for line in script], []),
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def _pick_folder_macos(prompt: str) -> str:
    script = [
        "try",
        f'return POSIX path of (choose folder with prompt "{prompt}")',
        "on error number -128",
        'return ""',
        "end try",
    ]
    result = subprocess.run(
        ["osascript"] + sum([["-e", line] for line in script], []),
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip()


def _pick_file_windows(prompt: str, filetypes: list[tuple[str, str]]) -> str:
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        return filedialog.askopenfilename(title=prompt, filetypes=filetypes) or ""
    finally:
        root.destroy()


def _pick_folder_windows(prompt: str) -> str:
    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        return filedialog.askdirectory(title=prompt) or ""
    finally:
        root.destroy()


def _header_badge_info() -> tuple[str, str]:
    c = _get_ctx()
    s = c.state
    if s.is_generating:
        return "生成中", "#DBEAFE"
    if s.total_count > 0 and (s.success_count + s.fail_count) == s.total_count:
        return "已完成", "#DCFCE7"
    return "待生成", "#EEF2FF"


def _refresh_ui():
    c = _get_ctx()
    s = c.state
    r = c.refs

    if r.excel_value:
        val = _display_name(s.selected_excel_path, "请选择 Excel 文件")
        r.excel_value.value = val
        r.excel_value.color = TEXT_PRIMARY if s.selected_excel_path else TEXT_SECONDARY
    if r.template_value:
        val = _display_name(s.selected_template_path, "请选择 Word 模板")
        r.template_value.value = val
        r.template_value.color = TEXT_PRIMARY if s.selected_template_path else TEXT_SECONDARY
    if r.output_value:
        val = _display_name(s.output_dir, "请选择输出目录")
        r.output_value.value = val
        r.output_value.color = TEXT_PRIMARY if s.output_dir else TEXT_SECONDARY

    if r.field_dropdown:
        r.field_dropdown.options = [ft.dropdown.Option(x) for x in s.filename_fields]
        if s.filename_field not in s.filename_fields and s.filename_fields:
            s.filename_field = s.filename_fields[0]
        r.field_dropdown.value = s.filename_field
        r.field_dropdown.disabled = s.is_generating
    if r.start_button:
        r.start_button.text = "生成中..." if s.is_generating else "开始生成"
        r.start_button.disabled = s.is_generating

    if r.success_text:
        r.success_text.value = str(s.success_count)
    if r.fail_text:
        r.fail_text.value = str(s.fail_count)
    if r.total_text:
        r.total_text.value = str(s.total_count)

    if r.progress_bar:
        r.progress_bar.value = s.progress_value
    if r.progress_percent:
        r.progress_percent.value = f"{int(s.progress_value * 100)}%"
    if r.progress_status:
        r.progress_status.value = f"完成：成功 {s.success_count} 份，失败 {s.fail_count} 份"
        r.progress_status.color = SUCCESS if s.fail_count == 0 and s.total_count > 0 else TEXT_SECONDARY

    if r.logs_list:
        r.logs_list.controls = [build_log_item(item) for item in s.logs]
    if r.logs_empty:
        r.logs_empty.visible = len(s.logs) == 0

    badge_label, badge_bg = _header_badge_info()
    if r.badge_text:
        r.badge_text.value = badge_label
    if r.badge_box:
        r.badge_box.bgcolor = badge_bg

    c.page.update()


def _card(content: ft.Control, expand: bool = False) -> ft.Container:
    return ft.Container(
        content=content,
        bgcolor=CARD_COLOR,
        border=ft.border.all(1, BORDER),
        border_radius=16,
        padding=20,
        expand=expand,
    )


def _section_title(title: str, subtitle: str | None = None, icon: ft.IconData | None = None):
    children: list[ft.Control] = []
    if icon is not None:
        children.append(
            ft.Container(
                width=28,
                height=28,
                border_radius=8,
                bgcolor="#E0ECFF",
                alignment=_align_center(),
                content=ft.Icon(icon, size=16, color=PRIMARY),
            )
        )
    children.append(
        ft.Column(
            [
                ft.Text(title, size=16, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                ft.Text(subtitle or "", size=12, color=TEXT_SECONDARY, visible=bool(subtitle)),
            ],
            spacing=1,
            expand=True,
        )
    )
    return ft.Row(children, spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)


def _on_excel_picked(e: ft.FilePickerResultEvent):
    if e.files:
        c = _get_ctx()
        c.state.selected_excel_path = e.files[0].path
        _load_fields_from_excel(c.state.selected_excel_path)
        _refresh_ui()


def _on_template_picked(e: ft.FilePickerResultEvent):
    if e.files:
        c = _get_ctx()
        c.state.selected_template_path = e.files[0].path
        _refresh_ui()


def _on_output_picked(e: ft.FilePickerResultEvent):
    if e.path:
        c = _get_ctx()
        c.state.output_dir = e.path
        _refresh_ui()


def pick_excel(e=None):
    c = _get_ctx()
    if _is_macos():
        path = _pick_file_macos("选择 Excel 数据源")
        if path:
            if Path(path).suffix.lower() not in {".xlsx", ".xlsm", ".xls"}:
                _append_log("error", Path(path).name, "文件类型不支持，请选择 Excel 文件")
                _refresh_ui()
                return
            c.state.selected_excel_path = path
            _load_fields_from_excel(c.state.selected_excel_path)
            _refresh_ui()
            return
    if _is_windows():
        path = _pick_file_windows(
            "选择 Excel 数据源",
            [("Excel 文件", "*.xlsx *.xlsm *.xls"), ("所有文件", "*.*")],
        )
        if path:
            if Path(path).suffix.lower() not in {".xlsx", ".xlsm", ".xls"}:
                _append_log("error", Path(path).name, "文件类型不支持，请选择 Excel 文件")
                _refresh_ui()
                return
            c.state.selected_excel_path = path
            _load_fields_from_excel(c.state.selected_excel_path)
            _refresh_ui()
            return
    if c.excel_picker:
        c.excel_picker.pick_files(
            dialog_title="选择 Excel 数据源",
            allow_multiple=False,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["xlsx", "xlsm", "xls"],
        )


def pick_template(e=None):
    c = _get_ctx()
    if _is_macos():
        path = _pick_file_macos("选择 Word 模板")
        if path:
            if Path(path).suffix.lower() != ".docx":
                _append_log("error", Path(path).name, "模板文件必须是 .docx")
                _refresh_ui()
                return
            c.state.selected_template_path = path
            _refresh_ui()
            return
    if _is_windows():
        path = _pick_file_windows("选择 Word 模板", [("Word 文档", "*.docx"), ("所有文件", "*.*")])
        if path:
            if Path(path).suffix.lower() != ".docx":
                _append_log("error", Path(path).name, "模板文件必须是 .docx")
                _refresh_ui()
                return
            c.state.selected_template_path = path
            _refresh_ui()
            return
    if c.template_picker:
        c.template_picker.pick_files(
            dialog_title="选择 Word 模板",
            allow_multiple=False,
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["docx"],
        )


def pick_output_dir(e=None):
    c = _get_ctx()
    if _is_macos():
        path = _pick_folder_macos("选择输出目录")
        if path:
            c.state.output_dir = path
            _refresh_ui()
            return
    if _is_windows():
        path = _pick_folder_windows("选择输出目录")
        if path:
            c.state.output_dir = path
            _refresh_ui()
            return
    if c.output_picker:
        c.output_picker.get_directory_path(dialog_title="选择输出目录")


def _on_field_change(e: ft.ControlEvent):
    c = _get_ctx()
    c.state.filename_field = e.control.value or "合同名称"
    _refresh_ui()


def _load_fields_from_excel(excel_path: str) -> None:
    c = _get_ctx()
    try:
        fields, record_count = list_excel_fields(excel_path)
        c.state.filename_fields = fields if fields else ["合同名称"]
        if c.state.filename_field not in c.state.filename_fields:
            c.state.filename_field = c.state.filename_fields[0]
        _append_log("success", Path(excel_path).name, f"已读取字段 {len(c.state.filename_fields)} 个，记录 {record_count} 条")
    except Exception as exc:
        c.state.filename_fields = ["合同名称"]
        c.state.filename_field = "合同名称"
        log_file = _write_error_log("load_fields", exc, {"excel_path": excel_path})
        _append_log("error", Path(excel_path).name, f"读取字段失败：{exc}（日志：{log_file.name}）")


async def start_generate(e=None):
    c = _get_ctx()
    s = c.state
    if s.is_generating:
        return

    if not s.selected_excel_path or not s.selected_template_path or not s.output_dir:
        _append_log("error", "参数检查", "请先选择 Excel、Word 模板和输出目录")
        _refresh_ui()
        return

    excel_path = Path(s.selected_excel_path)
    template_path = Path(s.selected_template_path)
    if not excel_path.exists():
        _append_log("error", "参数检查", f"Excel 文件不存在：{excel_path}")
        _refresh_ui()
        return
    if not template_path.exists():
        _append_log("error", "参数检查", f"模板文件不存在：{template_path}")
        _refresh_ui()
        return

    out_dir = _resolve_output_dir(s.output_dir)
    s.output_dir = str(out_dir)

    s.is_generating = True
    s.success_count = 0
    s.fail_count = 0
    s.total_count = 0
    s.progress_value = 0
    s.logs = []
    _refresh_ui()

    try:
        name_field = s.filename_field if s.filename_field in s.filename_fields else None
        result = generate_contracts(
            excel_path=str(excel_path),
            template_path=str(template_path),
            output_dir=str(out_dir),
            name_field=name_field,
        )

        s.total_count = int(result.get("records", 0))
        s.success_count = int(result.get("success", 0))
        s.fail_count = int(result.get("failed", 0))
        s.progress_value = 1.0 if s.total_count > 0 else 0.0

        for file_path in result.get("generated_files", []):
            _append_log("success", Path(file_path).name, "生成成功")
        for error in result.get("errors", []):
            _append_log("error", "生成失败", str(error))
    except Exception as exc:
        s.fail_count += 1
        s.progress_value = 0
        log_file = _write_error_log(
            "generate",
            exc,
            {
                "excel_path": s.selected_excel_path,
                "template_path": s.selected_template_path,
                "output_dir": s.output_dir,
                "filename_field": s.filename_field,
            },
        )
        _append_log("error", "生成失败", f"{exc}（日志：{log_file.name}）")
    finally:
        s.is_generating = False
        _refresh_ui()


def clear_logs(e=None):
    c = _get_ctx()
    s = c.state
    s.logs = []
    s.success_count = 0
    s.fail_count = 0
    s.total_count = 0
    s.progress_value = 0
    _refresh_ui()


def _resolve_output_dir(path_value: str) -> Path:
    path = Path(path_value).expanduser()
    if not path.is_absolute():
        path = (Path.cwd() / path).resolve()
    else:
        path = path.resolve()
    return path


def open_output_dir(e=None):
    c = _get_ctx()
    out = c.state.output_dir.strip()
    if not out:
        _append_log("error", "输出目录", "请先选择输出目录")
        _refresh_ui()
        return
    try:
        out_path = _resolve_output_dir(out)
        out_path.mkdir(parents=True, exist_ok=True)
        if _is_macos():
            result = subprocess.run(
                ["open", str(out_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise RuntimeError((result.stderr or result.stdout or f"exit {result.returncode}").strip())
        elif _is_windows():
            os.startfile(str(out_path))  # type: ignore[attr-defined]
        else:
            result = subprocess.run(
                ["xdg-open", str(out_path)],
                check=False,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise RuntimeError((result.stderr or result.stdout or f"exit {result.returncode}").strip())
        _append_log("success", out_path.name, f"已打开目录：{out_path}")
        _refresh_ui()
    except Exception as exc:
        log_file = _write_error_log("open_output_dir", exc, {"output_dir": out})
        _append_log("error", "输出目录", f"打开失败：{exc}（日志：{log_file.name}）")
        _refresh_ui()


def build_file_selector(label, value, placeholder, on_click):
    c = _get_ctx()
    value_text = ft.Text(
        _display_name(value, placeholder),
        size=14,
        color=TEXT_PRIMARY if value else TEXT_SECONDARY,
        no_wrap=False,
        max_lines=2,
        overflow=ft.TextOverflow.VISIBLE,
    )
    if label == "Excel 数据源":
        c.refs.excel_value = value_text
    elif label == "Word 模板":
        c.refs.template_value = value_text
    else:
        c.refs.output_value = value_text

    return ft.Container(
        height=68,
        bgcolor=INPUT_BG,
        border=ft.border.all(1, BORDER),
        border_radius=14,
        padding=ft.padding.symmetric(horizontal=14),
        content=ft.Row(
            [
                ft.Column(
                    [
                        ft.Text(label, size=12, color=TEXT_SECONDARY),
                        value_text,
                    ],
                    spacing=2,
                    expand=True,
                    alignment=ft.MainAxisAlignment.CENTER,
                ),
                ft.OutlinedButton(
                    "选择",
                    on_click=on_click,
                    height=36,
                    width=86,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def build_header(page):
    c = _get_ctx()
    c.refs.badge_text = ft.Text("待生成", size=12, weight=ft.FontWeight.W_600, color=PRIMARY)
    c.refs.badge_box = ft.Container(
        content=c.refs.badge_text,
        bgcolor="#EEF2FF",
        border_radius=999,
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
    )

    return ft.Row(
        [
            ft.Container(
                width=42,
                height=42,
                border_radius=12,
                bgcolor="#DBEAFE",
                alignment=_align_center(),
                content=ft.Icon(ft.Icons.DESCRIPTION_OUTLINED, color=PRIMARY, size=24),
            ),
            ft.Column(
                [
                    ft.Text("合同批量生成器", size=22, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY),
                    ft.Text("根据 Excel 数据源和 Word 模板批量生成合同文件", size=12, color=TEXT_SECONDARY),
                ],
                spacing=2,
                expand=True,
            ),
            c.refs.badge_box,
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )


def build_config_card(page):
    c = _get_ctx()
    s = c.state
    c.refs.field_dropdown = ft.Dropdown(
        value=s.filename_field,
        options=[ft.dropdown.Option(x) for x in s.filename_fields],
        text_size=14,
        filled=True,
        fill_color=INPUT_BG,
        border_color=BORDER,
        border_radius=14,
        expand=True,
    )
    c.refs.field_dropdown.on_change = _on_field_change
    c.refs.start_button = ft.FilledButton(
        "开始生成",
        on_click=start_generate,
        height=48,
        width=132,
        style=ft.ButtonStyle(
            bgcolor=PRIMARY,
            color="#FFFFFF",
            shape=ft.RoundedRectangleBorder(radius=14),
            overlay_color=PRIMARY_HOVER,
        ),
    )

    content = ft.Column(
        [
            _section_title("生成配置", "选择文件后会自动更新字段列表", ft.Icons.TUNE_OUTLINED),
            build_file_selector("Excel 数据源", s.selected_excel_path, "请选择 Excel 文件", pick_excel),
            build_file_selector("Word 模板", s.selected_template_path, "请选择 Word 模板", pick_template),
            build_file_selector("输出目录", s.output_dir, "请选择输出目录", pick_output_dir),
            ft.Container(
                height=52,
                content=ft.Container(content=c.refs.field_dropdown, expand=True),
            ),
            ft.Container(height=8),
            ft.Row(
                [
                    ft.TextButton(
                        "打开输出目录",
                        on_click=open_output_dir,
                        style=ft.ButtonStyle(color=PRIMARY),
                    ),
                    c.refs.start_button,
                ],
                alignment=ft.MainAxisAlignment.END,
                vertical_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            ),
        ],
        spacing=14,
    )
    return _card(content)


def build_stat_item(label, value, color, icon):
    value_control = value if isinstance(value, ft.Text) else ft.Text(str(value), size=20, weight=ft.FontWeight.BOLD, color=color)
    return ft.Container(
        bgcolor="#F8FAFC",
        border=ft.border.all(1, BORDER),
        border_radius=14,
        padding=12,
        content=ft.Column(
            [
                ft.Row([ft.Icon(icon, color=color, size=16), ft.Text(label, size=12, color=TEXT_SECONDARY)], spacing=6),
                value_control,
            ],
            spacing=6,
        ),
        expand=True,
    )


def build_stats_card():
    c = _get_ctx()
    c.refs.success_text = ft.Text("0", size=20, weight=ft.FontWeight.BOLD, color=SUCCESS)
    c.refs.fail_text = ft.Text("0", size=20, weight=ft.FontWeight.BOLD, color=ERROR)
    c.refs.total_text = ft.Text("0", size=20, weight=ft.FontWeight.BOLD, color=PRIMARY)

    return _card(
        ft.Column(
            [
                _section_title("生成统计", "结果会在生成结束后自动刷新", ft.Icons.ANALYTICS_OUTLINED),
                ft.Row(
                    [
                        build_stat_item("成功", c.refs.success_text, SUCCESS, ft.Icons.CHECK_CIRCLE_OUTLINE),
                        build_stat_item("失败", c.refs.fail_text, ERROR, ft.Icons.ERROR_OUTLINE),
                        build_stat_item("总数", c.refs.total_text, PRIMARY, ft.Icons.SUMMARIZE_OUTLINED),
                    ],
                    spacing=10,
                ),
            ],
            spacing=12,
        )
    )


def build_progress_card():
    c = _get_ctx()
    c.refs.progress_bar = ft.ProgressBar(value=0, bgcolor="#E5E7EB", color=PRIMARY, bar_height=8)
    c.refs.progress_percent = ft.Text("0%", size=14, weight=ft.FontWeight.BOLD, color=TEXT_PRIMARY)
    c.refs.progress_status = ft.Text("完成：成功 0 份，失败 0 份", size=12, color=TEXT_SECONDARY)

    return _card(
        ft.Column(
            [
                _section_title("生成进度", "生成状态和百分比", ft.Icons.DOWNLOAD_DONE_OUTLINED),
                c.refs.progress_bar,
                ft.Row([c.refs.progress_percent, ft.Container(expand=True), c.refs.progress_status]),
            ],
            spacing=12,
        )
    )


def build_log_item(log):
    status = log.get("status", "info")
    icon = ft.Icons.CHECK_CIRCLE if status == "success" else ft.Icons.ERROR
    icon_color = SUCCESS if status == "success" else ERROR
    return ft.Container(
        height=44,
        expand=True,
        bgcolor="#F8FAFC",
        border_radius=12,
        padding=ft.padding.symmetric(horizontal=12, vertical=8),
        content=ft.Row(
            [
                ft.Icon(icon, size=16, color=icon_color),
                ft.Text(log.get("file_name", "-"), size=14, color=TEXT_PRIMARY, expand=True, no_wrap=True),
                ft.Text(log.get("message", ""), size=12, color=TEXT_SECONDARY, no_wrap=True),
            ],
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        ),
    )


def build_logs_card():
    c = _get_ctx()
    c.refs.logs_empty = ft.Text("暂无生成记录", size=12, color=TEXT_SECONDARY)
    c.refs.logs_list = ft.ListView(spacing=8, expand=True, auto_scroll=False)
    return _card(
        ft.Column(
            [
                _section_title("输出日志", "按条目查看生成结果", ft.Icons.LIST_ALT_OUTLINED),
                ft.Container(
                    expand=True,
                    bgcolor=INPUT_BG,
                    border=ft.border.all(1, BORDER),
                    border_radius=14,
                    padding=12,
                    content=ft.Stack([c.refs.logs_empty, c.refs.logs_list], expand=True),
                ),
            ],
            spacing=12,
            expand=True,
        ),
        expand=True,
    )


def main(page: ft.Page):
    global ctx
    ctx = AppContext(page=page)
    c = _get_ctx()
    c.state.output_dir = str(Path.cwd() / "output_contracts")

    min_w = 480
    min_h = 560

    page.title = "合同批量生成器"
    page.bgcolor = BG_COLOR
    page.padding = 24
    page.scroll = ft.ScrollMode.AUTO
    page.window.width = 480
    page.window.height = 800
    page.window.min_width = min_w
    page.window.min_height = min_h
    page.window.resizable = True
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window.bgcolor = BG_COLOR
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(primary=PRIMARY),
        text_theme=ft.TextTheme(body_medium=ft.TextStyle(size=14, color=TEXT_PRIMARY)),
    )

    c.refs.window_width_text = ft.Text(
        f"窗口：{int(page.window.width or 0)} x {int(page.window.height or 0)} px",
        size=12,
        color=TEXT_SECONDARY,
    )

    def on_window_resize(e):
        if c.refs.window_width_text:
            width = getattr(e, "width", None) or page.window.width or 0
            height = getattr(e, "height", None) or page.window.height or 0
            c.refs.window_width_text.value = f"窗口：{int(width)} x {int(height)} px"
            c.refs.window_width_text.update()

    page.on_resized = on_window_resize

    if not _is_windows():
        c.excel_picker = ft.FilePicker()
        c.excel_picker.on_result = _on_excel_picked
        c.template_picker = ft.FilePicker()
        c.template_picker.on_result = _on_template_picked
        c.output_picker = ft.FilePicker()
        c.output_picker.on_result = _on_output_picked
        page.overlay.extend([c.excel_picker, c.template_picker, c.output_picker])

    left = ft.Container(build_config_card(page), col={"xs": 12, "md": 4})
    right = ft.Container(
        ft.Column([build_stats_card(), build_progress_card(), build_logs_card()], spacing=16, expand=True),
        col={"xs": 12, "md": 8},
        expand=True,
    )

    page.add(
        ft.Column(
            [
                build_header(page),
                ft.Container(height=16),
                ft.ResponsiveRow([left, right], spacing=16, run_spacing=16),
                ft.Container(
                    content=c.refs.window_width_text,
                    alignment=_align_center_right(),
                    padding=ft.padding.only(top=8),
                ),
            ],
            expand=True,
        )
    )

    _refresh_ui()


if __name__ == "__main__":
    ft.app(target=main, view=ft.AppView.FLET_APP)
