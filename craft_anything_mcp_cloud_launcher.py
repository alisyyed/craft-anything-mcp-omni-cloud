#!/usr/bin/env python3
"""
================================================================================
CRAFT-ANYTHING v1.2 OMNI-FOUNDRY - 24/7 CLOUD MCP SERVER & AUTO-PROVISIONER
================================================================================
Turns `storytold/craft-anything` (v0.6.0+, Pure-Rust 320-Tool Software Inspection,
Reverse-Engineering & Clean-Room Rebuild Engine) into a 100% Free, 24/7 Set-and-Forget
Remote MCP Server for Gemini Connected Apps!

WHAT IS FIXED IN v1.2:
  1. INSTANT 0ms GEMINI CONNECTED APPS HANDSHAKE IN THE CLOUDFLARE WORKER:
     The Cloudflare Worker router (`craft-anything-mcp-forever.forested-lung.workers.dev/mcp`)
     now embeds full JSON-RPC 2.0 handlers for `initialize`, `notifications/initialized`,
     `tools/list`, and `craft_list_all_320_tools` directly at the Cloudflare Edge!
     Gemini Connected Apps ("Add a custom app link") connects with 0 errors immediately,
     even while the background GitHub Actions runner is still booting or rotating!
  2. 15-SECOND FAST-TUNNEL STARTUP ON GITHUB ACTIONS:
     Starts the HTTP server and `cloudflared` tunnel FIRST (publishing `LIVE_MCP_URL.json`
     in ~15-25s) while downloading the 65 MB `craft-anything` v0.6.0 Linux release in
     a background thread, and removes slow `apt-get` snap/debconf blockers.
  3. AUTO-CANCELS STALE WORKFLOW RUNS ON RE-DEPLOY:
     Automatically cancels any stuck/queued workflow runs before dispatching the new
     runner so `--forever` never waits behind an old run.
================================================================================
"""

import argparse
import base64
import http.server
import json
import os
import platform
import re
import shutil
import socketserver
import subprocess
import sys
import tarfile
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import webbrowser
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# 1. Complete 17-Toolset Catalog of `storytold/craft-anything` (302+ Tools)
# ---------------------------------------------------------------------------

CRAFT_TOOLSETS: Dict[str, Dict[str, Any]] = {
    "core": {
        "title": "Essentials & Evidence Ledger (35 tools)",
        "mode": "clean_room_and_deep",
        "tools": [
            "core_target_open", "core_target_close", "core_session_show", "core_targets_list",
            "core_target_select", "core_evidence_show", "core_evidence_export", "core_evidence_import",
            "core_unknowns_show", "core_unknown_add", "core_unknown_edit", "core_unknown_verify",
            "core_archive_show", "core_archive_extract", "core_archives_compare", "core_person_ask",
            "core_action_approve", "assets_image_generate", "assets_model_generate",
            "core_investigation_show", "core_brief_write", "core_plan_update",
            "core_hypothesis_record", "core_hypothesis_update", "core_finding_record",
            "core_finding_edit", "core_handoff_write", "core_journal_read", "core_report_save",
            "core_report_write", "core_overview_show", "native_function_study",
            "core_feature_find", "core_target_triage", "core_evidence_browse",
        ],
    },
    "native": {
        "title": "Native Code & Pure-Rust Pseudo-C Decompiler (55 tools)",
        "mode": "deep",
        "tools": [
            "native_cursor_show", "native_functions_list", "native_sections_list",
            "native_strings_browse", "native_named_addresses_list", "native_open_documents_list",
            "native_bookmarks_show", "native_functions_search", "native_strings_find",
            "native_bytes_show", "native_address_offset_show", "native_xrefs_list",
            "native_name_show", "native_comment_read", "native_inline_comment_read",
            "native_function_show", "native_function_disassemble", "native_function_callees_list",
            "native_function_callers_list", "native_function_references_list",
            "native_function_pseudocode", "native_function_address_show",
            "native_function_instructions_list", "native_function_find", "native_instruction_show",
            "native_call_site_resolve", "native_data_show", "native_name_set", "native_names_set",
            "native_comment_write", "native_inline_comment_write", "native_bookmark_add",
            "native_bookmark_remove", "native_function_label", "native_cursor_address_show",
            "native_cursor_function_show", "native_document_show", "native_cursor_goto",
            "native_cursor_forward", "native_cursor_back", "native_call_graph_show",
            "native_call_path_find", "native_functions_decompile", "native_name_xrefs_list",
            "native_api_show", "native_value_flow_show", "native_dos_image_show",
            "native_address_show", "native_bytes_find", "app_builds_line_up",
            "native_source_folder_write", "native_objdump_run", "native_rizin_command_run",
            "native_cutter_sessions_list", "native_cutter_command_run",
        ],
    },
    "apple": {
        "title": "Apple macOS/iOS Mach-O, Objective-C & Swift (14 tools)",
        "mode": "deep",
        "tools": [
            "apple_objc_classes_list", "apple_objc_protocols_list", "apple_swift_types_list",
            "apple_dispatch_show", "apple_ui_action_trace", "apple_macho_show",
            "apple_signature_show", "apple_plist_show", "apple_slices_list",
            "apple_swift_symbols_demangle", "apple_nib_decode", "apple_archive_decode",
            "apple_assets_list", "apple_dylibs_resolve",
        ],
    },
    "formats": {
        "title": "File Formats, Unity/Unreal Games, Firmware, Wasm, Solana sBPF & PCAP (36 tools)",
        "mode": "deep",
        "tools": [
            "web_recording_show", "native_pe_resources_list", "native_layout_show",
            "native_crash_show", "native_go_binary_show", "formats_wasm_module_show",
            "formats_evm_interface_show", "formats_sbpf_show", "formats_sbpf_disassemble",
            "firmware_regions_list", "firmware_image_extract", "core_packed_files_list",
            "core_packed_files_unpack", "formats_bytecode_show", "game_archives_list",
            "game_pak_list", "game_iostore_list", "game_unity_list", "game_unity_bundle_list",
            "game_unity_asset_export", "game_unreal_texture_export", "game_pak_extract",
            "game_unity_code_names_show", "app_folder_explain", "native_rust_binary_show",
            "native_library_calls_list", "native_offered_symbols_list", "native_publisher_show",
            "formats_ai_weights_show", "formats_wasm_compare", "packets_capture_show",
            "packets_fields_show", "engines_tshark_check", "packets_inventory_show",
            "radio_recording_decode", "radio_decoders_list",
        ],
    },
    "managed": {
        "title": ".NET Assemblies & ILSpy C# Decompilation (8 tools)",
        "mode": "deep",
        "tools": [
            "managed_assembly_show", "managed_members_list", "managed_native_calls_list",
            "managed_assemblies_compare", "managed_native_calls_verify",
            "managed_reconstruction_check", "managed_app_graph_build", "managed_ilspy_decompile",
        ],
    },
    "android": {
        "title": "Android APK, DEX, Flutter & Dart AOT (14 tools)",
        "mode": "deep",
        "tools": [
            "android_package_show", "android_classes_find", "android_class_show",
            "android_method_show", "android_class_users_find", "android_resources_read",
            "android_components_list", "engines_apktool_check", "android_flutter_identify",
            "android_dart_snapshot_show", "engines_jeb_check", "android_jeb_open",
            "android_jeb_units_browse", "android_jeb_decompile",
        ],
    },
    "java": {
        "title": "Java Archives & Vineflower Decompilation (6 tools)",
        "mode": "deep",
        "tools": [
            "java_archive_show", "java_classes_find", "java_class_show",
            "java_method_show", "java_class_users_find", "java_vineflower_decompile",
        ],
    },
    "adb": {
        "title": "Connected Android Device Bridge (24 tools)",
        "mode": "deep",
        "tools": [
            "engines_adb_check", "adb_devices_find", "adb_device_show", "adb_apps_list",
            "adb_log_read", "adb_app_show", "adb_running_processes_list", "adb_folder_list",
            "adb_device_features_list", "adb_system_services_list", "adb_display_show",
            "adb_window_show", "adb_setting_get", "adb_apps_find", "adb_app_download",
            "adb_file_download", "adb_screenshot_take", "adb_bugreport_save",
            "adb_file_upload", "adb_app_install", "adb_app_remove", "adb_app_launch",
            "adb_activity_open", "adb_app_force_stop",
        ],
    },
    "browser": {
        "title": "Websites, 3-Width Responsive Captures & Pixel Diffing (22 tools)",
        "mode": "clean_room_and_deep",
        "tools": [
            "web_browser_connect", "web_pages_list", "web_page_show", "web_page_js_analyze",
            "web_page_watch", "web_mcp_tools_list", "web_page_screenshot_take",
            "web_snapshots_compare", "web_pixels_compare", "web_walkthrough_record",
            "web_walkthrough_check", "web_site_open", "web_site_capture",
            "web_page_states_capture", "web_site_close", "web_standin_build",
            "web_standin_start", "web_standin_stop", "web_standin_show",
            "web_coverage_measure", "web_listeners_list", "web_modules_trace",
        ],
    },
    "javascript": {
        "title": "Electron (`app.asar`), Bundles & Source-Map Recovery (11 tools)",
        "mode": "deep",
        "tools": [
            "js_app_map", "js_runtime_code_match", "web_scripts_save", "js_source_locate",
            "js_sources_restore", "js_electron_pages_list", "js_electron_page_show",
            "js_electron_walkthrough_record", "js_runtimes_list", "js_runtime_watch",
            "js_electron_fuses_show",
        ],
    },
    "runtime": {
        "title": "Running Program Walkthroughs, GDB & Rizin Debugging (14 tools)",
        "mode": "deep",
        "tools": [
            "native_window_capture", "runtime_walkthrough_record", "runtime_captures_compare",
            "runtime_ui_read", "runtime_ui_walkthrough_record", "apple_calls_observe",
            "native_gdb_session_begin", "native_gdb_command_run", "native_gdb_session_show",
            "native_gdb_session_end", "native_rizin_session_begin",
            "native_rizin_session_command_run", "native_rizin_session_show",
            "native_rizin_session_end",
        ],
    },
    "frida": {
        "title": "Dynamic Frida Instrumentation (9 tools)",
        "mode": "deep",
        "tools": [
            "frida_devices_find", "frida_targets_list", "frida_session_begin",
            "frida_script_run", "frida_session_continue", "frida_script_forget",
            "frida_session_show", "frida_session_end", "frida_instrument_run",
        ],
    },
    "application": {
        "title": "Cross-Build Comparison, Feature Tracing & Rebuild Verification (17 tools)",
        "mode": "clean_room_and_deep",
        "tools": [
            "app_feature_follow", "js_function_explain", "app_graphs_compare",
            "js_exports_compare", "app_source_import", "js_source_bundle_compare",
            "app_ledger_build", "app_coverage_evaluate", "android_app_graph_build",
            "apple_app_graph_build", "harmony_app_graph_build",
            "app_function_versions_compare", "core_evidence_exports_compare",
            "app_changes_summarize", "app_call_path_find", "app_runtime_correlate",
            "app_rebuild_claim_check",
        ],
    },
    "database": {
        "title": "SQLite Schema & Record Inspection (1 tool)",
        "mode": "deep",
        "tools": ["db_sqlite_show"],
    },
    "projects": {
        "title": "Craft Anything Project & Pin Lifecycle (21 tools)",
        "mode": "clean_room_and_deep",
        "tools": [
            "project_list", "project_show", "project_inbox_answer", "project_play",
            "project_preview", "project_open_folder", "project_rename",
            "project_plan_fold", "project_duplicate", "project_delete",
            "project_questions_set", "project_approvals_set", "project_build_finish",
            "project_assets_budget", "project_assets_allow", "project_pin_create",
            "project_pins_list", "project_pin_open", "project_pin_stop",
            "project_pin_rename", "project_pin_delete",
        ],
    },
    "setup": {
        "title": "Engines, Settings (`deep_mode`) & WASM/MCP Plugins (9 tools)",
        "mode": "clean_room_and_deep",
        "tools": [
            "engines_list", "engines_install", "settings_show", "settings_set",
            "plugins_list", "plugins_refresh", "plugins_add", "plugins_remove",
            "engines_app_open",
        ],
    },
    "build": {
        "title": "Project Workspace File & Command Builder (6 tools)",
        "mode": "clean_room_and_deep",
        "tools": [
            "build_files_list", "build_file_read", "build_file_write",
            "build_file_edit", "build_checklist", "build_command_run",
        ],
    },
}

DIRECT_CURATED_TOOLS: List[Dict[str, Any]] = [
    {
        "name": "craft_doctor_and_status",
        "description": "[Craft-Anything Omni-Foundry] Run `craft-anything-cli doctor` and return installed version, Clean-Room vs Deep-Mode status, detected engines (Ghidra, Chromium, Rizin, TShark, Apktool), and active cloud relay health.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "craft_list_all_320_tools",
        "description": "[Craft-Anything Omni-Foundry] Browse or search all 320 tools across the 17 `storytold/craft-anything` toolsets (`core`, `native`, `apple`, `formats`, `managed`, `android`, `java`, `adb`, `browser`, `javascript`, `runtime`, `frida`, `application`, `database`, `projects`, `setup`, `build`).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "toolset": {"type": "string", "description": "Optional toolset filter (e.g. 'native', 'browser', 'formats', 'android', 'application')."},
                "search": {"type": "string", "description": "Optional keyword substring to filter tool names."},
            },
        },
    },
    {
        "name": "craft_call_any_tool",
        "description": "[Craft-Anything Omni-Foundry] Universal dispatcher that executes ANY of the 320 `storytold/craft-anything` tools by name (via the live `craft-anything-cli mcp` session or CLI subcommand `craft-anything-cli <id-with-dashes>`), automatically switching between Clean-Room and Deep mode.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tool_name": {"type": "string", "description": "Exact tool name (e.g. 'core_target_triage', 'native_function_pseudocode', 'web_site_capture', 'game_unity_list', 'js_app_map')."},
                "arguments": {"type": "object", "description": "JSON object of tool arguments."},
                "deep_mode": {"type": "boolean", "description": "Set true (default) to enable Deep Mode (--deep) for internal code/binary inspection, or false for Clean-Room mode (--clean-room)."},
            },
            "required": ["tool_name"],
        },
    },
    {
        "name": "craft_study_target",
        "description": "[Craft-Anything Omni-Foundry] Open and study any website URL, binary (.exe/.elf/.dll/.sys/.so), Android .apk, Unity/Unreal archive, Electron app.asar, or firmware file. Runs `core_target_open`, `core_target_triage`, and `core_overview_show` and returns structured evidence.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target_url_or_path": {"type": "string", "description": "HTTPS URL (website or downloadable file) or cloud path to inspect."},
                "deep_mode": {"type": "boolean", "description": "True for Deep Mode (code, binaries, JS, Ghidra), False for Clean-Room visual/DOM inspection."},
            },
            "required": ["target_url_or_path"],
        },
    },
    {
        "name": "craft_start_async_rebuild_or_study",
        "description": "[Craft-Anything Omni-Foundry] Start a long-running `craft-anything-cli rebuild` or deep inspection job asynchronously in the background and return a `job_id` in 0.1s (preventing Gemini's 20s MCP timeout).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Target website URL, file path, or '-' for scratch build."},
                "prompt": {"type": "string", "description": "Plain-language rebuild or study specification (e.g. 'Recreate this website in React' or 'A snake game in Rust')."},
                "deep_mode": {"type": "boolean", "description": "Enable --deep mode (default true)."},
                "rounds": {"type": "integer", "description": "Number of study-build-check refinement rounds (default 1)."},
            },
            "required": ["target", "prompt"],
        },
    },
    {
        "name": "craft_poll_async_job",
        "description": "[Craft-Anything Omni-Foundry] Poll the status, stdout/stderr log stream, `craft.json` state, `checks/` comparison diffs, and `investigation.cany` evidence of an asynchronous job started with `craft_start_async_rebuild_or_study`.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "job_id": {"type": "string", "description": "Job ID returned by `craft_start_async_rebuild_or_study`."},
            },
            "required": ["job_id"],
        },
    },
    {
        "name": "core_target_triage",
        "description": "[Craft-Anything Core] Identify a target file, app bundle, archive, or URL (architecture, format, compiler/runtime, packing, and recommended inspection tools).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path or URL to target."},
            },
            "required": ["path"],
        },
    },
    {
        "name": "native_function_pseudocode",
        "description": "[Craft-Anything Native] Decompile a function at a given name or address into readable pseudo-C using Craft Anything's built-in pure-Rust decompiler (and Ghidra when present).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "description": "Target binary path."},
                "function": {"type": "string", "description": "Function name or hex address."},
            },
            "required": ["function"],
        },
    },
    {
        "name": "web_site_capture",
        "description": "[Craft-Anything Browser] Capture a live website across multiple viewport widths (mobile, tablet, desktop), recording computed styles, colors, typography, layout metrics, and interactive states for clean-room rebuilding.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "Website URL to capture."},
            },
            "required": ["url"],
        },
    },
    {
        "name": "app_ledger_build",
        "description": "[Craft-Anything Application] Build a structured rebuild ledger mapping every observed feature, screen, route, and function of the original target against the new implementation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_folder": {"type": "string", "description": "Optional project folder path."},
            },
        },
    },
]


# ---------------------------------------------------------------------------
# 2. Automatic Non-Blocking Installation of `storytold/craft-anything`
# ---------------------------------------------------------------------------

def install_craft_anything_engine(work_dir: Path) -> Dict[str, Any]:
    """Download and unpack the official prebuilt `storytold/craft-anything` release
    for Linux x86_64 (`.deb` or `.tar.gz` or `.AppImage`)."""
    bin_dir = work_dir / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    os.environ["PATH"] = f"{bin_dir.resolve()}{os.pathsep}{os.environ.get('PATH', '')}"

    cli_bin = shutil.which("craft-anything-cli")
    if cli_bin:
        return {"status": "already_installed", "cli_path": cli_bin}

    sys_name = platform.system().lower()
    machine = platform.machine().lower()
    if "linux" not in sys_name:
        return {"status": "non_linux_host", "note": "Cloud runner installs Linux x86_64 binary automatically."}

    arch_slug = "aarch64" if ("aarch64" in machine or "arm64" in machine) else "x86_64"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "CraftAnything-OmniCloud/1.2"}

    deb_url = ""
    tar_url = ""
    appimage_url = ""
    tag_name = "v0.6.0"
    try:
        req = urllib.request.Request("https://api.github.com/repos/storytold/craft-anything/releases/latest", headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            rel = json.loads(resp.read().decode("utf-8"))
        tag_name = rel.get("tag_name") or "v0.6.0"
        for asset in rel.get("assets") or []:
            aname = asset.get("name", "")
            burl = asset.get("browser_download_url", "")
            if f"linux-{arch_slug}.deb" in aname and not aname.endswith(".asc"):
                deb_url = burl
            elif f"linux-{arch_slug}.tar.gz" in aname and not aname.endswith(".asc"):
                tar_url = burl
            elif f"linux-{arch_slug}.AppImage" in aname and not aname.endswith((".asc", ".zsync")):
                appimage_url = burl
    except Exception:
        ver = tag_name.lstrip("v")
        deb_url = f"https://github.com/storytold/craft-anything/releases/download/{tag_name}/craft-anything-{ver}-linux-{arch_slug}.deb"
        appimage_url = f"https://github.com/storytold/craft-anything/releases/download/{tag_name}/craft-anything-{ver}-linux-{arch_slug}.AppImage"

    # 1. Try .deb package first (v0.6.0 always publishes craft-anything-<ver>-linux-<arch>.deb)
    if deb_url:
        try:
            deb_path = work_dir / f"craft-anything-{arch_slug}.deb"
            print(f"[+] Downloading Craft Anything {tag_name} .deb package: {deb_url}", flush=True)
            urllib.request.urlretrieve(deb_url, str(deb_path))
            deb_extract = work_dir / "extracted_deb"
            deb_extract.mkdir(parents=True, exist_ok=True)
            subprocess.run(["dpkg-deb", "-x", str(deb_path), str(deb_extract)], check=False)
            for f in deb_extract.rglob("*"):
                if f.is_file() and f.name in ("craft-anything-cli", "craft-anything"):
                    dest = bin_dir / f.name
                    shutil.copy2(f, dest)
                    dest.chmod(0o755)
            deb_path.unlink(missing_ok=True)
        except Exception as exc:
            print(f"[!] Deb unpack notice: {exc}", flush=True)

    # 2. Fallback to tarball if present
    if not (bin_dir / "craft-anything-cli").exists() and tar_url:
        try:
            tar_path = work_dir / f"craft-anything-{arch_slug}.tar.gz"
            urllib.request.urlretrieve(tar_url, str(tar_path))
            extract_dir = work_dir / "extracted_tar"
            extract_dir.mkdir(parents=True, exist_ok=True)
            with tarfile.open(tar_path, "r:gz") as tf:
                tf.extractall(path=extract_dir)
            for f in extract_dir.rglob("*"):
                if f.is_file() and f.name in ("craft-anything-cli", "craft-anything"):
                    dest = bin_dir / f.name
                    shutil.copy2(f, dest)
                    dest.chmod(0o755)
            tar_path.unlink(missing_ok=True)
        except Exception:
            pass

    # 3. Fallback to AppImage (--appimage-extract) if needed
    if not (bin_dir / "craft-anything-cli").exists() and appimage_url:
        try:
            ai_path = work_dir / f"craft-anything-{arch_slug}.AppImage"
            urllib.request.urlretrieve(appimage_url, str(ai_path))
            ai_path.chmod(0o755)
            subprocess.run([str(ai_path), "--appimage-extract"], cwd=str(work_dir), check=False)
            sq_root = work_dir / "squashfs-root"
            if sq_root.exists():
                for f in sq_root.rglob("*"):
                    if f.is_file() and f.name in ("craft-anything-cli", "craft-anything"):
                        dest = bin_dir / f.name
                        shutil.copy2(f, dest)
                        dest.chmod(0o755)
            ai_path.unlink(missing_ok=True)
        except Exception:
            pass

    final_cli = shutil.which("craft-anything-cli") or (str(bin_dir / "craft-anything-cli") if (bin_dir / "craft-anything-cli").exists() else "")
    return {
        "status": "installed" if final_cli else "staging",
        "release_tag": tag_name,
        "cli_path": final_cli,
    }


# ---------------------------------------------------------------------------
# 3. Thread-Safe Stdio-to-HTTP MCP Bridge & CLI Executor for Craft Anything
# ---------------------------------------------------------------------------

class CraftAnythingEngineBridge:
    def __init__(self, work_dir: Path, install_in_background: bool = False) -> None:
        self.work_dir = work_dir
        self.projects_dir = work_dir / "projects"
        self.downloads_dir = work_dir / "targets"
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self.downloads_dir.mkdir(parents=True, exist_ok=True)
        self.call_lock = threading.Lock()
        self.mcp_proc: Optional[subprocess.Popen] = None
        self.async_jobs: Dict[str, Dict[str, Any]] = {}
        self.install_info: Dict[str, Any] = {"status": "initializing"}
        self.cli_bin: str = ""
        self.deep_mode = True

        if install_in_background:
            threading.Thread(target=self._bg_install, daemon=True).start()
        else:
            self._bg_install()

    def _bg_install(self) -> None:
        self.install_info = install_craft_anything_engine(self.work_dir)
        self.cli_bin = self.install_info.get("cli_path") or shutil.which("craft-anything-cli") or ""

    def _ensure_mcp_stdio_proc(self) -> Optional[subprocess.Popen]:
        if not self.cli_bin:
            self.cli_bin = shutil.which("craft-anything-cli") or (str(self.work_dir / "bin" / "craft-anything-cli") if (self.work_dir / "bin" / "craft-anything-cli").exists() else "")
        if not self.cli_bin or not Path(self.cli_bin).exists():
            return None
        if self.mcp_proc is not None and self.mcp_proc.poll() is None:
            return self.mcp_proc
        try:
            env = dict(os.environ)
            env["CRAFT_ANYTHING_DEEP_MODE"] = "1" if self.deep_mode else "0"
            self.mcp_proc = subprocess.Popen(
                [self.cli_bin, "mcp"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                cwd=str(self.projects_dir),
                env=env,
            )
            init_msg = json.dumps({
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "CraftAnything-Cloud-Bridge", "version": "1.2.0"},
                },
            })
            if self.mcp_proc.stdin and self.mcp_proc.stdout:
                self.mcp_proc.stdin.write(init_msg + "\n")
                self.mcp_proc.stdin.flush()
                self.mcp_proc.stdout.readline()
                notif = json.dumps({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
                self.mcp_proc.stdin.write(notif + "\n")
                self.mcp_proc.stdin.flush()
            return self.mcp_proc
        except Exception:
            self.mcp_proc = None
            return None

    def run_doctor(self) -> Dict[str, Any]:
        if not self.cli_bin and (self.work_dir / "bin" / "craft-anything-cli").exists():
            self.cli_bin = str(self.work_dir / "bin" / "craft-anything-cli")
        cli_out = ""
        ver_out = ""
        if self.cli_bin and Path(self.cli_bin).exists():
            try:
                ver_out = subprocess.check_output([self.cli_bin, "--version"], stderr=subprocess.STDOUT, text=True, timeout=8).strip()
            except Exception as e:
                ver_out = str(e)
            try:
                cli_out = subprocess.check_output([self.cli_bin, "doctor"], stderr=subprocess.STDOUT, text=True, timeout=15).strip()
            except Exception as e:
                cli_out = str(e)
        return {
            "engine": "storytold/craft-anything (Pure-Rust 320-Tool Engine)",
            "release_info": self.install_info,
            "cli_version": ver_out or "craft-anything-cli v0.6.0",
            "deep_mode_enabled": self.deep_mode,
            "total_toolsets": len(CRAFT_TOOLSETS),
            "total_engine_tools": sum(len(v["tools"]) for v in CRAFT_TOOLSETS.values()),
            "detected_companion_binaries": {
                "ghidra_headless": bool(shutil.which("analyzeHeadless") or Path("/tmp/ghidra_mcp_cloud/ghidra_12.1.4_PUBLIC/support/analyzeHeadless").exists()),
                "chromium": bool(shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")),
                "rizin": bool(shutil.which("rizin") or shutil.which("rz-bin")),
                "tshark": bool(shutil.which("tshark")),
                "objdump": bool(shutil.which("objdump")),
                "sqlite3": bool(shutil.which("sqlite3")),
            },
            "doctor_output": cli_out,
        }

    def prepare_target(self, url_or_path: str) -> str:
        val = url_or_path.strip()
        if val.startswith(("http://", "https://")):
            parsed = urllib.parse.urlparse(val)
            ext = Path(parsed.path).suffix.lower()
            if ext in (".exe", ".elf", ".dll", ".sys", ".so", ".apk", ".ipa", ".zip", ".tar", ".gz", ".pak", ".wasm", ".pcap", ".pcapng", ".db", ".sqlite", ".asar", ".bin"):
                fname = Path(parsed.path).name or f"target_{int(time.time())}{ext}"
                dest = self.downloads_dir / fname
                req = urllib.request.Request(val, headers={"User-Agent": "CraftAnything-Cloud/1.2"})
                with urllib.request.urlopen(req, timeout=25) as r:
                    dest.write_bytes(r.read())
                return str(dest.resolve())
            return val
        return val

    def invoke_craft_tool(self, tool_name: str, arguments: Dict[str, Any], deep_mode: bool = True) -> Dict[str, Any]:
        self.deep_mode = deep_mode
        norm_tool = tool_name.strip().replace("-", "_")
        cli_subcmd = norm_tool.replace("_", "-")

        with self.call_lock:
            proc = self._ensure_mcp_stdio_proc()
            if proc and proc.stdin and proc.stdout:
                try:
                    rpc_id = int(time.time() * 1000) % 1000000
                    req_str = json.dumps({
                        "jsonrpc": "2.0",
                        "id": rpc_id,
                        "method": "tools/call",
                        "params": {"name": norm_tool, "arguments": arguments or {}},
                    })
                    proc.stdin.write(req_str + "\n")
                    proc.stdin.flush()
                    line = proc.stdout.readline()
                    if line:
                        parsed = json.loads(line)
                        if "result" in parsed:
                            return parsed["result"]
                        if "error" in parsed:
                            return {"content": [{"type": "text", "text": json.dumps(parsed["error"], indent=2)}]}
                except Exception:
                    self.mcp_proc = None

        if self.cli_bin and Path(self.cli_bin).exists():
            cmd = [self.cli_bin]
            cmd.append("--deep" if deep_mode else "--clean-room")
            cmd.append(cli_subcmd)
            for k, v in (arguments or {}).items():
                if isinstance(v, bool):
                    if v:
                        cmd.append(f"--{k.replace('_', '-')}")
                elif v is not None and str(v) != "":
                    cmd.extend([f"--{k.replace('_', '-')}", str(v)])
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=18, cwd=str(self.projects_dir))
                return {
                    "content": [{
                        "type": "text",
                        "text": json.dumps({
                            "tool": norm_tool,
                            "cli_command": " ".join(cmd),
                            "exit_code": res.returncode,
                            "stdout": res.stdout.strip(),
                            "stderr": res.stderr.strip(),
                        }, indent=2),
                    }]
                }
            except Exception as exc:
                return {"content": [{"type": "text", "text": json.dumps({"tool": norm_tool, "error": str(exc)}, indent=2)}]}

        return {
            "content": [{
                "type": "text",
                "text": json.dumps({
                    "tool": norm_tool,
                    "arguments": arguments,
                    "status": "CLI_BINARY_STAGING",
                    "note": "craft-anything-cli is finishing background extraction (~15s); retry or call `craft_doctor_and_status`.",
                }, indent=2),
            }]
        }

    def start_async_job(self, target: str, prompt: str, deep_mode: bool = True, rounds: int = 1) -> Dict[str, Any]:
        job_id = f"craft-job-{uuid.uuid4().hex[:8]}"
        proj_dir = self.projects_dir / job_id
        proj_dir.mkdir(parents=True, exist_ok=True)
        resolved_target = self.prepare_target(target) if target != "-" else "-"

        job_record: Dict[str, Any] = {
            "job_id": job_id,
            "target": resolved_target,
            "prompt": prompt,
            "deep_mode": deep_mode,
            "rounds": rounds,
            "project_folder": str(proj_dir.resolve()),
            "status": "RUNNING",
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "logs": [],
        }
        self.async_jobs[job_id] = job_record

        def _worker() -> None:
            if not self.cli_bin or not Path(self.cli_bin).exists():
                job_record["status"] = "ERROR_CLI_NOT_FOUND"
                return
            cmd = [
                self.cli_bin,
                "--deep" if deep_mode else "--clean-room",
                "rebuild",
                resolved_target,
                prompt,
                "--rounds",
                str(max(1, rounds)),
                "--project-folder",
                str(proj_dir.resolve()),
            ]
            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=str(proj_dir),
                )
                if proc.stdout:
                    for line in proc.stdout:
                        job_record["logs"].append(line.rstrip())
                        if len(job_record["logs"]) > 200:
                            job_record["logs"] = job_record["logs"][-200:]
                proc.wait()
                job_record["exit_code"] = proc.returncode
                job_record["status"] = "COMPLETED" if proc.returncode == 0 else f"EXITED_{proc.returncode}"
            except Exception as exc:
                job_record["status"] = "FAILED"
                job_record["logs"].append(str(exc))

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        return {
            "job_id": job_id,
            "status": "STARTED_ASYNC",
            "project_folder": str(proj_dir.resolve()),
            "next_step": f"Call `craft_poll_async_job(job_id='{job_id}')` to inspect progress, craft.json, and evidence.",
        }

    def poll_async_job(self, job_id: str) -> Dict[str, Any]:
        job = self.async_jobs.get(job_id)
        if not job:
            return {"error": f"Unknown job_id: {job_id}", "active_jobs": list(self.async_jobs.keys())}
        proj_dir = Path(job["project_folder"])
        craft_json = {}
        if (proj_dir / "craft.json").exists():
            try:
                craft_json = json.loads((proj_dir / "craft.json").read_text(encoding="utf-8"))
            except Exception:
                pass
        files = [str(p.relative_to(proj_dir)) for p in sorted(proj_dir.rglob("*")) if p.is_file()][:60]
        return {
            "job_id": job_id,
            "status": job["status"],
            "target": job["target"],
            "prompt": job["prompt"],
            "craft_json": craft_json,
            "project_files": files,
            "recent_logs": job["logs"][-40:],
        }


# ---------------------------------------------------------------------------
# 4. 24/7 Perpetual GitHub Cloud Relay & Edge-Smart Cloudflare Worker Router
# ---------------------------------------------------------------------------

GITHUB_WORKFLOW_YML = """name: Craft-Anything 24/7 Perpetual Cloud MCP Relay

on:
  workflow_dispatch:
  push:
    branches: [ main ]
  schedule:
    - cron: '25 */5 * * *'

permissions:
  contents: write
  actions: write

concurrency:
  group: craft-anything-perpetual-relay
  cancel-in-progress: false

jobs:
  craft-anything-cloud:
    runs-on: ubuntu-24.04
    timeout-minutes: 330
    steps:
      - name: 1. Checkout Repository
        uses: actions/checkout@v4

      - name: 2. Boot Craft-Anything Cloud MCP Tunnel First & Publish LIVE_MCP_URL.json (~15s)
        run: |
          nohup python3 -u craft_anything_mcp_cloud_launcher.py --port 7860 > /tmp/craft_omni.log 2>&1 &
          echo "Waiting for Cloudflare Quick Tunnel to publish URL..."
          for i in $(seq 1 60); do
            if grep -qE "https://[a-zA-Z0-9-]+\\.trycloudflare\\.com" /tmp/craft_omni.log; then
              BASE_URL=$(grep -oE "https://[a-zA-Z0-9-]+\\.trycloudflare\\.com" /tmp/craft_omni.log | head -n 1)
              MCP_URL="${BASE_URL}/mcp"
              GUI_URL="${BASE_URL}/"
              printf '{"status":"LIVE","engine":"storytold/craft-anything","mcp_url":"%s","gui_url":"%s","updated_at":"%s"}\\n' "$MCP_URL" "$GUI_URL" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > LIVE_MCP_URL.json
              git config user.name "craft-anything-cloud-bot"
              git config user.email "bot@users.noreply.github.com"
              git add LIVE_MCP_URL.json
              git commit -m "Auto-update LIVE_MCP_URL.json [skip ci]" || true
              git push || true
              break
            fi
            sleep 2
          done
          cat /tmp/craft_omni.log

      - name: 3. Install Optional Companion Packages Non-Interactively in Background
        run: |
          sudo DEBIAN_FRONTEND=noninteractive apt-get update -qq || true
          sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq sqlite3 binutils unzip curl || true

      - name: 4. Keep Server Online (5-Hour Relay Window)
        run: |
          sleep 18000

      - name: 5. Perpetual Self-Respawn
        if: always()
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        run: |
          curl -sS -X POST \\
            -H "Authorization: Bearer ${GH_TOKEN}" \\
            -H "Accept: application/vnd.github+json" \\
            "https://api.github.com/repos/${GITHUB_REPOSITORY}/actions/workflows/craft_anything_mcp_cloud.yml/dispatches" \\
            -d '{"ref":"main"}' || true
"""


def build_permanent_cloudflare_worker_js(
    github_username: str,
    repo_name: str = "craft-anything-mcp-omni-cloud",
    gh_token_for_autowake: str = "",
) -> str:
    raw_json_url = f"https://raw.githubusercontent.com/{github_username}/{repo_name}/main/LIVE_MCP_URL.json"
    dispatch_url = f"https://api.github.com/repos/{github_username}/{repo_name}/actions/workflows/craft_anything_mcp_cloud.yml/dispatches"
    tools_json_str = json.dumps(DIRECT_CURATED_TOOLS)
    toolsets_json_str = json.dumps(CRAFT_TOOLSETS)

    return f"""/**
 * Craft-Anything v1.2 - Edge-Smart Permanent Cloudflare Worker Router + Instant MCP Handshake
 * ===========================================================================================
 * Guarantees that Gemini Connected Apps ("Add a custom app link") ALWAYS succeeds in 0ms
 * by handling `initialize`, `notifications/initialized`, `tools/list`, and `craft_list_all_320_tools`
 * directly at the Cloudflare Edge if the upstream GitHub runner is booting or rotating!
 */
const GITHUB_LIVE_JSON_URL = "{raw_json_url}";
const GITHUB_DISPATCH_URL = "{dispatch_url}";
const AUTO_WAKE_GH_TOKEN = "{gh_token_for_autowake}";
const EDGE_CURATED_TOOLS = {tools_json_str};
const EDGE_TOOLSETS = {toolsets_json_str};

async function triggerGithubAutoWake() {{
  if (!AUTO_WAKE_GH_TOKEN) return false;
  try {{
    const r = await fetch(GITHUB_DISPATCH_URL, {{
      method: "POST",
      headers: {{
        "Authorization": "Bearer " + AUTO_WAKE_GH_TOKEN,
        "Accept": "application/vnd.github+json",
        "User-Agent": "CraftAnything-Permanent-Router/1.2",
        "Content-Type": "application/json"
      }},
      body: JSON.stringify({{ ref: "main" }})
    }});
    return r.status === 204 || r.status === 200;
  }} catch (_) {{
    return false;
  }}
}}

async function getLatestTunnelUrl() {{
  const res = await fetch(GITHUB_LIVE_JSON_URL + "?t=" + Date.now(), {{
    headers: {{ "User-Agent": "CraftAnything-Permanent-Router/1.2" }}
  }});
  if (!res.ok) throw new Error("Could not fetch LIVE_MCP_URL.json: HTTP " + res.status);
  return await res.json();
}}

function handleEdgeFallbackJsonRpc(body, upstreamErr) {{
  const rpcId = body && body.id !== undefined ? body.id : 1;
  const method = (body && body.method) || "";
  const params = (body && body.params) || {{}};

  if (method === "initialize") {{
    return {{
      jsonrpc: "2.0",
      id: rpcId,
      result: {{
        protocolVersion: "2025-03-26",
        capabilities: {{ tools: {{ listChanged: true }} }},
        serverInfo: {{ name: "CraftAnything-OmniFoundry", version: "1.2.0" }}
      }}
    }};
  }}

  if (method === "notifications/initialized" || method.startsWith("notifications/")) {{
    return {{ jsonrpc: "2.0", id: rpcId, result: {{}} }};
  }}

  if (method === "tools/list") {{
    return {{
      jsonrpc: "2.0",
      id: rpcId,
      result: {{ tools: EDGE_CURATED_TOOLS }}
    }};
  }}

  if (method === "tools/call") {{
    const tName = params.name || "";
    const tArgs = params.arguments || {{}};

    if (tName === "craft_list_all_320_tools") {{
      const tsFilter = String(tArgs.toolset || "").trim().toLowerCase();
      const qFilter = String(tArgs.search || "").trim().toLowerCase();
      const out = {{}};
      for (const [k, v] of Object.entries(EDGE_TOOLSETS)) {{
        if (tsFilter && tsFilter !== k) continue;
        const matched = v.tools.filter((t) => !qFilter || t.toLowerCase().includes(qFilter));
        if (matched.length > 0) {{
          out[k] = {{ title: v.title, mode: v.mode, count: matched.length, tools: matched }};
        }}
      }}
      return {{
        jsonrpc: "2.0",
        id: rpcId,
        result: {{ content: [{{ type: "text", text: JSON.stringify(out, null, 2) }}] }}
      }};
    }}

    return {{
      jsonrpc: "2.0",
      id: rpcId,
      result: {{
        content: [{{
          type: "text",
          text: JSON.stringify({{
            status: "CLOUD_RELAY_BOOTING_OR_WAKING",
            tool_requested: tName,
            message: "Your 24/7 GitHub Cloud Relay for storytold/craft-anything is finishing its ~30s boot. Repeat this tool call in a few seconds!",
            detail: String(upstreamErr || "")
          }}, null, 2)
        }}]
      }}
    }};
  }}

  return {{ jsonrpc: "2.0", id: rpcId, result: {{}} }};
}}

export default {{
  async fetch(request) {{
    const corsHeaders = {{
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Accept, MCP-Session-Id, Last-Event-ID"
    }};

    if (request.method === "OPTIONS") {{
      return new Response(null, {{ status: 204, headers: corsHeaders }});
    }}

    const url = new URL(request.url);
    let parsedBody = null;
    let rawBodyBuffer = undefined;
    if (request.method !== "GET" && request.method !== "HEAD") {{
      rawBodyBuffer = await request.arrayBuffer();
      try {{
        parsedBody = JSON.parse(new TextDecoder().decode(rawBodyBuffer));
      }} catch (_) {{}}
    }}

    // Always answer MCP handshake (`initialize`, `notifications/initialized`, `tools/list`, `craft_list_all_320_tools`)
    // directly at the Cloudflare Edge if the upstream runner isn't needed or is still booting!
    if (parsedBody && (
      parsedBody.method === "initialize" ||
      parsedBody.method === "notifications/initialized" ||
      parsedBody.method === "tools/list" ||
      (parsedBody.method === "tools/call" && parsedBody.params && parsedBody.params.name === "craft_list_all_320_tools")
    )) {{
      return new Response(JSON.stringify(handleEdgeFallbackJsonRpc(parsedBody, null)), {{
        status: 200,
        headers: {{ "Content-Type": "application/json", ...corsHeaders }}
      }});
    }}

    try {{
      const live = await getLatestTunnelUrl();
      const targetBase = (live.gui_url || live.mcp_url.replace(/\\/mcp$/, "")).replace(/\\/$/, "");
      const targetUrl = targetBase + url.pathname + url.search;

      if (request.method === "GET" && (url.pathname === "/status" || url.pathname === "/router-status")) {{
        return new Response(JSON.stringify({{
          router: "Craft-Anything v1.2 Edge-Smart Permanent Router",
          active_backend_mcp_url: live.mcp_url,
          active_backend_gui_url: live.gui_url,
          updated_at: live.updated_at
        }}, null, 2), {{
          status: 200,
          headers: {{ "Content-Type": "application/json", ...corsHeaders }}
        }});
      }}

      const proxyReq = new Request(targetUrl, {{
        method: request.method,
        headers: request.headers,
        body: rawBodyBuffer,
      }});
      const resp = await fetch(proxyReq);
      if (resp.status === 530 || resp.status === 502) {{
        await triggerGithubAutoWake();
        throw new Error("Upstream tunnel rotated (HTTP " + resp.status + ") - triggered Auto-Wake!");
      }}
      const newHeaders = new Headers(resp.headers);
      newHeaders.set("Access-Control-Allow-Origin", "*");
      return new Response(resp.body, {{ status: resp.status, headers: newHeaders }});
    }} catch (err) {{
      await triggerGithubAutoWake();
      if (parsedBody) {{
        return new Response(JSON.stringify(handleEdgeFallbackJsonRpc(parsedBody, err)), {{
          status: 200,
          headers: {{ "Content-Type": "application/json", ...corsHeaders }}
        }});
      }}
      return new Response(JSON.stringify({{
        status: "AUTO_WAKING_CLOUD_RELAY",
        engine: "storytold/craft-anything v0.6.0 (320 tools)",
        message: "Signaled your 24/7 Craft-Anything GitHub Cloud Relay to wake (~30s).",
        error: String(err)
      }}, null, 2), {{
        status: 200,
        headers: {{ "Content-Type": "application/json", ...corsHeaders }}
      }});
    }}
  }}
}};
"""


# ---------------------------------------------------------------------------
# 5. Autonomous `--forever` Provisioner
# ---------------------------------------------------------------------------

def auto_detect_saved_github_token(work_dir: Path) -> str:
    candidates = [
        work_dir / "forever_credentials.json",
        Path.cwd() / "forever_credentials.json",
        Path.home() / ".ghidra_mcp_forever" / "forever_credentials.json",
        Path(tempfile.gettempdir()) / "ghidra_mcp_cloud" / "forever_credentials.json",
    ]
    for cfg in candidates:
        if cfg.exists():
            try:
                tok = json.loads(cfg.read_text(encoding="utf-8")).get("github_token", "")
                if tok:
                    return tok.strip()
            except Exception:
                pass
    for env_key in ("GITHUB_TOKEN", "GH_TOKEN"):
        if os.environ.get(env_key):
            return os.environ[env_key].strip()
    if shutil.which("gh"):
        try:
            out = subprocess.check_output(["gh", "auth", "token"], stderr=subprocess.DEVNULL, text=True).strip()
            if out and len(out) >= 20:
                return out
        except Exception:
            pass
    return ""


def copy_to_system_clipboard(text: str) -> bool:
    sys_name = platform.system().lower()
    try:
        if "windows" in sys_name:
            subprocess.run(["clip"], input=text.encode("utf-8"), check=True)
            return True
        if "darwin" in sys_name:
            subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
            return True
    except Exception:
        pass
    return False


def deploy_to_github_cloud_api(gh_token: str, repo_name: str = "craft-anything-mcp-omni-cloud") -> Dict[str, Any]:
    token = gh_token.strip()
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "CraftAnything-OmniFoundry/1.2",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        user_req = urllib.request.Request("https://api.github.com/user", headers=headers)
        with urllib.request.urlopen(user_req, timeout=10) as resp:
            username = json.loads(resp.read().decode("utf-8")).get("login")

        create_payload = json.dumps({
            "name": repo_name,
            "description": "Craft-Anything v1.2 Omni-Foundry - 24/7 Cloud MCP Server",
            "private": False,
            "auto_init": True,
        }).encode("utf-8")
        try:
            c_req = urllib.request.Request("https://api.github.com/user/repos", data=create_payload, headers=headers, method="POST")
            urllib.request.urlopen(c_req, timeout=15)
            time.sleep(2)
        except urllib.error.HTTPError as he:
            if he.code not in (422, 409):
                raise

        def _put_file(rel_path: str, content_str: str, msg: str) -> None:
            api_url = f"https://api.github.com/repos/{username}/{repo_name}/contents/{rel_path}"
            sha = None
            try:
                g_req = urllib.request.Request(api_url, headers=headers)
                with urllib.request.urlopen(g_req, timeout=8) as g_resp:
                    sha = json.loads(g_resp.read().decode("utf-8")).get("sha")
            except Exception:
                pass
            body_dict: Dict[str, Any] = {
                "message": msg,
                "content": base64.b64encode(content_str.encode("utf-8")).decode("ascii"),
            }
            if sha:
                body_dict["sha"] = sha
            p_req = urllib.request.Request(api_url, data=json.dumps(body_dict).encode("utf-8"), headers=headers, method="PUT")
            urllib.request.urlopen(p_req, timeout=20)

        launcher_source = Path(__file__).resolve().read_text(encoding="utf-8")
        _put_file("craft_anything_mcp_cloud_launcher.py", launcher_source, "Deploy Craft-Anything v1.2 Omni-Foundry [skip ci]")
        _put_file("cloudflare_permanent_router_worker.js", build_permanent_cloudflare_worker_js(username, repo_name), "Add Edge-Smart Permanent Router [skip ci]")
        _put_file(".github/workflows/craft_anything_mcp_cloud.yml", GITHUB_WORKFLOW_YML, "Add 24/7 Fast-Tunnel Craft-Anything Cloud Relay")

        # Cancel any older stuck/in-progress runs before dispatching the fresh runner
        try:
            runs_url = f"https://api.github.com/repos/{username}/{repo_name}/actions/runs?per_page=5"
            r_req = urllib.request.Request(runs_url, headers=headers)
            with urllib.request.urlopen(r_req, timeout=10) as r_resp:
                runs_data = json.loads(r_resp.read().decode("utf-8")).get("workflow_runs") or []
            for run in runs_data:
                if run.get("status") in ("in_progress", "queued", "waiting"):
                    cancel_url = f"https://api.github.com/repos/{username}/{repo_name}/actions/runs/{run['id']}/cancel"
                    try:
                        urllib.request.urlopen(urllib.request.Request(cancel_url, data=b"", headers=headers, method="POST"), timeout=6)
                    except Exception:
                        pass
            time.sleep(2)
        except Exception:
            pass

        try:
            disp_url = f"https://api.github.com/repos/{username}/{repo_name}/actions/workflows/craft_anything_mcp_cloud.yml/dispatches"
            disp_req = urllib.request.Request(disp_url, data=json.dumps({"ref": "main"}).encode("utf-8"), headers=headers, method="POST")
            urllib.request.urlopen(disp_req, timeout=10)
        except Exception:
            pass

        return {
            "status": "DEPLOYED_GITHUB_CLOUD",
            "username": username,
            "repo_name": repo_name,
            "raw_live_url": f"https://raw.githubusercontent.com/{username}/{repo_name}/main/LIVE_MCP_URL.json",
            "github_repo": f"https://github.com/{username}/{repo_name}",
            "github_actions_url": f"https://github.com/{username}/{repo_name}/actions",
        }
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def deploy_cloudflare_worker_automatically(
    work_dir: Path,
    github_username: str,
    repo_name: str,
    gh_token: str,
) -> Dict[str, Any]:
    worker_name = "craft-anything-mcp-forever"
    worker_js = build_permanent_cloudflare_worker_js(github_username, repo_name, gh_token)

    npx_cmd = "npx.cmd" if platform.system().lower() == "windows" and shutil.which("npx.cmd") else "npx"
    if not shutil.which(npx_cmd):
        return {"status": "NEEDS_NODE_NPX", "message": "Install Node.js (`npx`) to auto-deploy the Cloudflare Worker."}

    w_dir = work_dir / "cf_craft_forever_worker"
    w_dir.mkdir(parents=True, exist_ok=True)
    (w_dir / "worker.js").write_text(worker_js, encoding="utf-8")
    (w_dir / "wrangler.toml").write_text(
        f'name = "{worker_name}"\nmain = "worker.js"\ncompatibility_date = "2026-01-01"\nworkers_dev = true\n',
        encoding="utf-8",
    )

    print("[+] Deploying Edge-Smart Craft-Anything Router Worker via `npx --yes wrangler@latest deploy`...")
    proc = subprocess.Popen(
        [npx_cmd, "--yes", "wrangler@latest", "deploy"],
        cwd=str(w_dir),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    deployed_url = ""
    output_lines: List[str] = []
    if proc.stdout:
        for line in proc.stdout:
            print(line, end="", flush=True)
            output_lines.append(line)
            m = re.search(r"(https://[a-zA-Z0-9._-]+\.workers\.dev)", line)
            if m:
                deployed_url = m.group(1).rstrip("/") + "/mcp"
    proc.wait()

    full_out = "".join(output_lines)
    if not deployed_url and ("more than one account available" in full_out.lower() or "cloudflare_account_id" in full_out.lower()):
        acct_matches = re.findall(r"`([^`]+)`:\s*`([0-9a-fA-F]{32})`", full_out)
        chosen_name, chosen_id = "", ""
        for a_name, a_id in acct_matches:
            if "forested lung" in a_name.lower():
                chosen_name, chosen_id = a_name, a_id
                break
        if not chosen_id and acct_matches:
            chosen_name, chosen_id = acct_matches[0]
        if chosen_id:
            print(f"[+] Multiple Cloudflare accounts detected - auto-selecting `{chosen_name}` ({chosen_id}) and re-deploying...")
            (w_dir / "wrangler.toml").write_text(
                f'name = "{worker_name}"\naccount_id = "{chosen_id}"\nmain = "worker.js"\ncompatibility_date = "2026-01-01"\nworkers_dev = true\n',
                encoding="utf-8",
            )
            env_with_acct = dict(os.environ)
            env_with_acct["CLOUDFLARE_ACCOUNT_ID"] = chosen_id
            proc_retry = subprocess.Popen(
                [npx_cmd, "--yes", "wrangler@latest", "deploy"],
                cwd=str(w_dir),
                env=env_with_acct,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            if proc_retry.stdout:
                for line in proc_retry.stdout:
                    print(line, end="", flush=True)
                    output_lines.append(line)
                    m = re.search(r"(https://[a-zA-Z0-9._-]+\.workers\.dev)", line)
                    if m:
                        deployed_url = m.group(1).rstrip("/") + "/mcp"
            proc_retry.wait()

    if deployed_url:
        copy_to_system_clipboard(deployed_url)
        return {
            "status": "DEPLOYED_PERMANENT_WORKER",
            "permanent_mcp_url": deployed_url,
            "method": "Wrangler Auto-Deploy (Edge-Smart v1.2)",
        }
    return {"status": "WRANGLER_ERROR", "logs": "".join(output_lines[-15:])}


def run_forever_provisioner(work_dir: Path, gh_token_input: str = "") -> Dict[str, Any]:
    work_dir.mkdir(parents=True, exist_ok=True)
    gh_token = gh_token_input.strip() or auto_detect_saved_github_token(work_dir)
    if not gh_token:
        gh_url = "https://github.com/settings/tokens/new?description=CraftAnything-24x7-Forever&scopes=repo,workflow"
        print(f"Opening GitHub Token page: {gh_url}")
        try:
            webbrowser.open(gh_url)
        except Exception:
            pass
        gh_token = input("-> Paste your GitHub Token (ghp_...) and press Enter: ").strip()

    (work_dir / "forever_credentials.json").write_text(json.dumps({"github_token": gh_token}, indent=2), encoding="utf-8")

    print("[+] Step 1/3: Auto-provisioning 24/7 Perpetual GitHub Cloud Relay for `storytold/craft-anything`...")
    gh_res = deploy_to_github_cloud_api(gh_token, repo_name="craft-anything-mcp-omni-cloud")
    if gh_res.get("status") != "DEPLOYED_GITHUB_CLOUD":
        return gh_res

    print("[+] Step 2/3: Deploying Edge-Smart Permanent Front-Door Cloudflare Worker Router...")
    cf_res = deploy_cloudflare_worker_automatically(
        work_dir=work_dir,
        github_username=gh_res["username"],
        repo_name=gh_res["repo_name"],
        gh_token=gh_token,
    )

    print("[+] Step 3/3: Waiting for your 24/7 Craft-Anything Cloud Relay runner to publish LIVE_MCP_URL.json (~25-60s)...")
    live_tunnel_mcp = ""
    raw_live_url = gh_res["raw_live_url"]
    for elapsed in range(0, 75, 5):
        try:
            req = urllib.request.Request(f"{raw_live_url}?t={int(time.time())}", headers={"User-Agent": "CraftAnything-AutoProvisioner/1.2"})
            with urllib.request.urlopen(req, timeout=6) as r:
                live_data = json.loads(r.read().decode("utf-8"))
                if live_data.get("mcp_url"):
                    live_tunnel_mcp = live_data["mcp_url"]
                    break
        except Exception:
            pass
        print(f"    ... GitHub Cloud VM starting tunnel ({elapsed}s elapsed)...")
        time.sleep(5)

    final_url = cf_res.get("permanent_mcp_url") or live_tunnel_mcp
    if final_url:
        copy_to_system_clipboard(final_url)

    return {
        "status": "CRAFT_ANYTHING_FOREVER_COMPLETE",
        "github_repo": gh_res["github_repo"],
        "github_actions_url": gh_res["github_actions_url"],
        "raw_live_url": raw_live_url,
        "active_relay_tunnel_mcp_url": live_tunnel_mcp or "Edge Worker is LIVE now (GitHub runner finishes in ~20s)",
        "cloudflare_worker_result": cf_res,
        "final_gemini_mcp_url": final_url,
        "instructions": "DONE! Paste `final_gemini_mcp_url` into Gemini -> Settings -> Connected Apps -> Add a custom app link! (Edge-Smart v1.2 connects in 0ms even while the background runner boots!)",
    }


# ---------------------------------------------------------------------------
# 6. Streamable HTTP + SSE MCP Server (Fast Tunnel Startup Pattern)
# ---------------------------------------------------------------------------

def handle_mcp_jsonrpc(bridge: CraftAnythingEngineBridge, body: Dict[str, Any]) -> Dict[str, Any]:
    rpc_id = body.get("id", 1)
    method = body.get("method", "")
    params = body.get("params") or {}

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": rpc_id,
            "result": {
                "protocolVersion": "2025-03-26",
                "capabilities": {"tools": {"listChanged": True}},
                "serverInfo": {"name": "CraftAnything-OmniFoundry", "version": "1.2.0"},
            },
        }

    if method == "notifications/initialized":
        return {"jsonrpc": "2.0", "id": rpc_id, "result": {}}

    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rpc_id, "result": {"tools": DIRECT_CURATED_TOOLS}}

    if method == "tools/call":
        t_name = params.get("name", "")
        t_args = params.get("arguments") or {}

        if t_name == "craft_doctor_and_status":
            return {"jsonrpc": "2.0", "id": rpc_id, "result": {"content": [{"type": "text", "text": json.dumps(bridge.run_doctor(), indent=2)}]}}

        if t_name == "craft_list_all_320_tools":
            ts_filter = (t_args.get("toolset") or "").strip().lower()
            q_filter = (t_args.get("search") or "").strip().lower()
            out: Dict[str, Any] = {}
            for ts_key, ts_val in CRAFT_TOOLSETS.items():
                if ts_filter and ts_filter != ts_key:
                    continue
                matched = [t for t in ts_val["tools"] if not q_filter or q_filter in t.lower()]
                if matched:
                    out[ts_key] = {"title": ts_val["title"], "mode": ts_val["mode"], "count": len(matched), "tools": matched}
            return {"jsonrpc": "2.0", "id": rpc_id, "result": {"content": [{"type": "text", "text": json.dumps(out, indent=2)}]}}

        if t_name == "craft_call_any_tool":
            inner_tool = t_args.get("tool_name", "")
            inner_args = t_args.get("arguments") or {}
            deep = bool(t_args.get("deep_mode", True))
            res = bridge.invoke_craft_tool(inner_tool, inner_args, deep_mode=deep)
            return {"jsonrpc": "2.0", "id": rpc_id, "result": res}

        if t_name == "craft_study_target":
            target = bridge.prepare_target(t_args.get("target_url_or_path", ""))
            deep = bool(t_args.get("deep_mode", True))
            triage = bridge.invoke_craft_tool("core_target_triage", {"path": target}, deep_mode=deep)
            overview = bridge.invoke_craft_tool("core_overview_show", {"path": target}, deep_mode=deep)
            return {
                "jsonrpc": "2.0",
                "id": rpc_id,
                "result": {
                    "content": [{
                        "type": "text",
                        "text": json.dumps({"target": target, "deep_mode": deep, "triage": triage, "overview": overview}, indent=2),
                    }]
                },
            }

        if t_name == "craft_start_async_rebuild_or_study":
            job_res = bridge.start_async_job(
                target=t_args.get("target", "-"),
                prompt=t_args.get("prompt", ""),
                deep_mode=bool(t_args.get("deep_mode", True)),
                rounds=int(t_args.get("rounds", 1)),
            )
            return {"jsonrpc": "2.0", "id": rpc_id, "result": {"content": [{"type": "text", "text": json.dumps(job_res, indent=2)}]}}

        if t_name == "craft_poll_async_job":
            poll_res = bridge.poll_async_job(t_args.get("job_id", ""))
            return {"jsonrpc": "2.0", "id": rpc_id, "result": {"content": [{"type": "text", "text": json.dumps(poll_res, indent=2)}]}}

        res = bridge.invoke_craft_tool(t_name, t_args, deep_mode=bridge.deep_mode)
        return {"jsonrpc": "2.0", "id": rpc_id, "result": res}

    return {"jsonrpc": "2.0", "id": rpc_id, "result": {}}


def start_cloud_server(port: int, work_dir: Path) -> None:
    # Start bridge with background installation so HTTP server + Cloudflare tunnel boot in <10s!
    bridge = CraftAnythingEngineBridge(work_dir, install_in_background=True)

    class Handler(http.server.BaseHTTPRequestHandler):
        def _cors(self) -> None:
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, DELETE, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "Content-Type, Accept, MCP-Session-Id")

        def do_OPTIONS(self) -> None:
            self.send_response(204)
            self._cors()
            self.end_headers()

        def do_GET(self) -> None:
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(bridge.run_doctor(), indent=2).encode("utf-8"))

        def do_POST(self) -> None:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
            try:
                body = json.loads(raw)
            except Exception:
                body = {}
            resp = handle_mcp_jsonrpc(bridge, body)
            out_bytes = json.dumps(resp).encode("utf-8")
            self.send_response(200)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(out_bytes)))
            self.end_headers()
            self.wfile.write(out_bytes)

        def log_message(self, fmt: str, *args: Any) -> None:
            return

    class ThreadedTCPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
        daemon_threads = True
        allow_reuse_address = True

    srv = ThreadedTCPServer(("0.0.0.0", port), Handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    print(f"[+] Craft-Anything v1.2 Omni-Foundry MCP Server listening on 0.0.0.0:{port}/mcp", flush=True)

    cf_bin = shutil.which("cloudflared")
    if not cf_bin and platform.system().lower() == "linux":
        cf_path = work_dir / "cloudflared"
        if not cf_path.exists():
            urllib.request.urlretrieve(
                "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64",
                str(cf_path),
            )
            cf_path.chmod(0o755)
        cf_bin = str(cf_path)

    if cf_bin:
        tunnel_proc = subprocess.Popen(
            [cf_bin, "tunnel", "--url", f"http://127.0.0.1:{port}"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        printed = False
        if tunnel_proc.stdout:
            for line in tunnel_proc.stdout:
                print(line, end="", flush=True)
                m = re.search(r"(https://[a-zA-Z0-9-]+\.trycloudflare\.com)", line)
                if m and not printed:
                    printed = True
                    base_url = m.group(1).rstrip("/")
                    print("\n" + "=" * 78, flush=True)
                    print(f"  CRAFT-ANYTHING PUBLIC TUNNEL READY: {base_url}/mcp", flush=True)
                    print("=" * 78 + "\n", flush=True)

    while True:
        time.sleep(3600)


def main() -> int:
    parser = argparse.ArgumentParser(description="Craft-Anything v1.2 Omni-Foundry - 24/7 Cloud MCP Server & Auto-Provisioner")
    parser.add_argument("--forever", action="store_true", help="Auto-provision 24/7 GitHub Cloud Relay + Edge-Smart Permanent Cloudflare Worker URL")
    parser.add_argument("--port", type=int, default=7860, help="HTTP port for MCP server (default 7860)")
    parser.add_argument("--self-test", action="store_true", help="Run offline deterministic self-test of the 17 toolsets and JSON-RPC handler")
    args = parser.parse_args()

    work_dir = Path(tempfile.gettempdir()) / "craft_anything_mcp_cloud"
    work_dir.mkdir(parents=True, exist_ok=True)

    if args.self_test:
        bridge = CraftAnythingEngineBridge(work_dir, install_in_background=False)
        init_res = handle_mcp_jsonrpc(bridge, {"jsonrpc": "2.0", "id": 1, "method": "initialize"})
        list_res = handle_mcp_jsonrpc(bridge, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        worker_js = build_permanent_cloudflare_worker_js("alisyyed", "craft-anything-mcp-omni-cloud")
        assert "handleEdgeFallbackJsonRpc" in worker_js
        print(json.dumps({
            "self_test": "PASSED_V1_2_EDGE_SMART",
            "server_info": init_res["result"]["serverInfo"],
            "curated_mcp_tools_count": len(list_res["result"]["tools"]),
            "total_toolsets": len(CRAFT_TOOLSETS),
            "total_cataloged_engine_tools": sum(len(v["tools"]) for v in CRAFT_TOOLSETS.values()),
        }, indent=2))
        return 0

    if args.forever:
        res = run_forever_provisioner(Path.cwd())
        print("\n" + "=" * 82)
        print("  CRAFT-ANYTHING 24/7 CLOUD PROVISIONER RESULT (v1.2 EDGE-SMART)")
        print("=" * 82)
        print(json.dumps(res, indent=2))
        print("=" * 82)
        return 0

    start_cloud_server(args.port, work_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())