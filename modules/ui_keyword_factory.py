"""
UI Module for the Keyword Factory Tab
(Incorporating Argument Manager, Output Variables, Suggestions, Reordering)
"""
import streamlit as st
import uuid
import json
import os
import re
import textwrap
from . import kw_manager
from .session_manager import get_clean_locator_name
from .ui_common import render_argument_input, ARGUMENT_PRESETS, ARGUMENT_PATTERNS # Import PATTERNS
from .dialog_commonkw import render_add_step_dialog_base
from .file_manager import append_robot_content_intelligently, create_new_robot_file, scan_robot_project # Added scan_robot_project
from .test_flow_manager import categorize_keywords
from datetime import datetime
from .utils import scan_steps_for_variables, generate_arg_name_from_locator, format_args_as_string, format_args_as_multiline_string  # Added format_args_as_string
from .utils import FILL_FORM_DEFAULTS, VERIFY_FORM_DEFAULTS

# ======= ENTRY POINT FUNCTION =======
def render_keyword_factory_tab():
    """
    Main entry point for the Keyword Factory Tab
    """
    # Use styles from ui_crud, they are very similar
    from .crud_generator.ui_crud import inject_hybrid_css # Keep this specific import if styles are there
    from .ui_common import extract_csv_datasource_keywords
    inject_hybrid_css()

    kw_manager.initialize_workspace()
    ws = kw_manager._get_workspace()

    # --- Main View Switching (List vs. Editor) ---
    if ws.get('active_keyword_id') is None:
        render_keyword_list_view(ws)
    else:
        render_keyword_editor_view(ws)

# ======= LIST VIEW =======
def render_keyword_list_view(ws):
    """
    Displays the list of all created keywords and a button to create new ones.
    """
    st.markdown("<h3 style='font-size: 1.6rem;'>🏭 Keyword Factory</h3>", unsafe_allow_html=True)
    st.caption("Create and manage reusable, high-level keywords from smaller steps.")

    if st.button("➕ Create New Keyword", width='content', type="secondary"):
        kw_manager.create_new_keyword()
        st.rerun()

    st.markdown("---")

    all_keywords = kw_manager.get_all_keywords()

    if not all_keywords:
        st.info("No keywords created yet. Click 'Create New Keyword' to start.")
        return

    st.markdown("#### Manage Existing Keywords")

    for kw in all_keywords:
        with st.container(border=True):
            cols = st.columns([4, 1, 1])
            with cols[0]:
                st.markdown(f"**{kw.get('name', 'Untitled')}**")
                # Display arguments correctly from list of dicts
                args_display = [f"{arg['name']}" + (f"={arg['default']}" if arg.get('default') else "")
                                for arg in kw.get('args', [])]
                st.caption(f"Arguments: {', '.join(args_display) or 'None'}")
                st.caption(f"Steps: {len(kw.get('steps', []))}")
            with cols[1]:
                if st.button("✏️ Edit", key=f"edit_kw_{kw['id']}", use_container_width=True):
                    kw_manager.set_active_keyword(kw['id'])
                    st.rerun()
            with cols[2]:
                if st.button("🗑️ Delete", key=f"del_kw_{kw['id']}", use_container_width=True):
                    kw_manager.delete_keyword(kw['id'])
                    st.rerun()

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
                    st.session_state[f"kw_doc_{keyword_id}"],
                    # Args removed from here
                    st.session_state[f"kw_tags_{keyword_id}"]
                )
            )
            # ***** End Keyword Name *****

            st.markdown("---") # เส้นคั่น

            # ***** Argument Manager UI *****
            st.markdown("**🧩 Keyword Arguments (Auto-Detected)**")
            st.caption("Select variables found in steps to make them arguments.")

            steps = kw.get('steps', [])

            # 1. สแกนหาตัวแปร
            detected_vars = scan_steps_for_variables(steps)

            # 2. จัดการ State สำหรับ Arguments ที่เลือก (List of Dicts)
            if 'args' not in kw or not isinstance(kw['args'], list):
                kw['args'] = []

            # อ่าน List of Dicts ปัจจุบัน (ลำดับมีความสำคัญ)
            current_ordered_args = kw.get('args', [])
            selected_arg_names = {arg['name'] for arg in current_ordered_args}

            if not detected_vars and not kw['args']:
                st.caption("No potential arguments detected in steps yet.")
            else:
                 # --- แก้ไข Header Columns ---
                header_cols = st.columns([1, 4, 3, 1.5]) # ปรับความกว้างคอลัมน์ 4 สำหรับ Order
                with header_cols[0]: st.markdown("**Use**")
                with header_cols[1]: st.markdown("**Variable**")
                with header_cols[2]: st.markdown("**Default Value**")
                with header_cols[3]: st.markdown("**Order**")

                # --- แสดงตัวแปรที่ *ไม่ได้* ถูกเลือกก่อน (ไม่มีปุ่ม Order) ---
                detected_but_not_selected = sorted([
                    var_name for var_name in detected_vars
                    if var_name not in selected_arg_names
                ])

                if detected_but_not_selected:
                    st.caption("_Variables detected in steps but not used as arguments:_")
                    for var_name in detected_but_not_selected:
                        row_cols = st.columns([1, 4, 3, 1.5])
                        with row_cols[0]:
                            new_selection = st.checkbox(" ", value=False, key=f"arg_select_{keyword_id}_{var_name}", label_visibility="collapsed")
                        with row_cols[1]:
                            st.code(var_name, language='robotframework')
                        # คอลัมน์ Default และ Order ว่างเปล่า
                        if new_selection: # ถ้าผู้ใช้เพิ่งติ๊กเลือก
                            # เพิ่มเข้า List (จะถูกเรียงใหม่รอบหน้า)
                            current_ordered_args.append({'name': var_name, 'default': ''})
                            kw['args'] = current_ordered_args # อัปเดต state หลักทันที
                            st.rerun() # Rerun ทันที

                    st.markdown("---") # คั่นระหว่างกลุ่ม

                # --- วนลูปสร้าง UI สำหรับ Arguments ที่ถูกเลือก *ตามลำดับปัจจุบัน* ---
                if current_ordered_args: # แสดงเฉพาะถ้ามี args ที่เลือกแล้ว
                    st.caption("_Selected keyword arguments (order matters):_")
                num_selected_args = len(current_ordered_args)
                temp_new_args_list = [] # เก็บค่า default ที่อาจมีการแก้ไข

                for idx, arg_config in enumerate(current_ordered_args):
                    var_name = arg_config['name']
                    row_cols = st.columns([1, 4, 3, 1.5])

                    with row_cols[0]:
                        is_selected = True
                        new_selection = st.checkbox(" ", value=is_selected, key=f"arg_select_{keyword_id}_{var_name}", label_visibility="collapsed")
                    with row_cols[1]:
                        st.code(var_name, language='robotframework')
                    with row_cols[2]:
                        default_val = st.text_input("Default",
                                                    value=arg_config.get('default', ''),
                                                    key=f"arg_default_{keyword_id}_{var_name}",
                                                    label_visibility="collapsed",
                                                    placeholder="Optional (e.g., ${EMPTY})")
                        temp_new_args_list.append({'name': var_name, 'default': default_val})
                    with row_cols[3]:
                        btn_cols = st.columns([1, 1])
                        with btn_cols[0]:
                            up_disabled = (idx == 0)
                            if st.button("⬆️", key=f"arg_up_{keyword_id}_{var_name}", disabled=up_disabled, use_container_width=True, help="Move Up"):
                                current_ordered_args.insert(idx - 1, current_ordered_args.pop(idx))
                                kw['args'] = current_ordered_args
                                st.rerun()
                        with btn_cols[1]:
                            down_disabled = (idx == num_selected_args - 1)
                            if st.button("⬇️", key=f"arg_down_{keyword_id}_{var_name}", disabled=down_disabled, use_container_width=True, help="Move Down"):
                                current_ordered_args.insert(idx + 1, current_ordered_args.pop(idx))
                                kw['args'] = current_ordered_args
                                st.rerun()

                # --- อัปเดต kw['args'] หลัง Loop (จัดการ Default Value และ bỏ tick) ---
                final_args_list = []
                temp_defaults = {item['name']: item['default'] for item in temp_new_args_list}

                for arg_config in current_ordered_args:
                    var_name = arg_config['name']
                    if st.session_state.get(f"arg_select_{keyword_id}_{var_name}", False):
                        arg_config['default'] = temp_defaults.get(var_name, '')
                        final_args_list.append(arg_config)

                if kw.get('args', []) != final_args_list:
                    kw['args'] = final_args_list
            # ***** End Argument Manager UI *****

            st.markdown("---") # เส้นคั่น

        # --- 2. Quick Templates ---
        with st.expander("⚡Quick Step Templates", expanded=False):
            st.info("Add multiple steps at once based on locators.")
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                if st.button("✏️ Quick Fill Form", use_container_width=True):
                    st.session_state.show_kw_factory_fill_form_dialog = True
                    st.session_state['kw_factory_add_dialog_context'] = {"key": keyword_id}
                    st.rerun()
            with t_col2:
                if st.button("🔍 Quick Verify Detail", use_container_width=True):
                    st.session_state.show_kw_factory_verify_dialog = True
                    st.session_state['kw_factory_add_dialog_context'] = {"key": keyword_id}
                    st.rerun()

        # --- 3. Step Editor ---
        st.markdown("#### 👣 Keyword Steps")
        steps = kw.get('steps', [])
        indent_level = 0 # Track indent level for IF/END display

        if not steps:
            st.info("No steps yet. Click 'Add Step' below.")
        else:
            # Use specific step card renderer for keyword factory
            for i, step in enumerate(steps):
                # Pass indent_level to the renderer
                render_step_card_compact_for_kw(step, i, keyword_id, steps, indent_level)

                # Update indent level for the next step
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
    """
    [MODIFIED] Lets user select multiple locators and edit arguments in a table view
    to generate 'Fill in data form' steps.
    """
    ws_state = st.session_state.studio_workspace
    context = st.session_state.get('kw_factory_add_dialog_context', {})
    keyword_id = context.get("key") # This is the keyword_id

    # --- Session State Keys ---
    locators_state_key = f"kw_factory_fill_locators_{keyword_id}"
    custom_args_state_key = f"kw_factory_fill_custom_args_{keyword_id}"

    # Initialize state if not present
    if locators_state_key not in st.session_state:
        st.session_state[locators_state_key] = []
    if custom_args_state_key not in st.session_state:
        st.session_state[custom_args_state_key] = {} # Dict: {loc_name: {arg: value}}

    # Import defaults (assuming it's in utils.py now)
    try:
        from .utils import FILL_FORM_DEFAULTS
    except ImportError:
        st.error("Error: FILL_FORM_DEFAULTS not found in utils.py!")
        # Define fallback defaults here if needed
        FILL_FORM_DEFAULTS = { 'is_switch_type': False, 'is_checkbox_type': False, 'select_attribute': 'label', 'is_ant_design': False }

    # --- Cleanup Function ---
    def cleanup_and_close():
        keys_to_delete = [locators_state_key, custom_args_state_key]
        # Also delete individual widget keys if necessary (though rerun might handle it)
        selected_locs = st.session_state.get(locators_state_key, [])
        for loc_name in selected_locs:
            loc_key_prefix = f"fill_arg_{keyword_id}_{loc_name.replace('LOCATOR_', '')}"
            keys_to_delete.extend([f"{loc_key_prefix}_switch", f"{loc_key_prefix}_check", f"{loc_key_prefix}_attr", f"{loc_key_prefix}_ant"])

        for key in keys_to_delete:
            if key in st.session_state:
                try: del st.session_state[key]
                except KeyError: pass
        st.session_state.show_kw_factory_fill_form_dialog = False
        st.rerun()

    # --- Back Button ---
    if st.button("← Back to Editor", key="back_fill_form_dialog"):
        cleanup_and_close()

    if not keyword_id:
        st.error("Error: Keyword context not found.")
        st.session_state.show_kw_factory_fill_form_dialog = False
        st.rerun()
        return

    st.markdown("#### ✏️ Select Fields and Configure Fill Steps")
    st.caption("Select locators, then customize arguments for each generated step in the table below.")

    all_locators = ws_state.get('locators', [])
    if not all_locators:
        st.warning("No locators found in 'Assets' tab. Please add locators first.")
        # Render cancel button even if no locators
        st.markdown("---")
        if st.button("❌ Cancel", use_container_width=True):
            cleanup_and_close()
        return # Stop rendering the rest

    # --- Locator Multiselect ---
    available_locator_names = [loc['name'] for loc in all_locators]
    # Read current selection from state BEFORE rendering multiselect
    current_selection_in_state = st.session_state.get(locators_state_key, [])

    selected_locators_names_widget = st.multiselect(
        "Select Locators",
        options=available_locator_names,
        default=current_selection_in_state,
        format_func=get_clean_locator_name,
        key=f"multiselect_{locators_state_key}" # Unique key for the widget
    )

    # Check if the multiselect value differs from the state, then update state and rerun
    if selected_locators_names_widget != current_selection_in_state:
        st.session_state[locators_state_key] = selected_locators_names_widget
        # Clean up custom args state for locators that were unselected
        current_custom_args = st.session_state.get(custom_args_state_key, {})
        new_custom_args = {loc: args for loc, args in current_custom_args.items() if loc in selected_locators_names_widget}
        st.session_state[custom_args_state_key] = new_custom_args
        st.rerun() # Rerun immediately after selection change

    # Use the selection from the state for the rest of the logic
    selected_locators_names = st.session_state.get(locators_state_key, [])

    st.markdown("---")

    # --- [NEW] Argument Customization Table ---
    if selected_locators_names:
        st.markdown("**Customize Step Arguments:**")

        # --- Header Row ---
        header_cols = st.columns([3, 1, 1.3, 1, 1, 2]) # Adjust ratios
        with header_cols[0]: st.caption("**Locator**")
        with header_cols[1]: st.caption("**Ant?**")     # Moved Ant Design here
        with header_cols[2]: st.caption("**Sel attr.**") # Renamed for brevity
        with header_cols[3]: st.caption("**Checkbox?**")
        with header_cols[4]: st.caption("**Switch?**")
        with header_cols[5]: st.caption("**Locator Switch Checked?**") # Added new column
        st.divider()

        # --- Data Rows ---
        current_custom_args = st.session_state.get(custom_args_state_key, {})
        # Create a temporary dict to store widget values during rendering
        widget_values_temp = {}

        for loc_name in selected_locators_names:
            # Initialize custom args for this locator if needed (same as before)
            if loc_name not in current_custom_args:
                current_custom_args[loc_name] = FILL_FORM_DEFAULTS.copy()

            loc_args = current_custom_args[loc_name] # Get current settings
            loc_key_prefix = f"fill_arg_{keyword_id}_{loc_name.replace('LOCATOR_', '')}" # Unique prefix

            # New column order: Locator, Sel attr., Checkbox?, Ant?, Switch?, Switch Checked?
            row_cols = st.columns([3, 1, 1.3, 1, 1, 2]) # Use new ratios

            with row_cols[0]: # Locator
                st.markdown(f"`{get_clean_locator_name(loc_name)}`")

            with row_cols[2]: # Select Attribute
                attr_options = ["label", "value", "text", "index"]
                current_attr = loc_args.get('select_attribute', FILL_FORM_DEFAULTS['select_attribute'])
                try:
                    attr_index = attr_options.index(current_attr)
                except ValueError:
                    attr_index = 0 # Default if value invalid

                selected_attr = st.selectbox(" ", # Label in header
                                options=attr_options,
                                index=attr_index,
                                key=f"{loc_key_prefix}_attr",
                                label_visibility="collapsed")
                widget_values_temp.setdefault(loc_name, {})['select_attribute'] = selected_attr

            with row_cols[3]: # Checkbox?
                is_check = st.checkbox(" ",
                            value=loc_args.get('is_checkbox_type', FILL_FORM_DEFAULTS['is_checkbox_type']),
                            key=f"{loc_key_prefix}_check",
                            label_visibility="collapsed")
                widget_values_temp.setdefault(loc_name, {})['is_checkbox_type'] = is_check

            with row_cols[1]: # Ant Design?
                is_ant = st.checkbox(" ",
                           value=loc_args.get('is_ant_design', FILL_FORM_DEFAULTS['is_ant_design']),
                           key=f"{loc_key_prefix}_ant",
                           label_visibility="collapsed")
                widget_values_temp.setdefault(loc_name, {})['is_ant_design'] = is_ant

            with row_cols[4]: # Switch?
                is_switch = st.checkbox(" ",
                             value=loc_args.get('is_switch_type', FILL_FORM_DEFAULTS['is_switch_type']),
                             key=f"{loc_key_prefix}_switch",
                             label_visibility="collapsed")
                widget_values_temp.setdefault(loc_name, {})['is_switch_type'] = is_switch

            with row_cols[5]: # Locator Switch Checked? (Changed to Text Input)
                current_lsc_value = loc_args.get(
                    'locator_switch_checked',
                    FILL_FORM_DEFAULTS.get('locator_switch_checked', '${EMPTY}') # Get default from constants
                )
                # Ensure the default displayed is exactly '${EMPTY}' if that's the current value
                display_value = '${EMPTY}' if current_lsc_value == '${EMPTY}' else current_lsc_value

                switch_checked_input = st.text_input(" ", # Label in header
                                     value=display_value,
                                     key=f"{loc_key_prefix}_switch_checked_text", # New key
                                     placeholder="${EMPTY}, ${True}, ...",
                                     label_visibility="collapsed")
                # Store the raw text input value
                widget_values_temp.setdefault(loc_name, {})['locator_switch_checked'] = switch_checked_input

        # --- Update Session State AFTER rendering all widgets ---
        # Compare temporary values with current state to see if an update is needed
        if widget_values_temp != current_custom_args:
             st.session_state[custom_args_state_key] = widget_values_temp
             # Optional: Rerun if you want changes reflected immediately (might feel slow)
             # st.rerun()

        st.markdown("---")

    # --- Add/Cancel Buttons ---
    col_add, col_cancel = st.columns(2)
    with col_add:
        # Disable button if no locators are selected
        add_disabled = not selected_locators_names
        if st.button("✅ Add Fill Steps", type="primary", use_container_width=True, disabled=add_disabled):
            # Read the final custom args directly from session state
            custom_args_for_selected = st.session_state.get(custom_args_state_key, {})

            # Prepare data for the manager function
            locators_with_custom_args = {
                loc_name: custom_args_for_selected.get(loc_name, FILL_FORM_DEFAULTS.copy())
                for loc_name in selected_locators_names # Use state variable here
            }

            # Call the manager function
            kw_manager.add_quick_fill_form_steps_with_custom_args(keyword_id, locators_with_custom_args)

            # Cleanup state and close dialog
            cleanup_and_close()

    with col_cancel:
        if st.button("❌ Cancel", use_container_width=True):
            cleanup_and_close()

@st.dialog("Quick Template: Verify Detail", width="large", dismissible=False)
def render_kw_factory_verify_detail_dialog():
    """
    [MODIFIED] Lets user select multiple locators and edit arguments in a table view
    to generate 'Verify data form' steps.
    """
    ws_state = st.session_state.studio_workspace
    context = st.session_state.get('kw_factory_add_dialog_context', {}) # Re-use context key? Verify if this is correct
    keyword_id = context.get("key") # This is the keyword_id

    # --- Session State Keys ---
    locators_state_key = f"kw_factory_verify_locators_{keyword_id}"
    custom_args_state_key = f"kw_factory_verify_custom_args_{keyword_id}"

    # Initialize state if not present
    if locators_state_key not in st.session_state:
        st.session_state[locators_state_key] = []
    if custom_args_state_key not in st.session_state:
        st.session_state[custom_args_state_key] = {} # Dict: {loc_name: {arg: value}}

    # --- Cleanup Function ---
    def cleanup_and_close():
        keys_to_delete = [locators_state_key, custom_args_state_key]
        # Cleanup widget keys (optional but good practice)
        selected_locs = st.session_state.get(locators_state_key, [])
        for loc_name in selected_locs:
            loc_key_prefix = f"verify_arg_{keyword_id}_{loc_name.replace('LOCATOR_', '')}"
            keys_to_delete.extend([
                f"{loc_key_prefix}_assert", f"{loc_key_prefix}_exp_val", f"{loc_key_prefix}_attr",
                f"{loc_key_prefix}_ignore", f"{loc_key_prefix}_ant", f"{loc_key_prefix}_switch",
                f"{loc_key_prefix}_sw_checked", f"{loc_key_prefix}_skip"
            ])

        for key in keys_to_delete:
            if key in st.session_state:
                try: del st.session_state[key]
                except KeyError: pass
        st.session_state.show_kw_factory_verify_dialog = False
        st.rerun()

    # --- Back Button ---
    if st.button("← Back to Editor", key="back_verify_dialog"):
        cleanup_and_close()

    if not keyword_id:
        st.error("Error: Keyword context not found.")
        st.session_state.show_kw_factory_verify_dialog = False
        st.rerun()
        return

    st.markdown("#### 🔍 Select Fields and Configure Verify Steps")
    st.caption("Select locators, then customize arguments for each generated step.")

    all_locators = ws_state.get('locators', [])
    if not all_locators:
        st.warning("No locators found in 'Assets' tab. Please add locators first.")
        st.markdown("---")
        if st.button("❌ Cancel", use_container_width=True):
            cleanup_and_close()
        return

    # --- Locator Multiselect ---
    available_locator_names = [loc['name'] for loc in all_locators]
    current_selection_in_state = st.session_state.get(locators_state_key, [])

    selected_locators_names_widget = st.multiselect(
        "Select Locators",
        options=available_locator_names,
        default=current_selection_in_state,
        format_func=get_clean_locator_name,
        key=f"multiselect_{locators_state_key}"
    )

    if selected_locators_names_widget != current_selection_in_state:
        st.session_state[locators_state_key] = selected_locators_names_widget
        current_custom_args = st.session_state.get(custom_args_state_key, {})
        new_custom_args = {loc: args for loc, args in current_custom_args.items() if loc in selected_locators_names_widget}
        st.session_state[custom_args_state_key] = new_custom_args
        st.rerun()

    selected_locators_names = st.session_state.get(locators_state_key, [])

    st.markdown("---")

    # --- [NEW] Argument Customization Table ---
    if selected_locators_names:
        st.markdown("**Customize Step Arguments:**")

        # --- Header Row ---
        # Locator | Assertion | Exp. Value | Sel Attr | Ignore? | Ant? | Switch? | Sw Checked | Skip?
        header_cols = st.columns([3.5, 2, 1.5, 1, 1, 1, 2, 1]) # Adjust ratios
        with header_cols[0]: st.caption("**Locator**")
        with header_cols[1]: st.caption("**Assertion**")
        with header_cols[2]: st.caption("**Sel Attr.**")
        with header_cols[3]: st.caption("**Ignore Case**")
        with header_cols[4]: st.caption("**Ant?**")
        with header_cols[5]: st.caption("**Switch?**")
        with header_cols[6]: st.caption("**locator Switch Checked**") # Changed label slightly
        st.divider()

        # --- Data Rows ---
        current_custom_args = st.session_state.get(custom_args_state_key, {})
        widget_values_temp = {} # Temporary dict for widget values

        # Define options for dropdowns
        assertion_options = ["equal", "should be", "contains", "not contains", "inequal"]
        attr_options = ["label", "value"]

        for loc_name in selected_locators_names:
            if loc_name not in current_custom_args:
                current_custom_args[loc_name] = VERIFY_FORM_DEFAULTS.copy()
                # Auto-generate expected value variable only when adding locator initially
                from .utils import generate_arg_name_from_locator # Import here if needed
                arg_var = generate_arg_name_from_locator(loc_name)
                if not arg_var:
                     clean_loc = loc_name.replace('LOCATOR_', '').lower()
                     arg_var = f"${{{clean_loc or 'expected'}}}"
                current_custom_args[loc_name]['exp_value'] = arg_var # Set default expected value

            loc_args = current_custom_args[loc_name]
            loc_key_prefix = f"verify_arg_{keyword_id}_{loc_name.replace('LOCATOR_', '')}"

            row_cols = st.columns([3.5, 2, 1.5, 1, 1, 1, 2, 1]) # Use same ratios

            with row_cols[0]: # Locator
                st.markdown(f"`{get_clean_locator_name(loc_name)}`")

            with row_cols[1]: # Assertion
                current_assert = loc_args.get('assertion', 'equal') # <-- แก้ไขตรงนี้
                try: assert_index = assertion_options.index(current_assert)
                except ValueError: assert_index = 0 # Default to 'equal' index
                selected_assert = st.selectbox(" ", options=assertion_options, index=assert_index, key=f"{loc_key_prefix}_assert", label_visibility="collapsed")
                widget_values_temp.setdefault(loc_name, {})['assertion'] = selected_assert

            with row_cols[2]: # Select Attribute
                current_attr = loc_args.get('select_attribute', VERIFY_FORM_DEFAULTS['select_attribute'])
                try: attr_index = attr_options.index(current_attr)
                except ValueError: attr_index = 0
                selected_attr = st.selectbox(" ", options=attr_options, index=attr_index, key=f"{loc_key_prefix}_attr", label_visibility="collapsed")
                widget_values_temp.setdefault(loc_name, {})['select_attribute'] = selected_attr

            with row_cols[3]: # Ignore Case?
                is_ignore = st.checkbox(" ", value=loc_args.get('ignorcase', VERIFY_FORM_DEFAULTS['ignorcase']), key=f"{loc_key_prefix}_ignore", label_visibility="collapsed")
                widget_values_temp.setdefault(loc_name, {})['ignorcase'] = is_ignore

            with row_cols[4]: # Ant Design?
                is_ant = st.checkbox(" ", value=loc_args.get('antdesign', VERIFY_FORM_DEFAULTS['antdesign']), key=f"{loc_key_prefix}_ant", label_visibility="collapsed")
                widget_values_temp.setdefault(loc_name, {})['antdesign'] = is_ant

            with row_cols[5]: # Is Switch Type?
                is_switch = st.checkbox(" ", value=loc_args.get('is_switchtype', VERIFY_FORM_DEFAULTS['is_switchtype']), key=f"{loc_key_prefix}_switch", label_visibility="collapsed")
                widget_values_temp.setdefault(loc_name, {})['is_switchtype'] = is_switch

            with row_cols[6]: # Locator Switch Checked?
                current_lsc_value = loc_args.get('locator_switch_checked', VERIFY_FORM_DEFAULTS['locator_switch_checked'])
                display_value = '${EMPTY}' if current_lsc_value == '${EMPTY}' else current_lsc_value
                sw_checked_input = st.text_input(" ", value=display_value, key=f"{loc_key_prefix}_sw_checked", placeholder="${EMPTY}, ${True}, ...", label_visibility="collapsed")
                widget_values_temp.setdefault(loc_name, {})['locator_switch_checked'] = sw_checked_input

        # --- Update Session State AFTER rendering ---
        # Read the current full state from session state
        state_needs_update = False
        current_state_args = st.session_state.get(custom_args_state_key, {})

        # Iterate through the temporary widget values we collected
        for loc_name, new_widget_vals in widget_values_temp.items():
            # Get the existing arguments for this locator from the current state
            existing_loc_args = current_state_args.get(loc_name, {})

            # Preserve the existing exp_value if it exists
            preserved_exp_value = existing_loc_args.get('exp_value')

            # Update the existing args with the new widget values
            updated_loc_args = existing_loc_args.copy() # Start with existing
            updated_loc_args.update(new_widget_vals)    # Overwrite with new widget values

            # Put the preserved exp_value back if it existed and wasn't somehow in new_widget_vals
            if preserved_exp_value is not None and 'exp_value' not in new_widget_vals:
                updated_loc_args['exp_value'] = preserved_exp_value
            # Or ensure exp_value from defaults is there if it was missing entirely
            elif 'exp_value' not in updated_loc_args:
                 # Re-generate if completely missing (shouldn't happen often here)
                 from .utils import generate_arg_name_from_locator
                 arg_var = generate_arg_name_from_locator(loc_name)
                 if not arg_var:
                      clean_loc = loc_name.replace('LOCATOR_', '').lower()
                      arg_var = f"${{{clean_loc or 'expected'}}}"
                 updated_loc_args['exp_value'] = arg_var


            # Check if the updated args are different from the ones currently in state
            if updated_loc_args != existing_loc_args:
                current_state_args[loc_name] = updated_loc_args # Update the main dictionary
                state_needs_update = True

        # Write the potentially modified dictionary back to session state ONLY if changes occurred
        if state_needs_update:
            st.session_state[custom_args_state_key] = current_state_args
            # st.rerun() # Optional: Rerun if you want immediate reflection of updates

        st.markdown("---")

    # --- Add/Cancel Buttons ---
    col_add, col_cancel = st.columns(2)
    with col_add:
        add_disabled = not selected_locators_names
        if st.button("✅ Add Verify Steps", type="primary", use_container_width=True, disabled=add_disabled):
            custom_args_for_selected = st.session_state.get(custom_args_state_key, {})

            locators_with_custom_args = {
                loc_name: custom_args_for_selected.get(loc_name, VERIFY_FORM_DEFAULTS.copy())
                for loc_name in selected_locators_names
            }

            # Call the NEW manager function
            kw_manager.add_quick_verify_steps_with_custom_args(keyword_id, locators_with_custom_args)

            cleanup_and_close()

    with col_cancel:
        if st.button("❌ Cancel", use_container_width=True):
            cleanup_and_close()