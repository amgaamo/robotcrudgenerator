"""
UI Module for the Keyword Factory Tab
(MODIFIED: Includes auto-import logic from 'pageobjects')
"""
import streamlit as st
import uuid
import json
import os  # <--- ตรวจสอบว่ามี import นี้
import re
import textwrap
from . import kw_manager
from .session_manager import get_clean_locator_name
from .ui_common import render_argument_input, ARGUMENT_PRESETS, ARGUMENT_PATTERNS
from .dialog_commonkw import render_add_step_dialog_base
from .file_manager import append_robot_content_intelligently, create_new_robot_file, scan_robot_project
from .test_flow_manager import categorize_keywords
from datetime import datetime
from .utils import parse_robot_keywords  # <--- ตรวจสอบว่ามี import นี้
from .utils import scan_steps_for_variables, generate_arg_name_from_locator, format_args_as_string, format_args_as_multiline_string
from .utils import FILL_FORM_DEFAULTS, VERIFY_FORM_DEFAULTS
from .simplified_quick_fill_dialog import render_kw_factory_fill_form_dialog as render_simplified_fill
from .simplified_quick_verify_dialog import render_kw_factory_verify_detail_dialog as render_simplified_verify
from .ui_reorder_component import render_sortable_arguments, render_sortable_steps

# ======= ENTRY POINT FUNCTION =======
def render_keyword_factory_tab():
    """
    Main entry point for the Keyword Factory Tab
    """
    from .crud_generator.ui_crud import inject_hybrid_css
    from .ui_common import extract_csv_datasource_keywords
    inject_hybrid_css()

    kw_manager.initialize_workspace()
    ws = kw_manager._get_workspace()

    # --- Main View Switching (List vs. Editor) ---
    if ws.get('active_keyword_id') is None:
        render_keyword_list_view(ws) # <--- เราจะแก้ไขฟังก์ชันนี้
    else:
        render_keyword_editor_view(ws)

# ======= LIST VIEW (ฉบับแก้ไขใหม่) =======
def render_keyword_list_view(ws):
    """
    Displays the list of all created keywords and a button to create new ones.
    (MODIFIED: Includes auto-import logic from 'pageobjects')
    """
    st.markdown("#### 🏭 Keyword Factory", unsafe_allow_html=True)
    st.caption("Create and manage reusable, high-level keywords from smaller steps.")

    # --- START: NEW Auto-Import Logic ---
    
    # 1. Initialize the flag if it doesn't exist
    if 'project_keywords_auto_imported' not in st.session_state:
        st.session_state.project_keywords_auto_imported = False

    project_path = st.session_state.get("project_path")
    project_structure = st.session_state.get("project_structure")

    # 2. Check if we need to run the import
    if project_path and project_structure and not st.session_state.project_keywords_auto_imported:
        
        all_robot_files = project_structure.get('robot_files', [])
        target_folder = "pageobjects"
        pageobject_files = [
            f for f in all_robot_files 
            if f.replace(os.sep, '/').startswith(target_folder + '/')
        ]
        
        if pageobject_files:
            new_keywords_imported_count = 0
            
            # ใช้ st.spinner เพื่อแสดงสถานะการโหลด
            with st.spinner(f"Scanning {len(pageobject_files)} files in `pageobjects` for keywords..."):
                for rel_path in pageobject_files:
                    full_path = os.path.join(project_path, rel_path)
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        parsed_keywords = parse_robot_keywords(content)
                        
                        for kw in parsed_keywords:
                            # ใช้ import function (ซึ่งตอนนี้เช็คซ้ำแบบเงียบๆ แล้ว)
                            new_id = kw_manager.import_existing_keyword(
                                kw['name'], 
                                kw.get('args', []), 
                                kw.get('doc', 'Imported keyword.'),
                                tags=['Imported', f"from:{target_folder}"] # เพิ่ม Tag
                            )
                            if new_id:
                                new_keywords_imported_count += 1
                                
                    except Exception as e:
                        st.warning(f"Could not parse {rel_path}: {e}")

            if new_keywords_imported_count > 0:
                 st.toast(f"Auto-imported {new_keywords_imported_count} new keywords from `pageobjects`.", icon="✅")
        
        # 3. Set the flag to True so this doesn't run again
        st.session_state.project_keywords_auto_imported = True
        
        # 4. Rerun to refresh the list immediately
        st.rerun()
    
    # --- END: NEW Auto-Import Logic ---

    # ปุ่มสร้าง Keyword ใหม่
    if st.button("➕ Create New Keyword", width='content', type="secondary"):
        kw_manager.create_new_keyword()
        st.rerun()

    all_keywords = kw_manager.get_all_keywords()
    
    st.markdown("---") 
    st.markdown("#### Manage Existing Keywords")

    # --- NEW: Add CSS for Tags ---
    st.markdown("""
    <style>
    .tag-container {
        display: flex;
        flex-wrap: wrap;
        gap: 4px;
        margin-top: 5px;
    }
    .tag {
        font-size: 0.7rem;
        font-weight: 600;
        padding: 2px 6px;
        border-radius: 10px;
        background-color: #30363d; /* Default tag color */
        color: #8b949e;
        border: 1px solid #484f58;
    }
    .tag-imported { /* Specific style for 'imported' tag */
        background-color: rgba(56, 139, 253, 0.1);
        color: #79c0ff;
        border: 1px solid rgba(56, 139, 253, 0.4);
    }
    .tag-from { /* Specific style for 'from:' tag */
        background-color: rgba(110, 118, 129, 0.1);
        color: #8b949e;
        border: 1px solid rgba(110, 118, 129, 0.4);
    }
    </style>
    """, unsafe_allow_html=True)
    # --- END: Add CSS ---

    if not all_keywords:
        st.info("No keywords found. Create one, or set a project path in the sidebar to auto-import from `pageobjects`.")
        return

    for kw in all_keywords:
        
        # --- START: เพิ่มตัวแปรเช็คสถานะ Import ---
        is_imported = 'Imported' in kw.get('tags', [])
        # --- END: เพิ่มตัวแปรเช็คสถานะ Import ---

        with st.container(border=True):
            cols = st.columns([4, 1, 1])
            with cols[0]:
                st.markdown(f"**{kw.get('name', 'Untitled')}**")
                
                args_display = [f"{arg['name']}" + (f"={arg['default']}" if arg.get('default') else "")
                                for arg in kw.get('args', [])]
                args_str = ', '.join(args_display) or 'None'
                st.caption(f"Arguments: `{args_str}`") 
                
                # --- START: แก้ไข (ซ่อน Steps ถ้า Import มา) ---
                if not is_imported:
                    st.caption(f"Steps: {len(kw.get('steps', []))}")
                # --- END: แก้ไข ---

                tags = kw.get('tags', [])
                if tags:
                    tags_html = ""
                    for tag in tags:
                        tag_class = tag.split(':')[0].lower() 
                        tags_html += f"<span class='tag tag-{tag_class}'>{tag}</span>"
                    st.markdown(f"<div class='tag-container'>{tags_html}</div>", unsafe_allow_html=True)

            # --- START: แก้ไข (ปิดปุ่มถ้า Import มา) ---
            with cols[1]:
                if not is_imported:
                    # Factory-created: ปุ่ม Edit ใช้งานได้
                    if st.button("✏️ Edit", key=f"edit_kw_{kw['id']}", use_container_width=True):
                        kw_manager.set_active_keyword(kw['id'])
                        st.rerun()
                else:
                    # Imported: ปุ่ม Edit ปิดใช้งาน
                    st.button("✏️", key=f"edit_kw_disabled_{kw['id']}", use_container_width=True, disabled=True, help="Imported keywords cannot be edited. Create a new keyword and add this as a step.")

            with cols[2]:
                if not is_imported:
                    # Factory-created: ปุ่ม Delete ใช้งานได้
                    if st.button("🗑️ Delete", key=f"del_kw_{kw['id']}", use_container_width=True):
                        kw_manager.delete_keyword(kw['id'])
                        st.rerun()
                else:
                    # Imported: ปุ่ม Delete ปิดใช้งาน
                    st.button("🗑️", key=f"del_kw_disabled_{kw['id']}", use_container_width=True, disabled=True, help="Imported keywords cannot be deleted.")
            # --- END: แก้ไข ---


# ======= (โค้ดส่วนที่เหลือของไฟล์ ui_keyword_factory.py) =======
# (ฟังก์ชัน render_keyword_editor_view และอื่นๆ
#  ให้คงไว้เหมือนเดิม ไม่ต้องลบครับ)
# ==========================================================

# ======= EDITOR VIEW =======
def render_keyword_editor_view(ws):
    """
    Displays the editor for a single keyword (details, steps, preview).
    (Incorporates Argument Manager and Reordering)
    """
    keyword_id = ws.get('active_keyword_id')
    kw = kw_manager.get_keyword(keyword_id)

    if not kw:
        st.error("Error: Could not find keyword to edit.")
        kw_manager.set_active_keyword(None)
        st.rerun()
        return

    if st.button("← Back to Keyword List"):
        kw_manager.set_active_keyword(None)
        st.rerun()

    header_left, header_right = st.columns([0.6, 0.4], gap="large")

    with header_left:
        st.markdown(f"<h3 style='font-size: 1.6rem;'>✏️ Editing: {kw.get('name', '...')}</h3>", unsafe_allow_html=True)
        st.caption("Define the keyword's arguments, steps, and documentation.")

    with header_right:
        st.markdown("<h3 style='font-size: 1.6rem;'>🚀 Live Code Preview</h3>", unsafe_allow_html=True)
        st.caption("Updates automatically as you edit")

    left_editor, right_preview = st.columns([0.6, 0.4], gap="large")

    # --- LEFT PANEL: EDITOR ---
    with left_editor:
        # --- 1. Keyword Details ---
        with st.expander("⚙️ Keyword Configuration", expanded=True):
            # ***** Keyword Name *****
            st.text_input(
                "Keyword Name",
                value=kw['name'],
                key=f"kw_name_{keyword_id}",
                on_change=lambda: kw_manager.update_keyword_details(
                    keyword_id,
                    st.session_state[f"kw_name_{keyword_id}"],
                )
            )
            # ***** End Keyword Name *****

            st.markdown("---") # เส้นคั่น

            # ***** Argument Manager UI with Drag & Drop *****
            steps = kw.get('steps', [])
            detected_vars = scan_steps_for_variables(steps)
            
            # Initialize args
            if 'args' not in kw or not isinstance(kw['args'], list):
                kw['args'] = []
            
            current_ordered_args = kw.get('args', [])
            selected_arg_names = {arg['name'] for arg in current_ordered_args}
            
            # Section 1: Unused Variables
            detected_but_not_selected = sorted([
                var_name for var_name in detected_vars
                if var_name not in selected_arg_names
            ])
            
            if detected_but_not_selected:
                with st.expander(f"➕ **Add Arguments** ({len(detected_but_not_selected)} unused variables)", 
                                expanded=len(current_ordered_args) == 0):
                    st.caption("Select variables to use as keyword arguments:")
                    
                    # Select all button
                    if st.button("✅ Select All Unused", use_container_width=True, 
                                key=f"select_all_args_{keyword_id}"):
                        for var_name in detected_but_not_selected:
                            current_ordered_args.append({'name': var_name, 'default': ''})
                        kw['args'] = current_ordered_args
                        st.rerun()
                    
                    st.markdown("---")
                    
                    # List unused variables with add buttons
                    for var_name in detected_but_not_selected:
                        col_add, col_name = st.columns([0.8, 4])
                        with col_add:
                            if st.button("➕", key=f"add_arg_{keyword_id}_{var_name}", 
                                       help="Add as argument", use_container_width=True):
                                current_ordered_args.append({'name': var_name, 'default': ''})
                                kw['args'] = current_ordered_args
                                st.rerun()
                        with col_name:
                            st.code(var_name, language='robotframework')
            
            # Section 2: Sortable Arguments
            render_sortable_arguments(keyword_id, kw)
            
            # ***** End Argument Manager UI *****

            st.markdown("---") # เส้นคั่น

        # --- 2. Quick Templates ---
        st.markdown("---") # เพิ่มเส้นคั่น
        st.markdown("**⚡ Quick Step Templates**")
        st.caption("Add multiple steps at once based on locators.")
        
        t_col1, t_col2 = st.columns(2)
        with t_col1:
            if st.button("✏️ Quick Fill Form", use_container_width=True):
                st.session_state.show_kw_factory_fill_form_dialog = True
                st.session_state['kw_factory_add_dialog_context'] = {"key": keyword_id}
                st.rerun()
        with t_col2:
            if st.button("🔍 Quick Verify Detail", use_container_width=True):
                st.session_state.show_kw_factory_verify_detail_dialog = True
                st.session_state['kw_factory_add_dialog_context'] = {"key": keyword_id}
                st.rerun()

        # --- 3. Step Editor ---
        st.markdown("---") # เพิ่มเส้นคั่น
        
        # Toggle for drag & drop mode
        col_title, col_toggle = st.columns([3, 1])
        with col_title:
            st.markdown("#### 👣 Keyword Steps")
        with col_toggle:
            use_drag_drop = st.toggle("🎯 Drag", key=f"drag_mode_{keyword_id}", 
                                     help="Enable drag & drop reordering")
        
        steps = kw.get('steps', [])

        if not steps:
            st.info("No steps yet. Click 'Add Step' below.")
        else:
            if use_drag_drop:
                # Drag & Drop Mode
                render_sortable_steps(keyword_id, kw)
            else:
                # Normal Mode (existing code)
                indent_level = 0
                for i, step in enumerate(steps):
                    render_step_card_compact_for_kw(step, i, keyword_id, steps, indent_level)
                    
                    if step.get('keyword') == 'IF Condition':
                        indent_level += 1
                    elif step.get('keyword') == 'END':
                        indent_level = max(0, indent_level - 1)

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ Add Step", use_container_width=True, key=f"kw_add_step_{keyword_id}"):
                st.session_state['show_kw_factory_add_dialog'] = True
                st.session_state['kw_factory_add_dialog_context'] = {"key": keyword_id}
                st.rerun()
        with col2:
            if st.button("⚡ Add API/CSV Step", use_container_width=True, key=f"kw_add_api_csv_step_{keyword_id}"):
                st.session_state['show_kw_factory_api_csv_dialog'] = True
                st.session_state['kw_factory_api_csv_dialog_context'] = {"key": keyword_id}
                st.rerun()

    # --- RIGHT PANEL: PREVIEW & SAVE ---
    with right_preview:
        # --- 1. Live Preview ---
        script_code = kw_manager.generate_robot_script_for_keyword(keyword_id)

        st.markdown('<div class="code-preview-container">', unsafe_allow_html=True)
        st.code(script_code, language="robotframework", line_numbers=True)
        st.markdown('</div>', unsafe_allow_html=True)

        # --- 2. Save to File Options ---
        st.markdown("---")
        st.subheader("💾 Save to Project File")

        if 'kw_save_option' not in st.session_state:
            st.session_state.kw_save_option = "Append to Existing File"

        st.session_state.kw_save_option = st.radio(
            "Save Mode",
            ["Append to Existing File", "Create New File"],
            key="radio_kw_save_mode",
            horizontal=True,
            label_visibility="collapsed"
        )
        save_option = st.session_state.kw_save_option
        project_path = st.session_state.get("project_path") # Use .get() for safety

        if not project_path:
             st.warning("⚠️ Project path not set in sidebar. Save options disabled.")
        elif save_option == "Append to Existing File":
            all_robot_files = st.session_state.project_structure.get('robot_files', [])
            target_folder_1 = "resources"
            target_folder_2 = "pageobjects"

            # 1. Get files from 'resources'
            resource_files_list = [
                f for f in all_robot_files
                if f.replace(os.sep, '/').startswith(target_folder_1 + '/')
            ]
            
            # 2. Get files from 'pageobjects'
            pageobject_files_list = [
                f for f in all_robot_files
                if f.replace(os.sep, '/').startswith(target_folder_2 + '/')
            ]

            # 3. Combine them
            combined_files_list = resource_files_list + pageobject_files_list
            # --- END: MODIFICATION ---

            if not combined_files_list: # Check the combined list
                # Update the warning message
                st.warning(f"No files found in `{target_folder_1}/` or `{target_folder_2}/` folders.")
            else:
                # Use the combined list for the options
                file_options = [f.replace(os.sep, '/') for f in combined_files_list]
                
                selected_file = st.selectbox(
                    # Update the label to show both folders
                    f"Select a file in `{target_folder_1}/` or `{target_folder_2}/` to append to:",
                    options=sorted(file_options), # Sort the combined list
                    key="kw_append_target"
                )

                if st.button("➕ Append Keyword", key="append_kw_btn"):
                    full_path = os.path.join(project_path, selected_file)
                    success, message = append_robot_content_intelligently(
                        full_path,
                        keywords_code=script_code
                    )
                    if success:
                        st.success(message)
                    else:
                        st.error(message)

        elif save_option == "Create New File":
            # --- START: MODIFICATION (Add folder selector) ---
            # เพิ่ม st.radio นี้เข้าไปแทน:
            selected_target_folder = st.radio(
                "Save location:",
                options=["resources", "pageobjects"],
                index=0, # ค่าเริ่มต้นคือ 'resources'
                key="kw_new_file_folder_radio",
                horizontal=True
            )
            # --- END: MODIFICATION ---

            safe_kw_name = re.sub(r'[^a-zA-Z0-9_-]', '_', kw['name']).lower()
            default_filename = f"kw_{safe_kw_name}.resource"

            new_file_name = st.text_input(
                "New file name:",
                value=default_filename,
                key="kw_new_filename"
            )

            if st.button("📝 Create and Save File", key="create_kw_btn"):
                if not new_file_name.endswith(('.robot', '.resource')):
                    st.error("File name must end with .robot or .resource")
                else:
                    # (โค้ด full_content = textwrap.dedent(...) เหมือนเดิม)
                    full_content = textwrap.dedent(f"""
*** Settings ***
# This file might need other resources, e.g.
# Resource    commonkeywords.resource
# Resource    ../pageobjects/your_locators.robot

*** Keywords ***

# --- START: Generated by Keyword Factory ---
# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{script_code}

# ---  END: Generated by Keyword Factory  ---
""")
                    # --- START: MODIFICATION (Use selected folder) ---
                    # แก้ไขบรรทัด save_dir ให้ใช้ค่าจาก st.radio
                    save_dir = os.path.join(project_path, selected_target_folder)
                    # --- END: MODIFICATION ---
                    
                    os.makedirs(save_dir, exist_ok=True)
                    full_path = os.path.join(save_dir, new_file_name)

                    success = create_new_robot_file(full_path, full_content)
                    if success:
                        st.success(f"Successfully created file at `{os.path.relpath(full_path, project_path)}`")
                        # Rescan project to show new file in sidebar
                        st.session_state.project_structure = scan_robot_project(project_path)
                        st.rerun()
                    else:
                        st.error("Failed to create the file.")


    # ======= RENDER DIALOGS =======
    # Check session state and render dialogs if needed
    if st.session_state.get('show_kw_factory_fill_form_dialog'):
        render_kw_factory_fill_form_dialog()
    
    if st.session_state.get('show_kw_factory_verify_detail_dialog'):
        render_kw_factory_verify_detail_dialog()


# ======= REUSABLE STEP CARD (ADAPTED FROM ui_crud.py) =======
def render_step_card_compact_for_kw(step, index, keyword_id, steps_list, indent_level=0): # Added indent_level
    """
    Displays a compact step card inside the keyword editor.
    (Adapted from ui_crud.py, incorporates Output Vars UI, Suggestions, Indent)
    """
    ws_state = st.session_state.studio_workspace
    kw = kw_manager.get_keyword(keyword_id) # Get current keyword data
    total_steps = len(steps_list)

    # --- Edit Mode State ---
    edit_mode_key = f'kw_edit_mode_{step["id"]}'
    edit_mode = st.session_state.get(edit_mode_key, False)

    # Apply margin based on indent level
    margin_left = indent_level * 30 # 30px per indent level
    st.markdown(f"<div class='step-card' style='margin-left: {margin_left}px;'>", unsafe_allow_html=True)

    # === CARD HEADER ===
    with st.container():
        kw_col, btn_col = st.columns([0.6, 0.4], vertical_alignment="center")

        with kw_col:
            st.markdown(f"""
            <div class='step-header-content'>
                <span class='step-number-inline'>{index + 1}</span>
                <div class='step-keyword'>
                    <div class='step-keyword-label'>KEYWORD</div>
                    <div class='step-keyword-name'>{step.get('keyword', 'N/A')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with btn_col:
            # --- Toolbar Code ---
            st.markdown("<div class='step-card-toolbar-wrapper'>", unsafe_allow_html=True)
            action_cols = st.columns([1, 1, 1, 1, 1], gap="small")

            with action_cols[0]: # Up
                is_first = (index == 0)
                if st.button("⬆️", key=f"up_kw_{keyword_id}_{step['id']}", help="Move Up", use_container_width=True, disabled=is_first):
                    kw_manager.move_step(keyword_id, step['id'], 'up')
                    st.rerun()

            with action_cols[1]: # Down
                is_last = (index == total_steps - 1)
                if st.button("⬇️", key=f"down_kw_{keyword_id}_{step['id']}", help="Move Down", use_container_width=True, disabled=is_last):
                    kw_manager.move_step(keyword_id, step['id'], 'down')
                    st.rerun()

            with action_cols[2]: # Edit/Save
                edit_icon = "💾" if edit_mode else "✏️"
                edit_help = "Save Changes" if edit_mode else "Edit Step"
                if st.button(edit_icon, key=f"edit_kw_{keyword_id}_{step['id']}", help=edit_help, use_container_width=True):
                    st.session_state[edit_mode_key] = not edit_mode
                    if st.session_state[edit_mode_key]:
                        # Preload data for editing
                        st.session_state[f"edit_kw_select_kw_{step['id']}"] = step.get('keyword', '')
                        st.session_state[f"edit_temp_args_kw_{step['id']}"] = step.get('args', {}).copy()
                        st.session_state[f"prev_kw_kw_{step['id']}"] = step.get('keyword', '')
                    st.rerun()

            with action_cols[3]: # Duplicate
                if st.button("📋", key=f"copy_kw_{keyword_id}_{step['id']}", help="Duplicate", use_container_width=True):
                    # Find current step index to insert after
                    current_index = -1
                    for i, s in enumerate(steps_list):
                         if s['id'] == step['id']:
                              current_index = i
                              break
                    if current_index != -1:
                         new_step = step.copy()
                         new_step['id'] = str(uuid.uuid4())
                         # kw['steps'] is the list in the session state
                         kw['steps'].insert(current_index + 1, new_step)
                         st.rerun()

            with action_cols[4]: # Delete
                if st.button("🗑️", key=f"del_kw_{keyword_id}_{step['id']}", help="Delete", use_container_width=True):
                    kw_manager.delete_step(keyword_id, step['id'])
                    # Clear edit state if deleting the step being edited
                    if edit_mode_key in st.session_state: del st.session_state[edit_mode_key]
                    # Could clear temp args too, but rerun handles it
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    # === CARD BODY (Conditional Rendering) ===
    if not edit_mode:
        # --- Display Mode ---
        all_args = step.get('args', {})

        if all_args:
            # --- Call the NEW grid formatter ---
            args_grid_html = format_args_as_multiline_string(all_args)

            if args_grid_html:
                 # --- [NEW] Simplified container div, styling is now IN the grid_html ---
                 st.markdown(
                     f"""<div style='
                             padding: 0.5rem 0.5rem 0.6rem 0.5rem; /* Reduced padding */
                             margin-top: 0.3rem;
                             border-top: 1px solid rgba(110, 118, 129, 0.2);
                         '>
                         {args_grid_html}
                         </div>""",
                     unsafe_allow_html=True
                 )

        # Display CSV/API Config
        if step.get('type') == 'csv_import' and step.get('config'):
            cfg = step['config']
            st.caption(f"🗃️ **Data Source:** {cfg.get('ds_name', '?')}")
        elif step.get('type') == 'api_call':
            st.caption(f"🌐 **API Service Call**")

        # Display Output Variable Info (Read-Only)
        output_config = step.get('output_variable', {})
        if output_config.get('enabled') and output_config.get('name'):
             scope = output_config.get('scope', 'Test')
             var_name = output_config.get('name')
             st.caption(f"↪️ **Output:** Set {scope} Variable `${{{var_name}}}`")


    else: # Edit Mode
        st.markdown("<div class='crud-edit-section'>", unsafe_allow_html=True)

        # Load keywords if not already loaded
        if 'categorized_keywords' not in ws_state:
            all_keywords_list = ws_state.get('keywords', [])
            if all_keywords_list:
                # Assuming categorize_keywords is imported correctly
                ws_state['categorized_keywords'] = categorize_keywords(all_keywords_list)

        categorized_keywords = ws_state.get('categorized_keywords', {})
        # --- Add IF/END to selectable keywords ---
        control_flow_kws = [
             {'name': 'IF Condition', 'args': [{'name': '${condition}', 'default': ''}], 'doc': 'Starts a conditional block.'},
             {'name': 'ELSE IF Condition', 'args': [{'name': '${condition}', 'default': ''}], 'doc': 'Starts an else-if block.'},
             {'name': 'ELSE', 'args': [], 'doc': 'Starts an else block.'},
             {'name': 'END', 'args': [], 'doc': 'Ends a conditional block.'}
        ]
        all_kws = control_flow_kws + [kw for kws in categorized_keywords.values() for kw in kws]
        all_kw_names = [kw['name'] for kw in all_kws]
        # --- End Add IF/END ---

        st.markdown("##### 🔧 Edit Step")

        # Keyword Selector
        edit_kw_state_key = f"edit_kw_select_kw_{step['id']}"
        # Ensure state exists before accessing index
        if edit_kw_state_key not in st.session_state:
             st.session_state[edit_kw_state_key] = step.get('keyword', '')

        selected_kw_name = st.selectbox(
            "Select Keyword",
            all_kw_names,
            index=all_kw_names.index(st.session_state[edit_kw_state_key]) if st.session_state[edit_kw_state_key] in all_kw_names else 0,
            key=edit_kw_state_key
        )
        selected_kw = next((kw for kw in all_kws if kw['name'] == selected_kw_name), None)

        temp_args_key = f"edit_temp_args_kw_{step['id']}"

        # Check if keyword changed, reset temp args
        if st.session_state.get(edit_kw_state_key) != st.session_state.get(f"prev_kw_kw_{step['id']}", ""):
            st.session_state[temp_args_key] = {} # Reset args
            if selected_kw_name == 'IF Condition':
                 st.session_state[temp_args_key]['condition'] = step.get('args', {}).get('condition', '') # Keep existing condition if switching back to IF
            elif selected_kw_name == 'ELSE IF Condition': # <-- เพิ่ม
                 st.session_state[temp_args_key]['condition'] = step.get('args', {}).get('condition', '') # Keep existing condition
            elif selected_kw and selected_kw.get('args'):
                # Pre-fill with default values for the NEW keyword
                for arg_item in selected_kw.get('args', []):
                    # Ensure arg_item is a dict
                    arg_info = arg_item if isinstance(arg_item, dict) else {'name': str(arg_item)}
                    clean_arg_name = arg_info.get('name', '').strip('${}')
                    if clean_arg_name:
                        st.session_state[temp_args_key][clean_arg_name] = arg_info.get('default', '')
            # Update previous keyword tracking
            st.session_state[f"prev_kw_kw_{step['id']}"] = selected_kw_name
            # Don't rerun here, let rendering continue

        # --- Render Inputs based on Selected Keyword ---
        if selected_kw_name == 'IF Condition':
             st.markdown("**Condition:**")
             condition_val = st.text_input("Condition Expression",
                                           value=st.session_state.get(temp_args_key, {}).get('condition', ''),
                                           key=f"kw_if_condition_{step['id']}",
                                           placeholder="e.g., ${status} == 'OK' or ${count} > 0")
             st.session_state[temp_args_key]['condition'] = condition_val # Update temp state

        elif selected_kw_name == 'ELSE IF Condition': # <-- เพิ่ม
             st.markdown("**Condition:**")
             condition_val = st.text_input("Condition Expression",
                                           value=st.session_state.get(temp_args_key, {}).get('condition', ''),
                                           key=f"kw_if_condition_{step['id']}", # ใช้ key เดียวกับ IF ได้
                                           placeholder="e.g., ${status} == 'PENDING'")
             st.session_state[temp_args_key]['condition'] = condition_val

        elif selected_kw_name in ['END', 'ELSE']: # <-- เพิ่ม 'ELSE'
             st.info(f"Marks the start of an '{selected_kw_name}' block. No arguments needed.")
             st.session_state[temp_args_key] = {} # Ensure args are empty

        elif selected_kw and selected_kw.get('args'): # Normal Keyword Arguments
            st.markdown("**Arguments:**")
            for arg_item in selected_kw.get('args', []):
                # Ensure arg_item is a dict
                arg_info = arg_item if isinstance(arg_item, dict) else {'name': str(arg_item), 'default': ''}
                clean_arg_name = arg_info.get('name', '').strip('${}')
                if not clean_arg_name: continue
                arg_info['name'] = clean_arg_name # Use cleaned name for rendering

                # Read current value from temp state
                current_value = st.session_state.get(temp_args_key, {}).get(clean_arg_name, arg_info.get('default', ''))
                input_key = f"kw_factory_edit_{step['id']}_{clean_arg_name}"

                # Use the common renderer
                rendered_value = render_argument_input(
                    arg_info,
                    ws_state,
                    input_key,
                    current_value=current_value,
                    selected_kw_name=selected_kw.get('name') # <--- Pass selected keyword name
                )

                # --- Argument Suggestion Logic ---
                show_suggestion = False
                suggested_arg_name = None
                if clean_arg_name in ['value', 'exp_value', 'text']:
                     # Determine correct widget key based on input type
                     widget_key_base = input_key
                     widget_key = widget_key_base # Default for simple inputs
                     if arg_info.get('name') in ARGUMENT_PRESETS and ARGUMENT_PRESETS[arg_info['name']].get('type') == 'select_or_input':
                          if st.session_state.get(f"{widget_key_base}_select") == "📝 Other (custom)":
                               widget_key = f"{widget_key_base}_custom"
                          else:
                               widget_key = f"{widget_key_base}_select"
                     elif any(s in arg_info.get('name').lower() for s in ['locator', 'field', 'button', 'element', 'menu', 'header', 'body', 'theader', 'tbody']):
                           widget_key = f"{widget_key_base}_locator_select"
                     # === ADDED FIX for Menu Locator ===
                     elif 'menu' in arg_info.get('name').lower():
                         # Menu uses two keys, we don't suggest for it
                         pass
                     # ==================================
                     else: # Fallback for text input
                           widget_key = f"{widget_key_base}_default_text"

                     current_rendered_value = st.session_state.get(widget_key, '') if widget_key else '' # Check if widget_key exists

                     if current_rendered_value and not (isinstance(current_rendered_value, str) and current_rendered_value.startswith('${') and current_rendered_value.endswith('}')):
                          locator_arg_value = None
                          temp_step_args_sugg = st.session_state.get(temp_args_key, {})
                          if 'locator_field' in temp_step_args_sugg: locator_arg_value = temp_step_args_sugg['locator_field']
                          elif 'locator' in temp_step_args_sugg: locator_arg_value = temp_step_args_sugg['locator']

                          if locator_arg_value:
                               locator_name_str = locator_arg_value if isinstance(locator_arg_value, str) else locator_arg_value.get('name', '')
                               if locator_name_str:
                                    suggested_arg_name = generate_arg_name_from_locator(locator_name_str)
                                    if suggested_arg_name: show_suggestion = True

                if show_suggestion and suggested_arg_name:
                     suggestion_key = f"suggest_arg_{step['id']}_{clean_arg_name}"
                     sugg_cols = st.columns([1, 5])
                     with sugg_cols[0]:
                          if st.button(f"💡 `{suggested_arg_name}`?", key=suggestion_key, help=f"Use {suggested_arg_name}"):
                               st.session_state[temp_args_key][clean_arg_name] = suggested_arg_name
                               # Add to main args list if needed
                               kw_args_list_sugg = kw.get('args', [])
                               if not any(a['name'] == suggested_arg_name for a in kw_args_list_sugg):
                                    kw_args_list_sugg.append({'name': suggested_arg_name, 'default': ''})
                                    kw['args'] = sorted(kw_args_list_sugg, key=lambda x: x['name'])
                               st.rerun()
                # --- End Suggestion ---

                # --- Update temp state from widget (copied logic with MENU FIX) ---
                final_value = None
                is_locator_arg = any(s in clean_arg_name.lower() for s in ['locator', 'field', 'button', 'element', 'menu', 'header', 'body', 'theader', 'tbody'])

                if is_locator_arg:
                    if 'menu' in clean_arg_name.lower():
                        selected_main = st.session_state.get(f"{input_key}_main_menu_select", '')
                        selected_sub = st.session_state.get(f"{input_key}_sub_menu_select", '')

                        parts = []
                        if selected_main:
                            parts.append(f"${{mainmenu}}[{selected_main}]")
                        # เพิ่ม Submenu เฉพาะถ้า Keyword เป็น Go to SUBMENU name
                        kw_name_lower = str(selected_kw.get('name', '')).lower()
                        if selected_sub and 'go to submenu name' in kw_name_lower:
                            parts.append(f"${{submenu}}[{selected_sub}]")

                        final_value = "    ".join(parts) # Join with 4 spaces
                    else:
                        final_value = st.session_state.get(f"{input_key}_locator_select", current_value)

                elif clean_arg_name in ARGUMENT_PRESETS:
                    config = ARGUMENT_PRESETS[clean_arg_name]
                    preset_type = config.get('type')
                    if preset_type == "select_or_input":
                        selected = st.session_state.get(f"{input_key}_select")
                        if selected == "📝 Other (custom)":
                            final_value = st.session_state.get(f"{input_key}_custom", current_value)
                        else:
                            final_value = selected if selected is not None else current_value # Handle None case
                    elif preset_type == "boolean":
                         final_value = 'true' if st.session_state.get(input_key, False) else 'false'
                    else: # select, text etc.
                        final_value = st.session_state.get(input_key, current_value)
                else: # Pattern or default text
                    matched = False
                    for pattern_key, pattern_config in ARGUMENT_PATTERNS.items():
                        if pattern_key in clean_arg_name.lower():
                            final_value = st.session_state.get(input_key, current_value)
                            matched = True
                            break
                    if not matched:
                        final_value = st.session_state.get(f"{input_key}_default_text", current_value)

                # Store the determined value back into the temporary state
                st.session_state[temp_args_key][clean_arg_name] = final_value if final_value is not None else current_value


        elif not selected_kw and selected_kw_name not in ['IF Condition', 'ELSE IF Condition', 'ELSE', 'END']:
            st.warning("Selected keyword definition not found.")

        # --- Output Variable UI ---
        # (Only show if not IF, ELSE IF, ELSE, or END step)
        if selected_kw_name not in ['IF Condition', 'ELSE IF Condition', 'ELSE', 'END']:
            st.markdown("---")
            st.markdown("**⚙️ Output Variable (Optional)**")
            st.caption("Set the result of this step to a variable.")

            output_enabled_key = f"kw_output_enabled_{step['id']}"
            output_name_key = f"kw_output_name_{step['id']}"
            output_scope_key = f"kw_output_scope_{step['id']}"
            output_source_key = f"kw_output_source_{step['id']}" # Key for value source dropdown
            output_detail_key = f"kw_output_source_detail_{step['id']}" # Key for detail input/select

            output_config = step.get('output_variable', {})
            is_enabled_default = output_config.get('enabled', False)
            var_name_default = output_config.get('name', '')
            scope_default = output_config.get('scope', 'Test')
            source_default = output_config.get('value_source', "Default Return Value (${OUTPUT})") # Default source
            detail_default = output_config.get('source_detail', '') # Default detail

            is_enabled = st.checkbox("Set output variable", value=is_enabled_default, key=output_enabled_key)

            if is_enabled:
                col_name, col_scope = st.columns(2)
                with col_name:
                    var_name = st.text_input("Variable Name", value=var_name_default, key=output_name_key, placeholder="e.g., MY_RESULT")
                with col_scope:
                    scope_options = ["Test", "Suite", "Global"]
                    scope_index = scope_options.index(scope_default) if scope_default in scope_options else 0
                    selected_scope = st.selectbox("Scope", options=scope_options, index=scope_index, key=output_scope_key)

                # Value Source Selection
                value_source_options = ["Default Return Value (${OUTPUT})"]
                step_type = step.get('type')
                step_args_output = st.session_state.get(temp_args_key, {}) # Use temp args for options
                if step_type == 'api_call':
                    value_source_options.extend(["API Response Body (${GLOBAL_RESPONSE_JSON})", "API Response JSON Path"])
                if step_args_output: # Check if there are args in temp state
                    value_source_options.append("Specific Argument Value")
                value_source_options.append("Manual Value/Variable")

                # Ensure default is valid
                if source_default not in value_source_options: source_default = value_source_options[0]
                source_index = value_source_options.index(source_default)

                selected_source = st.selectbox("Value Source", options=value_source_options, index=source_index, key=output_source_key)

                # Detail Input/Select based on source
                source_detail_input = None
                if selected_source == "Specific Argument Value":
                    arg_names_output = list(step_args_output.keys())
                    detail_index_output = arg_names_output.index(detail_default) if detail_default in arg_names_output else 0
                    source_detail_input = st.selectbox("Select Argument", options=arg_names_output, index=detail_index_output, key=output_detail_key)
                elif selected_source == "API Response JSON Path":
                    source_detail_input = st.text_input("JSON Path", value=detail_default, key=output_detail_key, placeholder="e.g., data.id")
                elif selected_source == "Manual Value/Variable":
                    source_detail_input = st.text_input("Enter Value or Variable", value=detail_default, key=output_detail_key, placeholder="e.g., ${PREV_VAR}")

                # Update step data immediately
                step['output_variable'] = {
                    'enabled': True,
                    'name': var_name,
                    'scope': selected_scope,
                    'value_source': selected_source,
                    'source_detail': source_detail_input if source_detail_input is not None else ''
                }
            else: # If checkbox is unchecked
                step['output_variable'] = {'enabled': False}
        # --- End Output Variable UI ---


        # --- Save/Cancel Buttons ---
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Save Changes", key=f"save_edit_kw_{step['id']}", use_container_width=True, type="primary"):
                # Read final args from temp state
                final_args = st.session_state.get(temp_args_key, {}).copy()

                # Special handling for IF/ELSE IF/ELSE/END
                if selected_kw_name == 'IF Condition':
                     final_args = {'condition': final_args.get('condition', '')}
                elif selected_kw_name == 'ELSE IF Condition': # <-- เพิ่ม
                     final_args = {'condition': final_args.get('condition', '')}
                elif selected_kw_name in ['END', 'ELSE']: # <-- เพิ่ม 'ELSE'
                      final_args = {} # Ensure END/ELSE have no args saved

                updated_data = {
                    "keyword": selected_kw_name,
                    "args": final_args,
                    "output_variable": step.get('output_variable', {'enabled': False}) # Read updated output config
                }
                kw_manager.update_step(keyword_id, step['id'], updated_data)

                # Cleanup session state keys associated with this step's edit mode
                keys_to_delete = [edit_mode_key, temp_args_key, f"prev_kw_kw_{step['id']}", edit_kw_state_key]
                keys_to_delete.extend([f"kw_if_condition_{step['id']}", output_enabled_key, output_name_key, output_scope_key, output_source_key, output_detail_key])
                # Add argument widget keys (more complex to find all, might skip some for simplicity)
                if selected_kw and selected_kw.get('args'):
                     for arg_item in selected_kw.get('args', []):
                           clean_arg_name = arg_item.get('name', '').strip('${}')
                           if clean_arg_name:
                                keys_to_delete.append(f"kw_factory_edit_{step['id']}_{clean_arg_name}")
                                # === ADDED FIX for Menu Locator Keys ===
                                keys_to_delete.extend([
                                     f"kw_factory_edit_{step['id']}_{clean_arg_name}_select",
                                     f"kw_factory_edit_{step['id']}_{clean_arg_name}_custom",
                                     f"kw_factory_edit_{step['id']}_{clean_arg_name}_locator_select",
                                     f"kw_factory_edit_{step['id']}_{clean_arg_name}_default_text",
                                     f"kw_factory_edit_{step['id']}_{clean_arg_name}_main_menu_select", # New
                                     f"kw_factory_edit_{step['id']}_{clean_arg_name}_sub_menu_select"   # New
                                ])
                                # =======================================

                for key in keys_to_delete:
                    if key in st.session_state:
                        try: # Wrap in try-except in case key was already deleted
                             del st.session_state[key]
                        except KeyError:
                             pass

                st.rerun()

        with col2:
            if st.button("❌ Cancel", key=f"cancel_edit_kw_{step['id']}", use_container_width=True):
                 # Just toggle edit mode off and cleanup keys
                 st.session_state[edit_mode_key] = False
                 keys_to_delete = [temp_args_key, f"prev_kw_kw_{step['id']}", edit_kw_state_key]
                 keys_to_delete.extend([f"kw_if_condition_{step['id']}", output_enabled_key, output_name_key, output_scope_key, output_source_key, output_detail_key])
                 # Add argument widget keys (similar to save)
                 if selected_kw and selected_kw.get('args'):
                      for arg_item in selected_kw.get('args', []):
                            clean_arg_name = arg_item.get('name', '').strip('${}')
                            if clean_arg_name:
                                 keys_to_delete.append(f"kw_factory_edit_{step['id']}_{clean_arg_name}")
                                 # === ADDED FIX for Menu Locator Keys ===
                                 keys_to_delete.extend([
                                      f"kw_factory_edit_{step['id']}_{clean_arg_name}_select",
                                      f"kw_factory_edit_{step['id']}_{clean_arg_name}_custom",
                                      f"kw_factory_edit_{step['id']}_{clean_arg_name}_locator_select",
                                      f"kw_factory_edit_{step['id']}_{clean_arg_name}_default_text",
                                      f"kw_factory_edit_{step['id']}_{clean_arg_name}_main_menu_select", # New
                                      f"kw_factory_edit_{step['id']}_{clean_arg_name}_sub_menu_select"   # New
                                 ])
                                 # =======================================

                 for key in keys_to_delete:
                      if key in st.session_state:
                           try:
                                del st.session_state[key]
                           except KeyError:
                                pass
                 st.rerun()


        st.markdown("</div>", unsafe_allow_html=True) # End crud-edit-section

    st.markdown("</div>", unsafe_allow_html=True) # End step-card


# ======= DIALOG: Add Step =======
# (No changes needed here for IF/END, assuming IF/END are added to keyword list source)
def render_kw_factory_add_step_dialog():
    ws_state = st.session_state.studio_workspace
    context = st.session_state.get('kw_factory_add_dialog_context', {})
    keyword_id = context.get("key")

    def add_step_to_kw(context_dict, new_step):
        kw_id = context_dict.get("key")
        if kw_id:
            # Handle IF/END default args if needed when adding
            if new_step.get('keyword') == 'IF Condition' and 'args' not in new_step:
                 new_step['args'] = {'condition': ''}
            elif new_step.get('keyword') == 'END':
                 new_step['args'] = {} # Ensure END has empty args
            kw_manager.add_step(kw_id, new_step)

    # Filter generated keywords
    all_generated_kw_names = [kw['name'] for kw in kw_manager.get_all_keywords()]
    def kw_factory_filter(keyword):
        kw_name = keyword.get('name', '')
        # Exclude API/CSV and self-generated keywords
        if kw_name.lower().startswith(('import datasource', 'request service')): return False
        # Allow IF/END even though they might appear "generated"
        if kw_name in ['IF Condition', 'ELSE IF Condition', 'ELSE', 'END']: return True
        if kw_name in all_generated_kw_names: return False
        return True

    render_add_step_dialog_base(
        dialog_state_key='show_kw_factory_add_dialog',
        context_state_key='kw_factory_add_dialog_context',
        selected_kw_state_key='selected_kw_kw_factory',
        add_step_callback=add_step_to_kw,
        ws_state=ws_state,
        title=f"Add Step to Keyword",
        keyword_filter_func=kw_factory_filter,
        search_state_key="kw_search_dialog_kw_factory",
        recently_used_state_key="recently_used_keywords_kw_factory",
        # Optionally add IF/END to a specific category in the dialog:
        # custom_categories={"Control Flow": ["IF Condition", "END"]}
    )

# ======= DIALOG: Add API/CSV Step =======
@st.dialog("Add Data Source or API Step", width="large")
def render_kw_factory_api_csv_step_dialog():
    """
    Dialog to add CSV/API steps to a custom keyword.
    (Copied from ui_crud.py)
    """
    ws_state = st.session_state.studio_workspace
    context = st.session_state.get('kw_factory_api_csv_dialog_context', {})
    keyword_id = context.get("key") # This is the keyword_id
    from .ui_crud import extract_csv_datasource_keywords

    if not keyword_id:
        st.error("Error: Keyword context not found.")
        st.session_state['show_kw_factory_api_csv_dialog'] = False
        st.rerun()
        return

    def close_dialog():
        st.session_state['show_kw_factory_api_csv_dialog'] = False
        if 'kw_factory_api_csv_dialog_context' in st.session_state:
            del st.session_state['kw_factory_api_csv_dialog_context']
        st.rerun()
    
    if st.button("← Back to Editor"):
        close_dialog()

    st.info(f"Adding step to: **{kw_manager.get_keyword(keyword_id).get('name', '...')}**")
    
    st.markdown("### 🗃️ Available Data Sources")
    csv_keywords = extract_csv_datasource_keywords(ws_state)
    if not csv_keywords:
        st.caption("⚠️ No Data Sources found.")
    else:
        for ds_name, ds_info in csv_keywords.items():
            if st.button(f"📊 {ds_name}", key=f"kw_csv_{ds_name}", use_container_width=True):
                keyword_name = f"Import DataSource {ds_name}"
                new_step = {
                    "id": str(uuid.uuid4()), "keyword": keyword_name, "args": {},
                    "type": "csv_import", "config": ds_info
                }
                kw_manager.add_step(keyword_id, new_step)
                close_dialog()

    st.markdown("---")
    st.markdown("### 🌐 Available API Services")
    api_services = ws_state.get('api_services', [])
    if not api_services:
        st.caption("⚠️ No API Services found.")
    else:
        for service in api_services:
            service_name = service.get('service_name', 'Untitled')
            if st.button(f"🔗 {service_name}", key=f"kw_api_{service['id']}", use_container_width=True):
                keyword_name = f"Request {service_name.replace('_', ' ').title()}"
                args = service.get('analyzed_fields', {})
                required_args = [name for name, data in args.items() if data.get('is_argument')]
                default_args = {'headeruser': '${USER_ADMIN}', 'headerpassword': '${PASSWORD_ADMIN}'}
                default_args.update({arg: '' for arg in required_args})
                new_step = {
                    "id": str(uuid.uuid4()), "keyword": keyword_name, "args": default_args,
                    "type": "api_call"
                }
                kw_manager.add_step(keyword_id, new_step)
                close_dialog()

# ======= DIALOG: Quick Fill Form =======
@st.dialog("Quick Template: Fill Form", width="large", dismissible=False)
def render_kw_factory_fill_form_dialog():
    render_simplified_fill()

@st.dialog("Quick Template: Verify Detail", width="large", dismissible=False)
def render_kw_factory_verify_detail_dialog():
    """
    Quick Verify Detail Dialog - Using simplified version
    """
    render_simplified_verify()