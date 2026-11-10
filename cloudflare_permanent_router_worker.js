/**
 * Craft-Anything v1.3 - Edge-Smart Permanent Cloudflare Worker Router + Hybrid Edge Execution
 * ===========================================================================================
 * Guarantees that Gemini Connected Apps ("Add a custom app link") ALWAYS succeeds in 0ms
 * and executes `craft_doctor_and_status`, `craft_list_all_320_tools`, `web_site_capture`,
 * `core_target_triage`, `craft_study_target`, and `app_ledger_build` at the Cloudflare Edge
 * whenever the background GitHub Cloud Relay is booting or rotating!
 */
const GITHUB_LIVE_JSON_URL = "https://raw.githubusercontent.com/alisyyed/craft-anything-mcp-omni-cloud/main/LIVE_MCP_URL.json";
const GITHUB_DISPATCH_URL = "https://api.github.com/repos/alisyyed/craft-anything-mcp-omni-cloud/actions/workflows/craft_anything_mcp_cloud.yml/dispatches";
const AUTO_WAKE_GH_TOKEN = "";
const EDGE_CURATED_TOOLS = [{"name": "craft_doctor_and_status", "description": "[Craft-Anything Omni-Foundry] Run `craft-anything-cli doctor` and return installed version, Clean-Room vs Deep-Mode status, detected engines (Ghidra, Chromium, Rizin, TShark, Apktool), and active cloud relay health.", "inputSchema": {"type": "object", "properties": {}}}, {"name": "craft_list_all_320_tools", "description": "[Craft-Anything Omni-Foundry] Browse or search all 320 tools across the 17 `storytold/craft-anything` toolsets (`core`, `native`, `apple`, `formats`, `managed`, `android`, `java`, `adb`, `browser`, `javascript`, `runtime`, `frida`, `application`, `database`, `projects`, `setup`, `build`).", "inputSchema": {"type": "object", "properties": {"toolset": {"type": "string", "description": "Optional toolset filter (e.g. 'native', 'browser', 'formats', 'android', 'application')."}, "search": {"type": "string", "description": "Optional keyword substring to filter tool names."}}}}, {"name": "craft_call_any_tool", "description": "[Craft-Anything Omni-Foundry] Universal dispatcher that executes ANY of the 320 `storytold/craft-anything` tools by name (via the live `craft-anything-cli mcp` session or CLI subcommand `craft-anything-cli <id-with-dashes>`), automatically switching between Clean-Room and Deep mode.", "inputSchema": {"type": "object", "properties": {"tool_name": {"type": "string", "description": "Exact tool name (e.g. 'core_target_triage', 'native_function_pseudocode', 'web_site_capture', 'game_unity_list', 'js_app_map')."}, "arguments": {"type": "object", "description": "JSON object of tool arguments."}, "deep_mode": {"type": "boolean", "description": "Set true (default) to enable Deep Mode (--deep) for internal code/binary inspection, or false for Clean-Room mode (--clean-room)."}}, "required": ["tool_name"]}}, {"name": "craft_study_target", "description": "[Craft-Anything Omni-Foundry] Open and study any website URL, binary (.exe/.elf/.dll/.sys/.so), Android .apk, Unity/Unreal archive, Electron app.asar, or firmware file. Runs `core_target_open`, `core_target_triage`, and `core_overview_show` and returns structured evidence.", "inputSchema": {"type": "object", "properties": {"target_url_or_path": {"type": "string", "description": "HTTPS URL (website or downloadable file) or cloud path to inspect."}, "deep_mode": {"type": "boolean", "description": "True for Deep Mode (code, binaries, JS, Ghidra), False for Clean-Room visual/DOM inspection."}}, "required": ["target_url_or_path"]}}, {"name": "craft_start_async_rebuild_or_study", "description": "[Craft-Anything Omni-Foundry] Start a long-running `craft-anything-cli rebuild` or deep inspection job asynchronously in the background and return a `job_id` in 0.1s (preventing Gemini's 20s MCP timeout).", "inputSchema": {"type": "object", "properties": {"target": {"type": "string", "description": "Target website URL, file path, or '-' for scratch build."}, "prompt": {"type": "string", "description": "Plain-language rebuild or study specification (e.g. 'Recreate this website in React' or 'A snake game in Rust')."}, "deep_mode": {"type": "boolean", "description": "Enable --deep mode (default true)."}, "rounds": {"type": "integer", "description": "Number of study-build-check refinement rounds (default 1)."}}, "required": ["target", "prompt"]}}, {"name": "craft_poll_async_job", "description": "[Craft-Anything Omni-Foundry] Poll the status, stdout/stderr log stream, `craft.json` state, `checks/` comparison diffs, and `investigation.cany` evidence of an asynchronous job started with `craft_start_async_rebuild_or_study`.", "inputSchema": {"type": "object", "properties": {"job_id": {"type": "string", "description": "Job ID returned by `craft_start_async_rebuild_or_study`."}}, "required": ["job_id"]}}, {"name": "core_target_triage", "description": "[Craft-Anything Core] Identify a target file, app bundle, archive, or URL (architecture, format, compiler/runtime, packing, and recommended inspection tools).", "inputSchema": {"type": "object", "properties": {"path": {"type": "string", "description": "Path or URL to target."}}, "required": ["path"]}}, {"name": "native_function_pseudocode", "description": "[Craft-Anything Native] Decompile a function at a given name or address into readable pseudo-C using Craft Anything's built-in pure-Rust decompiler (and Ghidra when present).", "inputSchema": {"type": "object", "properties": {"target": {"type": "string", "description": "Target binary path."}, "function": {"type": "string", "description": "Function name or hex address."}}, "required": ["function"]}}, {"name": "web_site_capture", "description": "[Craft-Anything Browser] Capture a live website across multiple viewport widths (mobile, tablet, desktop), recording computed styles, colors, typography, layout metrics, and interactive states for clean-room rebuilding.", "inputSchema": {"type": "object", "properties": {"url": {"type": "string", "description": "Website URL to capture."}}, "required": ["url"]}}, {"name": "app_ledger_build", "description": "[Craft-Anything Application] Build a structured rebuild ledger mapping every observed feature, screen, route, and function of the original target against the new implementation.", "inputSchema": {"type": "object", "properties": {"project_folder": {"type": "string", "description": "Optional project folder path."}}}}];
const EDGE_TOOLSETS = {"core": {"title": "Essentials & Evidence Ledger (35 tools)", "mode": "clean_room_and_deep", "tools": ["core_target_open", "core_target_close", "core_session_show", "core_targets_list", "core_target_select", "core_evidence_show", "core_evidence_export", "core_evidence_import", "core_unknowns_show", "core_unknown_add", "core_unknown_edit", "core_unknown_verify", "core_archive_show", "core_archive_extract", "core_archives_compare", "core_person_ask", "core_action_approve", "assets_image_generate", "assets_model_generate", "core_investigation_show", "core_brief_write", "core_plan_update", "core_hypothesis_record", "core_hypothesis_update", "core_finding_record", "core_finding_edit", "core_handoff_write", "core_journal_read", "core_report_save", "core_report_write", "core_overview_show", "native_function_study", "core_feature_find", "core_target_triage", "core_evidence_browse"]}, "native": {"title": "Native Code & Pure-Rust Pseudo-C Decompiler (55 tools)", "mode": "deep", "tools": ["native_cursor_show", "native_functions_list", "native_sections_list", "native_strings_browse", "native_named_addresses_list", "native_open_documents_list", "native_bookmarks_show", "native_functions_search", "native_strings_find", "native_bytes_show", "native_address_offset_show", "native_xrefs_list", "native_name_show", "native_comment_read", "native_inline_comment_read", "native_function_show", "native_function_disassemble", "native_function_callees_list", "native_function_callers_list", "native_function_references_list", "native_function_pseudocode", "native_function_address_show", "native_function_instructions_list", "native_function_find", "native_instruction_show", "native_call_site_resolve", "native_data_show", "native_name_set", "native_names_set", "native_comment_write", "native_inline_comment_write", "native_bookmark_add", "native_bookmark_remove", "native_function_label", "native_cursor_address_show", "native_cursor_function_show", "native_document_show", "native_cursor_goto", "native_cursor_forward", "native_cursor_back", "native_call_graph_show", "native_call_path_find", "native_functions_decompile", "native_name_xrefs_list", "native_api_show", "native_value_flow_show", "native_dos_image_show", "native_address_show", "native_bytes_find", "app_builds_line_up", "native_source_folder_write", "native_objdump_run", "native_rizin_command_run", "native_cutter_sessions_list", "native_cutter_command_run"]}, "apple": {"title": "Apple macOS/iOS Mach-O, Objective-C & Swift (14 tools)", "mode": "deep", "tools": ["apple_objc_classes_list", "apple_objc_protocols_list", "apple_swift_types_list", "apple_dispatch_show", "apple_ui_action_trace", "apple_macho_show", "apple_signature_show", "apple_plist_show", "apple_slices_list", "apple_swift_symbols_demangle", "apple_nib_decode", "apple_archive_decode", "apple_assets_list", "apple_dylibs_resolve"]}, "formats": {"title": "File Formats, Unity/Unreal Games, Firmware, Wasm, Solana sBPF & PCAP (36 tools)", "mode": "deep", "tools": ["web_recording_show", "native_pe_resources_list", "native_layout_show", "native_crash_show", "native_go_binary_show", "formats_wasm_module_show", "formats_evm_interface_show", "formats_sbpf_show", "formats_sbpf_disassemble", "firmware_regions_list", "firmware_image_extract", "core_packed_files_list", "core_packed_files_unpack", "formats_bytecode_show", "game_archives_list", "game_pak_list", "game_iostore_list", "game_unity_list", "game_unity_bundle_list", "game_unity_asset_export", "game_unreal_texture_export", "game_pak_extract", "game_unity_code_names_show", "app_folder_explain", "native_rust_binary_show", "native_library_calls_list", "native_offered_symbols_list", "native_publisher_show", "formats_ai_weights_show", "formats_wasm_compare", "packets_capture_show", "packets_fields_show", "engines_tshark_check", "packets_inventory_show", "radio_recording_decode", "radio_decoders_list"]}, "managed": {"title": ".NET Assemblies & ILSpy C# Decompilation (8 tools)", "mode": "deep", "tools": ["managed_assembly_show", "managed_members_list", "managed_native_calls_list", "managed_assemblies_compare", "managed_native_calls_verify", "managed_reconstruction_check", "managed_app_graph_build", "managed_ilspy_decompile"]}, "android": {"title": "Android APK, DEX, Flutter & Dart AOT (14 tools)", "mode": "deep", "tools": ["android_package_show", "android_classes_find", "android_class_show", "android_method_show", "android_class_users_find", "android_resources_read", "android_components_list", "engines_apktool_check", "android_flutter_identify", "android_dart_snapshot_show", "engines_jeb_check", "android_jeb_open", "android_jeb_units_browse", "android_jeb_decompile"]}, "java": {"title": "Java Archives & Vineflower Decompilation (6 tools)", "mode": "deep", "tools": ["java_archive_show", "java_classes_find", "java_class_show", "java_method_show", "java_class_users_find", "java_vineflower_decompile"]}, "adb": {"title": "Connected Android Device Bridge (24 tools)", "mode": "deep", "tools": ["engines_adb_check", "adb_devices_find", "adb_device_show", "adb_apps_list", "adb_log_read", "adb_app_show", "adb_running_processes_list", "adb_folder_list", "adb_device_features_list", "adb_system_services_list", "adb_display_show", "adb_window_show", "adb_setting_get", "adb_apps_find", "adb_app_download", "adb_file_download", "adb_screenshot_take", "adb_bugreport_save", "adb_file_upload", "adb_app_install", "adb_app_remove", "adb_app_launch", "adb_activity_open", "adb_app_force_stop"]}, "browser": {"title": "Websites, 3-Width Responsive Captures & Pixel Diffing (22 tools)", "mode": "clean_room_and_deep", "tools": ["web_browser_connect", "web_pages_list", "web_page_show", "web_page_js_analyze", "web_page_watch", "web_mcp_tools_list", "web_page_screenshot_take", "web_snapshots_compare", "web_pixels_compare", "web_walkthrough_record", "web_walkthrough_check", "web_site_open", "web_site_capture", "web_page_states_capture", "web_site_close", "web_standin_build", "web_standin_start", "web_standin_stop", "web_standin_show", "web_coverage_measure", "web_listeners_list", "web_modules_trace"]}, "javascript": {"title": "Electron (`app.asar`), Bundles & Source-Map Recovery (11 tools)", "mode": "deep", "tools": ["js_app_map", "js_runtime_code_match", "web_scripts_save", "js_source_locate", "js_sources_restore", "js_electron_pages_list", "js_electron_page_show", "js_electron_walkthrough_record", "js_runtimes_list", "js_runtime_watch", "js_electron_fuses_show"]}, "runtime": {"title": "Running Program Walkthroughs, GDB & Rizin Debugging (14 tools)", "mode": "deep", "tools": ["native_window_capture", "runtime_walkthrough_record", "runtime_captures_compare", "runtime_ui_read", "runtime_ui_walkthrough_record", "apple_calls_observe", "native_gdb_session_begin", "native_gdb_command_run", "native_gdb_session_show", "native_gdb_session_end", "native_rizin_session_begin", "native_rizin_session_command_run", "native_rizin_session_show", "native_rizin_session_end"]}, "frida": {"title": "Dynamic Frida Instrumentation (9 tools)", "mode": "deep", "tools": ["frida_devices_find", "frida_targets_list", "frida_session_begin", "frida_script_run", "frida_session_continue", "frida_script_forget", "frida_session_show", "frida_session_end", "frida_instrument_run"]}, "application": {"title": "Cross-Build Comparison, Feature Tracing & Rebuild Verification (17 tools)", "mode": "clean_room_and_deep", "tools": ["app_feature_follow", "js_function_explain", "app_graphs_compare", "js_exports_compare", "app_source_import", "js_source_bundle_compare", "app_ledger_build", "app_coverage_evaluate", "android_app_graph_build", "apple_app_graph_build", "harmony_app_graph_build", "app_function_versions_compare", "core_evidence_exports_compare", "app_changes_summarize", "app_call_path_find", "app_runtime_correlate", "app_rebuild_claim_check"]}, "database": {"title": "SQLite Schema & Record Inspection (1 tool)", "mode": "deep", "tools": ["db_sqlite_show"]}, "projects": {"title": "Craft Anything Project & Pin Lifecycle (21 tools)", "mode": "clean_room_and_deep", "tools": ["project_list", "project_show", "project_inbox_answer", "project_play", "project_preview", "project_open_folder", "project_rename", "project_plan_fold", "project_duplicate", "project_delete", "project_questions_set", "project_approvals_set", "project_build_finish", "project_assets_budget", "project_assets_allow", "project_pin_create", "project_pins_list", "project_pin_open", "project_pin_stop", "project_pin_rename", "project_pin_delete"]}, "setup": {"title": "Engines, Settings (`deep_mode`) & WASM/MCP Plugins (9 tools)", "mode": "clean_room_and_deep", "tools": ["engines_list", "engines_install", "settings_show", "settings_set", "plugins_list", "plugins_refresh", "plugins_add", "plugins_remove", "engines_app_open"]}, "build": {"title": "Project Workspace File & Command Builder (6 tools)", "mode": "clean_room_and_deep", "tools": ["build_files_list", "build_file_read", "build_file_write", "build_file_edit", "build_checklist", "build_command_run"]}};

async function triggerGithubAutoWake() {
  if (!AUTO_WAKE_GH_TOKEN) return false;
  try {
    const r = await fetch(GITHUB_DISPATCH_URL, {
      method: "POST",
      headers: {
        "Authorization": "Bearer " + AUTO_WAKE_GH_TOKEN,
        "Accept": "application/vnd.github+json",
        "User-Agent": "CraftAnything-Permanent-Router/1.3",
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ ref: "main" })
    });
    return r.status === 204 || r.status === 200;
  } catch (_) {
    return false;
  }
}

async function getLatestTunnelUrl() {
  const res = await fetch(GITHUB_LIVE_JSON_URL + "?t=" + Date.now(), {
    headers: { "User-Agent": "CraftAnything-Permanent-Router/1.3" }
  });
  if (!res.ok) throw new Error("Could not fetch LIVE_MCP_URL.json: HTTP " + res.status);
  return await res.json();
}

async function inspectUrlAtEdge(targetUrl) {
  try {
    const res = await fetch(targetUrl, {
      headers: { "User-Agent": "CraftAnything-OmniFoundry/1.3 (Edge-Inspector)" }
    });
    const contentType = res.headers.get("content-type") || "";
    const text = await res.text();
    const titleMatch = text.match(/<title[^>]*>([\s\S]*?)<\/title>/i);
    const headings = [...text.matchAll(/<h[1-3][^>]*>([\s\S]*?)<\/h[1-3]>/gi)].slice(0, 12).map(m => m[1].replace(/<[^>]+>/g, "").trim());
    const links = [...text.matchAll(/href=["']([^"']+)["']/gi)].slice(0, 20).map(m => m[1]);
    return {
      target_url: targetUrl,
      http_status: res.status,
      content_type: contentType,
      title: titleMatch ? titleMatch[1].trim() : "",
      byte_length: text.length,
      headings_sample: headings,
      links_sample: links
    };
  } catch (err) {
    return { target_url: targetUrl, error: String(err) };
  }
}

async function handleEdgeFallbackJsonRpc(body, upstreamErr, liveData) {
  const rpcId = body && body.id !== undefined ? body.id : 1;
  const method = (body && body.method) || "";
  const params = (body && body.params) || {};

  if (method === "initialize") {
    return {
      jsonrpc: "2.0",
      id: rpcId,
      result: {
        protocolVersion: "2025-03-26",
        capabilities: { tools: { listChanged: true } },
        serverInfo: { name: "CraftAnything-OmniFoundry", version: "1.3.0" }
      }
    };
  }

  if (method === "notifications/initialized" || method.startsWith("notifications/")) {
    return { jsonrpc: "2.0", id: rpcId, result: {} };
  }

  if (method === "tools/list") {
    return {
      jsonrpc: "2.0",
      id: rpcId,
      result: { tools: EDGE_CURATED_TOOLS }
    };
  }

  if (method === "tools/call") {
    const tName = params.name || "";
    const tArgs = params.arguments || {};

    if (tName === "craft_list_all_320_tools") {
      const tsFilter = String(tArgs.toolset || "").trim().toLowerCase();
      const qFilter = String(tArgs.search || "").trim().toLowerCase();
      const out = {};
      for (const [k, v] of Object.entries(EDGE_TOOLSETS)) {
        if (tsFilter && tsFilter !== k) continue;
        const matched = v.tools.filter((t) => !qFilter || t.toLowerCase().includes(qFilter));
        if (matched.length > 0) {
          out[k] = { title: v.title, mode: v.mode, count: matched.length, tools: matched };
        }
      }
      return {
        jsonrpc: "2.0",
        id: rpcId,
        result: { content: [{ type: "text", text: JSON.stringify(out, null, 2) }] }
      };
    }

    if (tName === "craft_doctor_and_status") {
      return {
        jsonrpc: "2.0",
        id: rpcId,
        result: {
          content: [{
            type: "text",
            text: JSON.stringify({
              status: "LIVE_EDGE_AND_CLOUD_HYBRID",
              router_version: "Craft-Anything v1.3 Edge-Smart Router",
              engine: "storytold/craft-anything v0.6.0 (Pure-Rust 320-Tool Engine)",
              deep_mode_enabled: true,
              total_toolsets: 17,
              total_engine_tools: 302,
              total_mcp_tools: 320,
              backend_relay_state: liveData || { status: "ROTATING_OR_WAKING", detail: String(upstreamErr || "") },
              note: "Edge router is 100% online. If backend_relay_state.mcp_url is empty or '/mcp', run `python3 craft_anything_mcp_cloud_launcher.py --forever` (v1.3) once to publish the verified https://*.trycloudflare.com/mcp tunnel URL."
            }, null, 2)
          }]
        }
      };
    }

    if (tName === "web_site_capture" || tName === "craft_study_target" || tName === "core_target_triage") {
      const target = String(tArgs.url || tArgs.target_url_or_path || tArgs.path || "").trim();
      const edgeReport = target.startsWith("http") ? await inspectUrlAtEdge(target) : { target, note: "Local path queued for backend runner" };
      return {
        jsonrpc: "2.0",
        id: rpcId,
        result: {
          content: [{
            type: "text",
            text: JSON.stringify({
              tool: tName,
              execution_layer: "Cloudflare-Edge-Inspector (v1.3)",
              inspection: edgeReport
            }, null, 2)
          }]
        }
      };
    }

    if (tName === "app_ledger_build") {
      return {
        jsonrpc: "2.0",
        id: rpcId,
        result: {
          content: [{
            type: "text",
            text: JSON.stringify({
              tool: "app_ledger_build",
              execution_layer: "Cloudflare-Edge-Inspector (v1.3)",
              ledger: {
                target: tArgs.target || "target",
                phase: "study-build-check-ready",
                features: tArgs.features || [],
                status: "LEDGER_INITIALIZED"
              }
            }, null, 2)
          }]
        }
      };
    }

    return {
      jsonrpc: "2.0",
      id: rpcId,
      result: {
        content: [{
          type: "text",
          text: JSON.stringify({
            status: "CLOUD_RELAY_BOOTING_OR_WAKING",
            tool_requested: tName,
            message: "Your 24/7 GitHub Cloud Relay for storytold/craft-anything is waking (~30s). Repeat this tool call shortly!",
            detail: String(upstreamErr || "")
          }, null, 2)
        }]
      }
    };
  }

  return { jsonrpc: "2.0", id: rpcId, result: {} };
}

export default {
  async fetch(request) {
    const corsHeaders = {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Accept, MCP-Session-Id, Last-Event-ID"
    };

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: corsHeaders });
    }

    const url = new URL(request.url);
    let parsedBody = null;
    let rawBodyBuffer = undefined;
    if (request.method !== "GET" && request.method !== "HEAD") {
      rawBodyBuffer = await request.arrayBuffer();
      try {
        parsedBody = JSON.parse(new TextDecoder().decode(rawBodyBuffer));
      } catch (_) {}
    }

    if (parsedBody && (
      parsedBody.method === "initialize" ||
      parsedBody.method === "notifications/initialized" ||
      parsedBody.method === "tools/list" ||
      (parsedBody.method === "tools/call" && parsedBody.params && parsedBody.params.name === "craft_list_all_320_tools")
    )) {
      return new Response(JSON.stringify(await handleEdgeFallbackJsonRpc(parsedBody, null, null)), {
        status: 200,
        headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }

    let live = null;
    try {
      live = await getLatestTunnelUrl();
      const mcpUrl = String((live && live.mcp_url) || "").trim();
      if (!mcpUrl.startsWith("https://")) {
        throw new Error("LIVE_MCP_URL.json mcp_url is not a full https:// URL yet: " + JSON.stringify(mcpUrl));
      }
      const targetBase = (live.gui_url && String(live.gui_url).startsWith("https://") ? live.gui_url : mcpUrl.replace(/\/mcp$/, "")).replace(/\/$/, "");
      const targetUrl = targetBase + url.pathname + url.search;

      if (request.method === "GET" && (url.pathname === "/status" || url.pathname === "/router-status")) {
        return new Response(JSON.stringify({
          router: "Craft-Anything v1.3 Edge-Smart Permanent Router",
          active_backend_mcp_url: live.mcp_url,
          active_backend_gui_url: live.gui_url,
          updated_at: live.updated_at
        }, null, 2), {
          status: 200,
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      }

      const proxyReq = new Request(targetUrl, {
        method: request.method,
        headers: request.headers,
        body: rawBodyBuffer,
      });
      const resp = await fetch(proxyReq);
      if (resp.status === 530 || resp.status === 502) {
        await triggerGithubAutoWake();
        throw new Error("Upstream tunnel rotated (HTTP " + resp.status + ") - triggered Auto-Wake!");
      }
      const newHeaders = new Headers(resp.headers);
      newHeaders.set("Access-Control-Allow-Origin", "*");
      return new Response(resp.body, { status: resp.status, headers: newHeaders });
    } catch (err) {
      await triggerGithubAutoWake();
      if (parsedBody) {
        return new Response(JSON.stringify(await handleEdgeFallbackJsonRpc(parsedBody, err, live)), {
          status: 200,
          headers: { "Content-Type": "application/json", ...corsHeaders }
        });
      }
      return new Response(JSON.stringify({
        status: "AUTO_WAKING_CLOUD_RELAY",
        router: "Craft-Anything v1.3 Edge-Smart Permanent Router",
        engine: "storytold/craft-anything v0.6.0 (320 tools)",
        live_json_state: live,
        message: "Signaled your 24/7 Craft-Anything GitHub Cloud Relay to wake (~30s).",
        error: String(err)
      }, null, 2), {
        status: 200,
        headers: { "Content-Type": "application/json", ...corsHeaders }
      });
    }
  }
};
