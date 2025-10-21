"""
UI Module for the CRUD Generator Tab
(Complete Code - Hybrid Style with Top-Tabs)
(Version 3.10 - CSV Step Dialog now stores configuration)
"""
import streamlit as st
import uuid
import numpy as np
import json
import os 
import re
from . import manager
from ..session_manager import get_clean_locator_name
from ..ui_common import render_argument_input
from ..test_flow_manager import categorize_keywords
from ..dialog_commonkw import render_add_step_dialog_base

# ======= ENTRY POINT FUNCTION =======
def render_crud_generator_tab():
    """
    Main entry point สำหรับ CRUD Generator Tab
    """
    inject_hybrid_css()
    render_crud_generator_tab_improved()

    # --- Dialog Handlers ---
    if st.session_state.get('show_crud_add_dialog'):
        render_crud_add_step_dialog()
    if st.session_state.get('show_fill_form_dialog'):
        render_fill_form_dialog()
    if st.session_state.get('show_verify_detail_dialog'):
        render_verify_detail_dialog()
    # --- Updated Dialog Handler Check ---
    if st.session_state.get('show_api_csv_dialog'):
        render_api_csv_step_dialog() # Ensure this function is called


# ======= NEW HELPER FUNCTION (V3.7) =======
def render_generator_expander_content(ws):
    """Renders the content for the 'Auto-Generate Template' expander."""

    # Determine button label based on state
    if st.session_state.crud_template_generated:
        button_label = f"🔄 Regenerate {ws.get('active_action')} Template"
    else:
        button_label = f"🚀 Generate {ws.get('active_action')} Template"

    ws['active_action'] = st.selectbox(
        "Action Type",
        ["Create", "Update", "Delete"],
        index=["Create", "Update", "Delete"].index(ws.get('active_action', 'Create')),
        key="selectbox_generator_action"
    )
    
    # Show helpful info based on selected action
    action = ws.get('active_action')
    if action == 'Create':
        st.info("💡 **Create Flow:** Navigate → Click New → Fill Form → Save → Verify New Item")
    elif action == 'Update':
        st.info("💡 **Update Flow:** Navigate → Search → Click Edit → Modify Form → Save → Verify Updated Item")
    elif action == 'Delete':
        st.info("💡 **Delete Flow:** Navigate → Search → Click Delete → Confirm → Verify Item Removed")

    if st.button(button_label, type="primary", use_container_width=True, key="btn_generate_template_main"):
        action = ws.get('active_action')
        
        if action == 'Create':
            manager.generate_create_template()
            st.session_state.crud_template_generated = True
            st.success("✅ Create template generated!")
            st.rerun()
        elif action == 'Update':
            manager.generate_update_template()
            st.session_state.crud_template_generated = True
            st.success("✅ Update template generated!")
            st.rerun()
        elif action == 'Delete':
            manager.generate_delete_template() # <-- เรียกฟังก์ชันใหม่
            st.session_state.crud_template_generated = True
            st.success("✅ Delete template generated!")
            st.rerun()
        else:
            st.warning(f"Template for '{action}' not yet implemented.")


# ======= MAIN UI FUNCTION (REVISED V3.8) =======
def render_crud_generator_tab_improved():
    """
    Main function - REVISED (V3.8)
    - Added Config Expander with Data Source and API linking
    """

# ✅ ป้องกัน workspace ถูก reinit ซ้ำทุก rerun
    if "studio_workspace" not in st.session_state:
        manager.initialize_workspace()

    ws = manager._get_workspace()
    ws_state = st.session_state.studio_workspace

    # ✅ ตรวจสอบและสร้างโครงสร้าง steps หากยังไม่มี
    if "steps" not in ws:
        ws["steps"] = {}

    for section in [
        "suite_setup", "test_setup", "action_list", "action_detail",
        "verify_list", "verify_detail", "suite_teardown", "test_teardown"
    ]:
        if section not in ws["steps"]:
            ws["steps"][section] = []

    # 1. --- State flag ---
    if 'crud_template_generated' not in st.session_state:
        st.session_state.crud_template_generated = False
        if any(len(ws['steps'][key]) > 0 for key in ws['steps']):
             st.session_state.crud_template_generated = True


    # ======= แก้ตรงนี้: Header แยก 2 ฝั่ง =======
    header_left, header_right = st.columns([0.6, 0.4], gap="large")
    
    with header_left:
        st.markdown("<h3 style='font-size: 1.6rem;'>🎯 CRUD Test Generator</h3>", unsafe_allow_html=True)
        st.caption("Organize your test by phases: Setup → Actions → Verification → Teardown")
    
    with header_right:
        st.markdown("<h3 style='font-size: 1.6rem;'>🚀 Live Code Preview</h3>", unsafe_allow_html=True)
        st.caption("Updates automatically as you edit")
    
    # สร้าง 2 คอลัมน์ (Editor ซ้าย, Preview ขวา)
    left_editor, right_preview = st.columns([0.6, 0.4], gap="large")

    with left_editor:
        # --- 3. Generator in an Expander ---
        is_expanded = not st.session_state.crud_template_generated
        with st.expander("🤖 Auto-Generate Template", expanded=is_expanded):
            render_generator_expander_content(ws)

        # --- 4. Main Editor (Config + Tabs) ---
        if st.session_state.crud_template_generated:

            # --- 4.1 NEW (V3.8): Config Expander ---
            with st.expander("⚙️ Test Case Configuration", expanded=True):
                render_config_section_v3_8(ws, ws_state)

            st.markdown("---")

            # --- 4.2 Tabs (Top Navigation) ---
            tab_setup, tab_actions, tab_verify, tab_teardown = st.tabs([
                "🛠️ Phase 1: Setup",
                "⚡ Phase 2: Actions & Fill Form",
                "✅ Phase 3: Verification",
                "🧹 Phase 4: Teardown"
            ])

            with tab_setup:
                render_setup_phase(ws)
            with tab_actions:
                render_actions_phase(ws)
            with tab_verify:
                render_verification_phase(ws)
            with tab_teardown:
                render_teardown_phase(ws)

        else:
            if not is_expanded:
                st.info("Click '🤖 Auto-Generate Template' above to begin editing your test flow.")

    with right_preview:
        render_sticky_preview(ws)

# ======= PHASE RENDERERS (Sub-Navigation) =======
# (These functions remain largely unchanged but include the Add API/CSV button)

def render_setup_phase(ws):
    """Phase 1: Setup - (REVISED) Only 2 sub-sections"""
    st.markdown("### 🛠️ Setup Phase")

    def set_setup_sub(sub_name):
        st.session_state.setup_active_sub = sub_name

    if 'setup_active_sub' not in st.session_state:
        st.session_state.setup_active_sub = 'suite_setup'
    active_sub = st.session_state.setup_active_sub

    sub_nav_col1, sub_nav_col2 = st.columns(2)
    with sub_nav_col1:
        st.button("⚙️ Suite Setup", use_container_width=True,
            type="primary" if active_sub == 'suite_setup' else "secondary",
            on_click=set_setup_sub, args=('suite_setup',))
    with sub_nav_col2:
        st.button("🔧 Test Setup", use_container_width=True,
            type="primary" if active_sub == 'test_setup' else "secondary",
            on_click=set_setup_sub, args=('test_setup',))

    with st.container(border=True):
        if active_sub == 'suite_setup':
            render_suite_setup_section(ws)
        elif active_sub == 'test_setup':
            render_test_setup_section(ws)

def render_actions_phase(ws):
    """Phase 2: Actions - 3 sub-sections"""
    st.markdown("### ⚡ Actions Phase")

    def set_actions_sub(sub_name):
        st.session_state.actions_active_sub = sub_name

    if 'actions_active_sub' not in st.session_state:
        st.session_state.actions_active_sub = 'list'
    active_sub = st.session_state.actions_active_sub

    sub_col1, sub_col2, sub_col3 = st.columns(3)
    with sub_col1:
        st.button("📝 List Page Actions", use_container_width=True,
            type="primary" if active_sub == 'list' else "secondary",
            on_click=set_actions_sub, args=('list',))
    with sub_col2:
        st.button("✏️ Fill Form", use_container_width=True,
            type="primary" if active_sub == 'form' else "secondary",
            on_click=set_actions_sub, args=('form',))
    with sub_col3:
        st.button("🔘 Detail Actions", use_container_width=True,
            type="primary" if active_sub == 'detail' else "secondary",
            on_click=set_actions_sub, args=('detail',))

    with st.container(border=True):
        if active_sub == 'list':
            render_list_actions_section(ws)
        elif active_sub == 'form':
            render_fill_form_section(ws)
        elif active_sub == 'detail':
            render_detail_actions_section(ws)

def render_verification_phase(ws):
    """Phase 3: Verification - 2 sub-sections"""
    st.markdown("### ✅ Verification Phase")

    def set_verify_sub(sub_name):
        st.session_state.verify_active_sub = sub_name

    if 'verify_active_sub' not in st.session_state:
        st.session_state.verify_active_sub = 'list'
    active_sub = st.session_state.verify_active_sub

    sub_col1, sub_col2 = st.columns(2)
    with sub_col1:
        st.button("📊 Verify Main List", use_container_width=True,
            type="primary" if active_sub == 'list' else "secondary",
            on_click=set_verify_sub, args=('list',))
    with sub_col2:
        st.button("🔍 Verify Detail", use_container_width=True,
            type="primary" if active_sub == 'detail' else "secondary",
            on_click=set_verify_sub, args=('detail',))

    with st.container(border=True):
        if active_sub == 'list':
            render_verify_list_section(ws)
        elif active_sub == 'detail':
            render_verify_detail_section(ws)

def render_teardown_phase(ws):
    """Phase 4: Teardown - Simple, no sub-sections"""
    st.markdown("### 🧹 Teardown Phase")
    st.info("💡 Clean up after test execution (Logout, Close Browser)")

    with st.container(border=True):
        render_teardown_section(ws)


# ======= INDIVIDUAL SECTION RENDERERS =======

# --- Helper to open API/CSV dialog ---
def _open_api_csv_dialog(section_key):
    st.session_state['show_api_csv_dialog'] = True
    st.session_state['api_csv_dialog_context'] = {"key": section_key}
    if 'csv_api_dialog_selection' in st.session_state:
        del st.session_state['csv_api_dialog_selection'] # Clear previous selection
    st.rerun()

def render_config_section_v3_8(ws, ws_state):
    """Config Section - Simplified (Only Test Case Name and Tags)"""
    
    # Auto-update test case name based on action type
    action = ws.get('active_action', 'Create')
    default_name = f"TC_{action}_Item"
    
    # If test case name is still default from different action, update it
    current_name = ws.get('test_case_name', default_name)
    if current_name in ['TC_Create_Item', 'TC_Update_Item', 'TC_Delete_Item', 'TC_Create_New_Item']:
        ws['test_case_name'] = default_name

    ws['test_case_name'] = st.text_input(
        "Test Case Name",
        value=ws.get('test_case_name', default_name),
        help="ตั้งชื่อ Test Case ให้สื่อความหมาย"
    )

    # Auto-update tags based on action type
    default_tags = [action, 'Smoke']
    if 'tags' not in ws or not ws['tags']:
        ws['tags'] = default_tags
    
    tags_input = st.text_input(
        "Tags (comma-separated)",
        value=", ".join(ws.get('tags', default_tags))
    )
    ws['tags'] = [tag.strip() for tag in tags_input.split(',') if tag.strip()]

# --- Sections updated to include the "Add API/CSV Step" button ---
def render_suite_setup_section(ws):
    """Suite Setup Section"""
    st.markdown("#### ⚙️ Suite Setup Steps")
    st.caption("Runs ONCE before all test cases (e.g., Initialize System, Login)")

    steps = ws['steps']['suite_setup']

    if not steps:
        st.info("No steps yet. Click 'Add Step' below or use Generate Template.")
    else:
        for i, step in enumerate(steps):
            render_step_card_compact(step, i, 'suite_setup', ws)

    # --- Add buttons in columns ---
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add Step", use_container_width=True, key="crud_add_suite_setup"):
            st.session_state['show_crud_add_dialog'] = True
            st.session_state['crud_add_dialog_context'] = {"key": "suite_setup"}
            st.rerun()
    with col2:
        if st.button("⚡ Add API/CSV Step", use_container_width=True, key="crud_add_api_csv_setup"):
            _open_api_csv_dialog("suite_setup")

def render_test_setup_section(ws):
    """Test Setup Section"""
    st.markdown("#### 🔧 Test Setup Steps")
    st.caption("Runs BEFORE EACH test case (usually empty for CRUD)")

    steps = ws['steps']['test_setup']

    if not steps:
        st.info("No test setup steps defined. This is optional.")
    else:
        for i, step in enumerate(steps):
            render_step_card_compact(step, i, 'test_setup', ws)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add Test Setup Step", use_container_width=True, key="add_test_setup"):
            st.session_state['show_crud_add_dialog'] = True
            st.session_state['crud_add_dialog_context'] = {"key": "test_setup"}
            st.rerun()
    with col2:
        if st.button("⚡ Add API/CSV Step", use_container_width=True, key="crud_add_api_csv_test_setup"):
            _open_api_csv_dialog("test_setup")

def render_list_actions_section(ws):
    """List Page Actions Section"""
    st.markdown("#### 📝 Main List Page Actions")
    st.caption("Actions on the list/table page (Search, Click New, etc.)")

    steps = ws['steps']['action_list']

    if not steps:
        st.info("No actions yet. Typically: Search, Click 'New' button")
    else:
        for i, step in enumerate(steps):
            render_step_card_compact(step, i, 'action_list', ws)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add List Action Step", use_container_width=True, key="add_action_list"):
            st.session_state['show_crud_add_dialog'] = True
            st.session_state['crud_add_dialog_context'] = {"key": "action_list"}
            st.rerun()
    with col2:
        if st.button("⚡ Add API/CSV Step", use_container_width=True, key="crud_add_api_csv_action_list"):
            _open_api_csv_dialog("action_list")

def render_fill_form_section(ws):
    """Fill Form Section - Preview Removed"""
    st.markdown("#### ✏️ Fill Form Fields")

    fill_steps = [s for s in ws['steps']['action_detail'] if s['keyword'] == 'Fill in data form']

    col1, col2 = st.columns([0.7, 0.3])
    with col1:
        st.metric("📝 Total Form Fields", len(fill_steps))
    with col2:
        if st.button("⚙️ Manage All", use_container_width=True, type="primary", key="manage_form"):
            st.session_state.show_fill_form_dialog = True
            st.rerun()

    if fill_steps:
        st.caption("Click 'Manage All' to edit all fields at once")

def render_detail_actions_section(ws):
    """Detail Actions Section"""
    st.markdown("#### 🔘 Other Detail Actions")
    st.caption("Actions AFTER filling form (Save, Submit, Click Modal OK)")

    other_steps = [s for s in ws['steps']['action_detail'] if s['keyword'] != 'Fill in data form']

    if not other_steps:
        st.info("No other actions. Typically: Click Save, Click Modal OK")
    else:
        for i, step in enumerate(other_steps):
            render_step_card_compact(step, i, 'action_detail_others', ws)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add Detail Action Step", use_container_width=True, key="add_action_detail"):
            st.session_state['show_crud_add_dialog'] = True
            st.session_state['crud_add_dialog_context'] = {"key": "action_detail"}
            st.rerun()
    with col2:
        if st.button("⚡ Add API/CSV Step", use_container_width=True, key="crud_add_api_csv_action_detail"):
            _open_api_csv_dialog("action_detail")

def render_verify_list_section(ws):
    """Verify Main List Section (Renders steps in order)"""
    st.markdown("#### 📊 Verify Main List/Table")
    st.info("💡 Check if the created item appears in the table")

    steps = ws['steps']['verify_list']

    if not steps:
        st.warning("No table verification steps found. Generate template first.")
    else:
        for i, step in enumerate(steps):
            if step['keyword'] == 'Verify Result of data table':
                with st.expander(f"🔧 Edit Table Verification (Step {i+1})", expanded=True):
                    render_step_toolbar(step, i, 'verify_list', len(steps))
                    render_table_verification_ui(step, ws)
            else:
                render_step_card_compact(step, i, 'verify_list', ws)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add Verification Step", use_container_width=True, key="add_verify_list"):
            st.session_state['show_crud_add_dialog'] = True
            st.session_state['crud_add_dialog_context'] = {"key": "verify_list"}
            st.rerun()
    with col2:
        if st.button("⚡ Add API/CSV Step", use_container_width=True, key="crud_add_api_csv_verify_list"):
            _open_api_csv_dialog("verify_list")

def render_verify_detail_section(ws):
    """Verify Detail Section - Preview Removed"""
    st.markdown("#### 🔍 Verify Detail Page")
    st.info("💡 Check if data in detail page matches what you entered")

    verify_steps = [s for s in ws['steps']['verify_detail'] if s['keyword'] == 'Verify data form']

    col1, col2 = st.columns([0.7, 0.3])
    with col1:
        st.metric("🔍 Fields to Verify", len(verify_steps))
    with col2:
        if st.button("⚙️ Manage All", use_container_width=True, type="primary", key="manage_verify"):
            st.session_state.show_verify_detail_dialog = True
            st.rerun()

    other_steps = [s for s in ws['steps']['verify_detail'] if s['keyword'] != 'Verify data form']
    if other_steps:
        st.markdown("---")
        st.markdown("##### Navigation Steps")
        for i, step in enumerate(other_steps):
            render_step_card_compact(step, i, 'verify_detail_others', ws)

def render_teardown_section(ws):
    """Teardown Section"""
    st.markdown("#### 🧹 Suite Teardown Steps")
    st.caption("Runs ONCE after all tests (Logout, Close Browser)")

    steps = ws['steps']['suite_teardown']

    if not steps:
        st.info("No teardown steps. Typically: Logout, Close All Browsers")
    else:
        for i, step in enumerate(steps):
            render_step_card_compact(step, i, 'suite_teardown', ws)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add Teardown Step", use_container_width=True, key="crud_add_suite_teardown"):
            st.session_state['show_crud_add_dialog'] = True
            st.session_state['crud_add_dialog_context'] = {"key": "suite_teardown"}
            st.rerun()
    with col2:
        if st.button("⚡ Add API/CSV Step", use_container_width=True, key="crud_add_api_csv_suite_teardown"):
            _open_api_csv_dialog("suite_teardown")

    st.markdown("---")
    st.markdown("##### Test Teardown (Optional)")
    st.caption("Runs AFTER EACH test case")

    test_td_steps = ws['steps']['test_teardown']
    if not test_td_steps:
        st.info("No test teardown steps defined.")
    else:
        for i, step in enumerate(test_td_steps):
            render_step_card_compact(step, i, 'test_teardown', ws)

# ======= TOOLBAR HELPER =======
def render_step_toolbar(step, index, section_key, total_steps):
    """Renders the 5-button toolbar for special UI components like expanders"""
    st.markdown("<div class='step-card-toolbar-wrapper'>", unsafe_allow_html=True)
    action_cols = st.columns([1, 1, 1, 1, 1], gap="small")
    with action_cols[0]:
        is_first = (index == 0)
        if st.button("⬆️", key=f"up_{section_key}_{step['id']}", help="Move Up", use_container_width=True, disabled=is_first):
            manager.move_step(section_key, step['id'], 'up')
            st.rerun()
    with action_cols[1]:
        is_last = (index == total_steps - 1)
        if st.button("⬇️", key=f"down_{section_key}_{step['id']}", help="Move Down", use_container_width=True, disabled=is_last):
            manager.move_step(section_key, step['id'], 'down')
            st.rerun()
    with action_cols[2]:
        if st.button("✏️", key=f"edit_{section_key}_{step['id']}", help="Edit", use_container_width=True):
            st.info("Currently editing below.") # Or trigger inline edit if implemented differently
    with action_cols[3]:
        if st.button("📋", key=f"copy_{section_key}_{step['id']}", help="Duplicate", use_container_width=True):
            manager.duplicate_step(section_key, step['id'])
            st.rerun()
    with action_cols[4]:
        if st.button("🗑️", key=f"del_{section_key}_{step['id']}", help="Delete", use_container_width=True):
            manager.delete_step(section_key, step['id'])
            st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


# ======= ARG FORMATTING HELPER =======
def format_args_as_string(args_dict):
    """Helper to format arguments as a simple string for st.caption"""
    if not args_dict:
        return ""
    parts = []
    for k, v in args_dict.items():
        if k == 'assertion_columns': 
            continue # Skip this complex one

        if isinstance(v, dict) and 'name' in v:
            val_str = get_clean_locator_name(v['name'])
        elif v or v is False:
            val_str = str(v)
        else:
            continue # Skip empty/None values

        # ไม่ truncate ค่าแต่ละตัว
        parts.append(f"{k}={val_str}")

    # ไม่ truncate string ทั้งหมด แสดงครบ
    full_str = ", ".join(parts)
    return full_str

# ======= REVISED STEP CARD (V3.6) =======
def render_step_card_compact(step, index, section_key, ws):
    """
    REVISED (V3.11) - Enhanced CSV/API config display
    Displays CSV configuration in caption.
    Inline Editing similar to ui_test_flow.
    """
    real_section_key = section_key
    ws_state = st.session_state.studio_workspace

    # --- Logic to handle 'virtual' section keys ---
    if section_key == 'action_detail_others':
        real_section_key = 'action_detail'
        steps_list_for_display = [s for s in ws['steps']['action_detail'] if s['keyword'] != 'Fill in data form']
    elif section_key == 'verify_detail_others':
        real_section_key = 'verify_detail'
        steps_list_for_display = [s for s in ws['steps']['verify_detail'] if s['keyword'] != 'Verify data form']
    else:
        if real_section_key not in ws['steps']: 
            ws['steps'][real_section_key] = []
        steps_list_for_display = ws['steps'][real_section_key]

    try:
        display_index = next(i for i, s in enumerate(steps_list_for_display) if s['id'] == step['id'])
    except StopIteration:
        display_index = index

    try:
        original_list = ws['steps'][real_section_key]
        real_index = next(i for i, s in enumerate(original_list) if s['id'] == step['id'])
        total_steps_in_original = len(original_list)
    except StopIteration:
        st.error(f"Debug: Step ID {step['id']} not found in original list {real_section_key}")
        real_index = index
        total_steps_in_original = len(original_list) if original_list else 0

    # --- Edit Mode State ---
    edit_mode_key = f'crud_edit_mode_{step["id"]}'
    edit_mode = st.session_state.get(edit_mode_key, False)

    st.markdown("<div class='step-card'>", unsafe_allow_html=True)

    # === CARD HEADER ===
    with st.container():
        kw_col, btn_col = st.columns([0.6, 0.4], vertical_alignment="center")

        with kw_col:
            st.markdown(f"""
            <div class='step-header-content'>
                <span class='step-number-inline'>{display_index + 1}</span>
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
            
            with action_cols[0]:
                is_first = (real_index == 0)
                if st.button("⬆️", key=f"up_{real_section_key}_{step['id']}", help="Move Up", use_container_width=True, disabled=is_first):
                    manager.move_step(real_section_key, step['id'], 'up')
                    st.rerun()
            
            with action_cols[1]:
                is_last = (real_index == total_steps_in_original - 1)
                if st.button("⬇️", key=f"down_{real_section_key}_{step['id']}", help="Move Down", use_container_width=True, disabled=is_last):
                    manager.move_step(real_section_key, step['id'], 'down')
                    st.rerun()
            
            with action_cols[2]:
                edit_icon = "💾" if edit_mode else "✏️"
                edit_help = "Save Changes" if edit_mode else "Edit Step"
                if st.button(edit_icon, key=f"edit_{real_section_key}_{step['id']}", help=edit_help, use_container_width=True):
                    # Toggle edit mode
                    st.session_state[edit_mode_key] = not edit_mode

                    if st.session_state[edit_mode_key]:
                        edit_kw_state_key = f"edit_kw_select_{step['id']}"
                        temp_args_key = f"edit_temp_args_{step['id']}"

                       # --- START FIX ---
                        prev_kw_key = f"prev_kw_{step['id']}" # 1. กำหนดคีย์
                        current_kw = step.get('keyword', '')  # 2. ดึง KW ปัจจุบัน
                          
                        # ✅ เก็บ keyword ปัจจุบัน
                        st.session_state[edit_kw_state_key] = current_kw
                          
                          # 3. (FIX) ตั้งค่า prev_kw ด้วย KW ปัจจุบันทันที
                        st.session_state[prev_kw_key] = current_kw
                          # --- END FIX ---

                         # ✅ Preload arguments เดิมของ step ลงใน temp state ก่อน rerun
                        current_args = step.get('args', {})
                        st.session_state[temp_args_key] = current_args.copy() if current_args else {}

                        # ✅ ไม่ต้องลบ prev_kw หรือ temp_args ออก — ให้คงไว้จนกว่าจะ save หรือ cancel

                        st.rerun()
            
            with action_cols[3]:
                if st.button("📋", key=f"copy_{real_section_key}_{step['id']}", help="Duplicate", use_container_width=True):
                    manager.duplicate_step(real_section_key, step['id'])
                    st.rerun()
            
            with action_cols[4]:
                if st.button("🗑️", key=f"del_{real_section_key}_{step['id']}", help="Delete", use_container_width=True):
                    manager.delete_step(real_section_key, step['id'])
                    st.rerun()
            
            st.markdown("</div>", unsafe_allow_html=True)

    # === CARD BODY (Conditional Rendering) ===
    if not edit_mode:
        # --- Display Mode: Show simple caption ---
        valid_args = {k: v for k, v in step.get('args', {}).items() if (v or v is False)}
        if valid_args:
            args_str = format_args_as_string(valid_args)
            if args_str:
                st.markdown(
                f"<div style='padding: 0.1rem 1rem 0.6rem 1rem; color: #56d364; "
                f"font-size: 0.8rem; font-family: \"SF Mono\", Monaco, monospace; "
                f"line-height: 1.4; margin-top: -0.2rem; word-wrap: break-word; "
                f"white-space: normal; overflow-wrap: break-word;'>{args_str}</div>",
                unsafe_allow_html=True
            )
        
        # --- Display CSV/API Config ---
        if step.get('type') == 'csv_import' and step.get('config'):
            cfg = step['config']
            st.caption(
                f"🗃️ **Data Source:** {cfg.get('ds_name', '?')} "
                f"→ Variable: `{cfg.get('ds_var', '?')}` "
                f"→ Column: `{cfg.get('col_var', '?')}`"
            )
            
            if cfg.get('headers'):
                headers_display = ', '.join(cfg['headers'][:5])
                if len(cfg['headers']) > 5:
                    headers_display += "..."
                st.caption(f"📊 **Columns:** {headers_display}")
        
        elif step.get('type') == 'api_call':
            st.caption(f"🌐 **API Service Call**")

    else:
        # --- Edit Mode: Show inputs ---
        st.markdown("<div class='crud-edit-section'>", unsafe_allow_html=True)

        if 'categorized_keywords' not in ws_state:
            all_keywords_list = ws_state.get('keywords', [])
            if all_keywords_list:
                ws_state['categorized_keywords'] = categorize_keywords(all_keywords_list)

        categorized_keywords = ws_state.get('categorized_keywords', {})
        all_kws = [kw for kws in categorized_keywords.values() for kw in kws]
        all_kw_names = [kw['name'] for kw in all_kws]

        st.markdown("##### 🔧 Edit Step")

        # --- Keyword Selector ---
        current_kw_name = step.get('keyword', '')
        edit_kw_state_key = f"edit_kw_select_{step['id']}"
        if edit_kw_state_key not in st.session_state:
            st.session_state[edit_kw_state_key] = current_kw_name

        selected_kw_name = st.selectbox(
            "Select Keyword",
            all_kw_names,
            index=all_kw_names.index(st.session_state[edit_kw_state_key]) if st.session_state[edit_kw_state_key] in all_kw_names else 0,
            key=edit_kw_state_key
        )
        selected_kw = next((kw for kw in all_kws if kw['name'] == selected_kw_name), None)

        # === ✅ เพิ่ม CSV Quick Insert ตรงนี้ ===
        if selected_kw and selected_kw.get('args'):
            with st.expander("📊 Quick Insert from CSV Data", expanded=False):
                st.caption("Select value and target argument to insert")
                
                csv_keywords = extract_csv_datasource_keywords(ws_state)
                
                if csv_keywords:
                    col_ds, col_row, col_column, col_target = st.columns([2, 1.5, 1.5, 2])
                    
                    with col_ds:
                        quick_ds = st.selectbox(
                            "Data Source",
                            options=list(csv_keywords.keys()),
                            key=f"quick_csv_ds_edit_{step['id']}"
                        )
                    
                    quick_row_val = ""
                    with col_row:
                        quick_row_val = st.text_input(
                            "Row Key",
                            key=f"quick_csv_row_edit_{step['id']}",
                            placeholder="e.g., robotapi"
                        )
                    
                    quick_col = None
                    headers = []
                    if quick_ds:
                        ds_info = csv_keywords.get(quick_ds, {})
                        headers = ds_info.get('headers', [])
                        
                        if headers:
                            with col_column:
                                if len(headers) > 1:
                                    quick_col = st.selectbox(
                                        "Column",
                                        options=headers[1:], 
                                        key=f"quick_csv_col_edit_{step['id']}"
                                    )
                    
                    target_arg = None
                    with col_target:
                        text_args = []
                        for arg_item in selected_kw.get('args', []):
                            arg_name = arg_item.get('name', '').strip('${}')
                            is_locator = any(s in arg_name.lower() for s in ['locator', 'field', 'button', 'element', 'menu'])
                            from ..ui_common import ARGUMENT_PRESETS
                            is_preset = arg_name in ARGUMENT_PRESETS
                            if not is_locator and not is_preset:
                                text_args.append(arg_name)
                        
                        if text_args:
                            target_arg = st.selectbox(
                                "Insert to →",
                                options=text_args,
                                key=f"quick_csv_target_edit_{step['id']}"
                            )
                        else:
                            st.caption("_No text args_")
                    
                    # ✅ แสดงปุ่ม Insert
                    if quick_ds and target_arg:
                        ds_info = csv_keywords.get(quick_ds, {})
                        ds_var = ds_info.get('ds_var', 'DATA')
                        col_var = ds_info.get('col_var', 'COL')
                        
                        insert_syntax = ""
                        if quick_row_val:
                            if len(headers) > 1 and quick_col:
                                insert_syntax = f"${{{ds_var}['{quick_row_val}'][${{{col_var}.{quick_col}}}]}}"
                            else:
                                insert_syntax = f"${{{ds_var}['{quick_row_val}']}}"
                        
                        if st.button("✅ Insert", type="primary", use_container_width=True, 
                                    key=f"quick_csv_insert_btn_edit_{step['id']}"):
                            if not target_arg:
                                st.warning("Please select a target argument 'Insert to →'")
                            elif not quick_row_val:
                                st.warning("Please enter a 'Row Key'")
                            elif insert_syntax:
                                temp_args_key = f"edit_temp_args_{step['id']}"
                                if temp_args_key not in st.session_state:
                                    st.session_state[temp_args_key] = {}
                                
                                # ✅ อัปเดต temp_args_key
                                st.session_state[temp_args_key][target_arg] = insert_syntax
                                
                                # ✅ อัปเดต widget keys ทั้งหมดที่เป็นไปได้
                                base_key = f"crud_edit_{step['id']}_{target_arg}"
                                st.session_state[base_key] = insert_syntax
                                st.session_state[f"{base_key}_default_text"] = insert_syntax
                                
                                st.toast(f"✅ Inserted '{insert_syntax}' into '{target_arg}'", icon="✅")
                                st.rerun()
                else:
                    st.info("No CSV data sources found. Add them in Test Data tab.")
            
            st.markdown("---")

        # --- Argument Inputs (SIMPLIFIED LOGIC) ---
        temp_args_key = f"edit_temp_args_{step['id']}"

        # Initialize temp args ONCE when entering edit mode
        if temp_args_key not in st.session_state or not st.session_state[temp_args_key]:
            st.session_state[temp_args_key] = {}
            if selected_kw and selected_kw.get('args'):
                current_step_args = step.get('args', {})
                for arg_item in selected_kw.get('args', []):
                    clean_arg_name = arg_item.get('name', '').replace('${', '').replace('}', '')
                    arg_info = arg_item.get('info', {})
                    initial_value = current_step_args.get(clean_arg_name, arg_info.get('default', ''))
                    # ✅ ตั้งค่าเริ่มต้นเฉพาะครั้งแรกเท่านั้น
                    st.session_state[temp_args_key][clean_arg_name] = initial_value

        # Check if keyword changed
        if st.session_state.get(edit_kw_state_key) != st.session_state.get(f"prev_kw_{step['id']}", ""):
            # Reset temp args when keyword changes
            st.session_state[temp_args_key] = {}
            if selected_kw and selected_kw.get('args'):
                for arg_item in selected_kw.get('args', []):
                    arg_info = arg_item.copy() if isinstance(arg_item, dict) else {'name': str(arg_item), 'default': ''}
                    clean_arg_name = arg_info.get('name', '').strip('${}')
                    if not clean_arg_name: 
                        continue
                    st.session_state[temp_args_key][clean_arg_name] = arg_info.get('default', '')
            st.session_state[f"prev_kw_{step['id']}"] = selected_kw_name

        # Render argument inputs
        if selected_kw and selected_kw.get('args'):
            st.markdown("**Arguments:**")
            
            for arg_item in selected_kw.get('args', []):
                arg_info = arg_item.copy() if isinstance(arg_item, dict) else {'name': str(arg_item), 'default': ''}
                clean_arg_name = arg_info.get('name', '').strip('${}')
                if not clean_arg_name: 
                    continue
                arg_info['name'] = clean_arg_name

                # ✅ อ่านค่าจาก temp_args_key
                current_value = st.session_state[temp_args_key].get(clean_arg_name, arg_info.get('default', ''))
                
                # ✅ สร้าง unique key
                input_key = f"crud_edit_{step['id']}_{clean_arg_name}"
                
                # ✅ Render input และเก็บค่ากลับเข้า temp_args_key
                rendered_value = render_argument_input(
                    arg_info,
                    ws_state,
                    input_key,
                    current_value=current_value
                )
                
                # ✅ อัปเดต temp_args_key ด้วยค่าจาก widget
                # ใช้ logic แบบเดียวกับ ui_test_flow.py
                from ..ui_common import ARGUMENT_PRESETS, ARGUMENT_PATTERNS
                
                # Determine the actual key used by render_argument_input
                is_locator_arg = any(s in clean_arg_name.lower() for s in ['locator', 'field', 'button', 'element', 'menu', 'header', 'body', 'theader', 'tbody'])
                
                final_value = None
                if is_locator_arg:
                    final_value = st.session_state.get(f"{input_key}_locator_select", current_value)
                elif clean_arg_name in ARGUMENT_PRESETS:
                    config = ARGUMENT_PRESETS[clean_arg_name]
                    input_type = config.get('type')
                    if input_type == "select_or_input":
                        selected = st.session_state.get(f"{input_key}_select")
                        if selected == "📝 Other (custom)":
                            final_value = st.session_state.get(f"{input_key}_custom", current_value)
                        else:
                            final_value = selected if selected else current_value
                    else:
                        final_value = st.session_state.get(input_key, current_value)
                else:
                    # Check patterns
                    matched_pattern = False
                    arg_lower = clean_arg_name.lower()
                    for pattern_key in ARGUMENT_PATTERNS.keys():
                        if pattern_key in arg_lower:
                            final_value = st.session_state.get(input_key, current_value)
                            matched_pattern = True
                            break
                    
                    # Default Text Input
                    if not matched_pattern:
                        final_value = st.session_state.get(f"{input_key}_default_text", current_value)
                
                # Update temp_args_key
                st.session_state[temp_args_key][clean_arg_name] = final_value if final_value is not None else current_value

        elif not selected_kw:
            st.warning("Selected keyword definition not found.")

        # --- Save/Cancel Buttons (FIXED LOGIC) ---
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Save Changes", key=f"save_edit_{step['id']}", use_container_width=True, type="primary"):
                # ✅ ใช้ค่าจาก temp_args_key โดยตรง
                updated_data = {
                    "keyword": selected_kw_name,
                    "args": st.session_state.get(temp_args_key, {}).copy()
                }

                if 'type' in step: 
                    updated_data['type'] = step['type']
                if 'config' in step: 
                    updated_data['config'] = step['config']

                manager.update_step(real_section_key, step['id'], updated_data)
                
                # Cleanup states
                st.session_state[edit_mode_key] = False
                if edit_kw_state_key in st.session_state: 
                    del st.session_state[edit_kw_state_key]
                if temp_args_key in st.session_state: 
                    del st.session_state[temp_args_key]
                if f"prev_kw_{step['id']}" in st.session_state: 
                    del st.session_state[f"prev_kw_{step['id']}"]
                
                 # ✅ Cleanup CSV Quick Insert keys
                csv_keys = [
                    f"quick_csv_ds_edit_{step['id']}",
                    f"quick_csv_row_edit_{step['id']}",
                    f"quick_csv_col_edit_{step['id']}",
                    f"quick_csv_target_edit_{step['id']}",
                ]
                for key in csv_keys:
                    if key in st.session_state:
                        del st.session_state[key]
                
                # ✅ Cleanup Widget Keys
                if selected_kw and selected_kw.get('args'):
                    for arg_item in selected_kw.get('args', []):
                        clean_arg_name = arg_item.get('name', '').strip('${}')
                        if clean_arg_name:
                            widget_key = f"crud_edit_{step['id']}_{clean_arg_name}"
                            if widget_key in st.session_state:
                                del st.session_state[widget_key]

                st.rerun()
        
        with col2:
            if st.button("❌ Cancel", key=f"cancel_edit_{step['id']}", use_container_width=True):
                st.session_state[edit_mode_key] = False
                if edit_kw_state_key in st.session_state: 
                    del st.session_state[edit_kw_state_key]
                if temp_args_key in st.session_state: 
                    del st.session_state[temp_args_key]
                if f"prev_kw_{step['id']}" in st.session_state: 
                    del st.session_state[f"prev_kw_{step['id']}"]
                
                # ✅ Cleanup CSV Quick Insert keys
                csv_keys = [
                    f"quick_csv_ds_edit_{step['id']}",
                    f"quick_csv_row_edit_{step['id']}",
                    f"quick_csv_col_edit_{step['id']}",
                    f"quick_csv_target_edit_{step['id']}",
                ]
                for key in csv_keys:
                    if key in st.session_state:
                        del st.session_state[key]
                
                # ✅ Cleanup Widget Keys
                if selected_kw and selected_kw.get('args'):
                    for arg_item in selected_kw.get('args', []):
                        clean_arg_name = arg_item.get('name', '').strip('${}')
                        if clean_arg_name:
                            widget_key = f"crud_edit_{step['id']}_{clean_arg_name}"
                            if widget_key in st.session_state:
                                del st.session_state[widget_key]
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ======= TABLE VERIFICATION UI =======
def render_table_verification_ui(step, ws):
    """Simplified UI for table verification config"""
    step_id = step['id']
    st.markdown("**Table Locators**")
    col1, col2 = st.columns(2)
    with col1:
        step['args']['theader'] = st.text_input( "Header Locator",
            value=step['args'].get('theader', 'LOCATOR_TABLE_HEADER'), key=f"th_{step_id}" )
    with col2:
        step['args']['tbody'] = st.text_input( "Body Locator",
            value=step['args'].get('tbody', 'LOCATOR_TABLE_BODY'), key=f"tb_{step_id}" )

    st.markdown("---")
    st.markdown("**Column Assertions**")

    if 'assertion_columns' not in step['args']:
        step['args']['assertion_columns'] = []

    assertions = step['args']['assertion_columns']

    if not assertions:
        st.info("No column assertions yet. Click 'Add Column' below.")

    for i, assertion in enumerate(assertions):
        with st.container(border=True):
            col1, col2, col3 = st.columns([0.4, 0.5, 0.1])
            with col1:
                assertion['header_name'] = st.text_input("Column",
                    value=assertion.get('header_name', ''), key=f"tcol_{step_id}_{i}", label_visibility="collapsed")
            with col2:
                assertion['expected_value'] = st.text_input("Expected",
                    value=assertion.get('expected_value', ''), key=f"texp_{step_id}_{i}", label_visibility="collapsed")
            with col3:
                if st.button("🗑️", key=f"tdel_{step_id}_{i}", help="Remove"):
                    assertions.pop(i)
                    st.rerun()

    if st.button("➕ Add Column Assertion", use_container_width=True, key=f"tadd_{step_id}"):
        assertions.append({'header_name': '', 'expected_value': ''})
        st.rerun()


# ======= STICKY PREVIEW =======
def render_sticky_preview(ws):
    """Live Preview (Uses custom CSS div for scrolling) - ไม่มีหัวข้อ"""
    
    script_code = manager.generate_robot_script()

    st.markdown('<div class="code-preview-container">', unsafe_allow_html=True)
    st.code(script_code, language="robotframework", line_numbers=True)
    st.markdown('</div>', unsafe_allow_html=True)

    st.download_button(
        label="📥 Download Script",
        data=script_code,
        file_name=f"{ws.get('test_case_name', 'test')}.robot",
        mime="text/plain",
        use_container_width=True,
        type="primary"
    )

    with st.expander("📊 Script Stats", expanded=False):
        total_steps = sum(len(ws['steps'][key]) for key in ws['steps'])
        st.metric("Total Steps", total_steps)
        st.metric("Setup Steps", len(ws['steps'].get('suite_setup', [])))
        st.metric("Main Steps", len(ws['steps'].get('action_list', []) + ws['steps'].get('action_detail', [])))


# Wrapper function for CRUD Add Dialog
def render_crud_add_step_dialog():
    ws_state = st.session_state.studio_workspace # Get workspace state

    # Define the callback function for adding steps in CRUD Generator
    def add_step_to_crud(context_dict, new_step):
        section_key = context_dict.get("key")
        if section_key:
            manager.add_step(section_key, new_step)

    # Define a filter function to exclude API/CSV keywords
    def crud_keyword_filter(keyword):
        kw_name = keyword.get('name', '').lower()
        return not (kw_name.startswith('import datasource') or kw_name.startswith('request service'))

    # Call the base function with CRUD specific parameters
    context = st.session_state.get('crud_add_dialog_context', {})
    section_display_name = context.get('key', 'Unknown Section').upper()
    render_add_step_dialog_base(
        dialog_state_key='show_crud_add_dialog',
        context_state_key='crud_add_dialog_context', # Pass the context key
        selected_kw_state_key='selected_kw_crud',
        add_step_callback=add_step_to_crud,
        ws_state=ws_state,
        title=f"Add New Step to CRUD Flow ({section_display_name})",
        keyword_filter_func=crud_keyword_filter, # Apply the filter
        search_state_key="kw_search_dialog_crud", # Unique key
        recently_used_state_key="recently_used_keywords_crud" # Unique key
    )

# --- DIALOG: API/CSV Steps (UPDATED V3.10 - Stores Config) ---
@st.dialog("Add Data Source or API Step", width="large")
def render_api_csv_step_dialog():
    """
    Dialog to select and add CSV Data Source or API Service steps.
    (V3.11 - Enhanced with value insertion, Back button)
    """
    ws_state = st.session_state.studio_workspace
    context = st.session_state.get('api_csv_dialog_context', {})
    section_key = context.get("key")

    if not section_key:
        st.error("Error: Section context not found.")
        st.session_state['show_api_csv_dialog'] = False
        st.rerun()
        return

    # --- Cleanup Logic Function ---
    def close_dialog():
        st.session_state['show_api_csv_dialog'] = False
        if 'api_csv_dialog_context' in st.session_state:
            del st.session_state['api_csv_dialog_context']
        if 'csv_api_dialog_selection' in st.session_state:
            del st.session_state['csv_api_dialog_selection']
        st.rerun()

    # --- Back Button (Top Left) ---
    st.markdown('<div class="dialog-back-button">', unsafe_allow_html=True) # Add CSS class wrapper
    if st.button("← Back to Workspace", key="api_csv_dialog_back_button"):
        close_dialog()
    st.markdown('</div>', unsafe_allow_html=True) # Close CSS class wrapper
    st.markdown("---") # Add a separator below the back button

    # --- Dialog Content ---
    selection = st.session_state.get('csv_api_dialog_selection')
    st.info(f"Adding step to: **{section_key.upper()}**") # Keep info banner
    left_col, right_col = st.columns([1, 1], gap="large")

    # --- LEFT COLUMN (Selection) ---
    with left_col:
        st.markdown("### 🗃️ Available Data Sources")
        csv_keywords = extract_csv_datasource_keywords(ws_state)
        if not csv_keywords:
            st.caption("⚠️ No Data Sources found. Add them in the 'Test Data' tab first.")
        else:
            with st.container(border=True):
                for ds_name, ds_info in csv_keywords.items():
                    col_count = len(ds_info.get('headers', []))
                    label = f"📊 {ds_name}" + (f" ({col_count} columns)" if col_count > 0 else "")
                    # Use unique key combining type and name
                    button_key = f"csv_ds_{ds_name.replace(' ', '_').replace('.', '_')}"
                    if st.button(label, key=button_key, use_container_width=True):
                        st.session_state.csv_api_dialog_selection = {'type': 'csv', 'ds_name': ds_name, 'ds_info': ds_info}
                        st.rerun()

        st.markdown("---")
        st.markdown("### 🌐 Available API Services")
        api_services = ws_state.get('api_services', [])
        if not api_services:
            st.caption("⚠️ No API Services found. Add them in the 'Test Data' tab first.")
        else:
            with st.container(border=True):
                for service in api_services:
                    service_name = service.get('service_name', 'Untitled')
                    method = service.get('http_method', 'POST')
                    # Use unique key combining type and name
                    button_key = f"api_svc_{service_name.replace(' ', '_').replace('.', '_')}"
                    if st.button(f"🔗 {service_name} ({method})", key=button_key, use_container_width=True):
                        st.session_state.csv_api_dialog_selection = {'type': 'api', 'service': service}
                        st.rerun()

    # --- RIGHT COLUMN (Configuration & Add) ---
    with right_col:
        if not selection:
            st.info("👈 Select a Data Source or API Service from the left to configure.")
            # No redundant close button needed here
            return # Exit if nothing is selected

        # --- CSV Data Source Configuration ---
        if selection['type'] == 'csv':
            ds_name = selection['ds_name']
            ds_info = selection['ds_info']
            st.markdown(f"#### 📊 Configure: `{ds_name}`")
            st.caption("This will import the CSV data into your test.")

            with st.container(border=True):
                st.markdown(f"**📁 File:** `{ds_info.get('csv_filename', 'N/A')}`")
                st.markdown(f"**🔤 Variable Name:** `{ds_info['ds_var']}`")
                st.markdown(f"**📋 Column Variable:** `{ds_info['col_var']}`")

            headers = ds_info.get('headers', [])
            if headers:
                st.markdown("---")
                st.markdown("**📊 Available Columns:**")
                cols_per_row = 3
                for i in range(0, len(headers), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j, col in enumerate(cols):
                        if i + j < len(headers):
                            col.markdown(f"`{headers[i + j]}`")
                st.markdown("---")
                st.markdown("**💡 Usage Examples:**")
                st.caption("After importing, you can access data like this:")
                key_col = headers[0] if headers else 'key_column' # Handle empty headers case
                if len(headers) > 1:
                    example_col = headers[1]
                    st.code(f"# Access specific value:\n${{{ds_info['ds_var']}['row_key'][${{{ds_info['col_var']}.{example_col}}}]}}\n\n# Example with actual key:\n${{{ds_info['ds_var']}['robotapi'][${{{ds_info['col_var']}.{example_col}}}]}}", language="robotframework")
                else:
                    st.code(f"# Access row by key:\n${{{ds_info['ds_var']}['{key_col}']}}", language="robotframework")
            else:
                st.warning("⚠️ Could not read CSV headers. The file might be empty or invalid.")

            st.markdown("---")
            if st.button(f"✅ Add Import Step for '{ds_name}'", type="primary", use_container_width=True):
                keyword_name = f"Import DataSource {ds_name}"
                new_step = {
                    "id": str(uuid.uuid4()),
                    "keyword": keyword_name,
                    "args": {},
                    "type": "csv_import",
                    "config": {
                        'ds_name': ds_name,
                        'col_var': ds_info['col_var'],
                        'ds_var': ds_info['ds_var'],
                        'csv_filename': ds_info.get('csv_filename', ''),
                        'headers': headers
                    }
                }
                manager.add_step(section_key, new_step)
                st.success(f"✅ Added '{keyword_name}' step!")
                close_dialog() # Close after adding

        # --- API Service Configuration ---
        elif selection['type'] == 'api':
            service = selection['service']
            service_name = service.get('service_name', 'Untitled')
            st.markdown(f"#### 🔗 Configure: `{service_name}`")

            with st.container(border=True):
                st.markdown(f"**🔄 Method:** `{service.get('http_method', 'POST')}`")
                st.markdown(f"**🌐 Endpoint:** `{service.get('endpoint_path', '/')}`")

            args = service.get('analyzed_fields', {})
            required_args = [name for name, data in args.items() if data.get('is_argument')]
            if required_args:
                st.markdown("**📝 Required Arguments:**")
                st.caption(" ".join([f"`${{{a}}}`" for a in required_args])) # Use caption for less space

            st.markdown("---")
            if st.button(f"✅ Add API Call for '{service_name}'", type="primary", use_container_width=True):
                keyword_name = f"Request {service_name.replace('_', ' ').title()}"
                default_args = {'headeruser': '${USER_ADMIN}', 'headerpassword': '${PASSWORD_ADMIN}'}
                default_args.update({arg: '' for arg in required_args}) # Add required args with empty default
                new_step = {
                    "id": str(uuid.uuid4()),
                    "keyword": keyword_name,
                    "args": default_args,
                    "type": "api_call"
                }
                manager.add_step(section_key, new_step)
                st.success(f"✅ Added '{keyword_name}' step!")
                close_dialog() # Close after adding


def extract_csv_datasource_keywords(ws_state):
    """
    Extracts CSV Data Source information from workspace state.
    Returns dict: {ds_name: {col_var, ds_var, csv_path, headers}}
    """
    result = {}
    
    # Get data sources from workspace
    data_sources = ws_state.get('data_sources', [])
    
    for ds in data_sources:
        ds_name_raw = ds.get('name', '')
        csv_filename = ds.get('file_name', '')
        col_var = ds.get('col_name', '')
        
        if not ds_name_raw or not csv_filename:
            continue
        
        # Generate variable names
        # e.g., "LOGIN" -> "DS_LOGIN"
        ds_var_name = f"{ds_name_raw.upper().replace(' ', '_')}"
        
        # Get CSV headers
        headers = manager.get_csv_headers(csv_filename)
        
        # Use ds_name_raw for both key and col_var generation
        result[ds_name_raw.upper()] = {  # ← แก้ตรงนี้
            'col_var': col_var if col_var else f"{ds_name_raw.lower().replace(' ', '_')}",  # ← แก้ตรงนี้ด้วย
            'ds_var': ds_var_name,
            'csv_filename': csv_filename,
            'headers': headers if headers else []
        }
    
    return result

# ======= DIALOG: Fill Form =======
# ======= DIALOG: Fill Form (FIXED - No Pending Logic) =======
@st.dialog("จัดการฟอร์มทั้งหมด (Fill Form Fields)", width="large")
def render_fill_form_dialog():
    """FIXED: ใช้ปุ่มธรรมดา + rerun แทน pending logic"""
    section_key = "action_detail"
    ws_state = st.session_state.studio_workspace
    all_locators = ws_state.get('locators', [])

    def format_locator(locator_obj):
        if isinstance(locator_obj, dict):
            return get_clean_locator_name(locator_obj.get('name', 'Invalid Locator'))
        return locator_obj

    st.markdown("""
        <style> .scrollable-dialog-container { max-height: 60vh; overflow-y: auto; padding-right: 15px; } </style>
    """, unsafe_allow_html=True)

    search_query = st.text_input("🔍 ค้นหาฟิลด์", key="fill_form_search").lower()
    if st.button("➕ เพิ่ม Field ใหม่", use_container_width=True):
        manager.add_fill_form_step(section_key)
        st.rerun()
    st.markdown("---")

    # === CSV Quick Insert (ไม่ใช้ pending logic) ===
    with st.expander("📊 Quick Insert from CSV Data", expanded=False):
        st.caption("Select a value to insert into empty fields")
        csv_keywords = extract_csv_datasource_keywords(ws_state)
        
        if csv_keywords:
            quick_col1, quick_col2, quick_col3 = st.columns([2, 2, 2])
            
            with quick_col1:
                quick_ds = st.selectbox(
                    "Data Source",
                    options=list(csv_keywords.keys()),
                    key="quick_csv_ds_fill"
                )
            
            if quick_ds:
                ds_info = csv_keywords[quick_ds]
                headers = ds_info.get('headers', [])
                
                if headers:
                    with quick_col2:
                        quick_row = st.text_input(
                            "Row Key",
                            key="quick_csv_row_fill",
                            placeholder="e.g., robotapi"
                        )
                    
                    with quick_col3:
                        if len(headers) > 1:
                            quick_col = st.selectbox(
                                "Column",
                                options=headers[1:],
                                key="quick_csv_col_fill"
                            )
                        else:
                            quick_col = None
                    
                    # ✅ แสดงปุ่ม Apply เสมอ (ไม่มี preview)
                    if quick_ds:
                        ds_var = ds_info['ds_var']
                        col_var = ds_info['col_var']
                        
                        insert_syntax = ""
                        if quick_row:
                            if len(headers) > 1 and quick_col:
                                insert_syntax = f"${{{ds_var}['{quick_row}'][${{{col_var}.{quick_col}}}]}}"
                            else:
                                insert_syntax = f"${{{ds_var}['{quick_row}']}}"
                        
                        # ✅ ปุ่ม Apply (แสดงเสมอ)
                        if st.button("✅ Apply to All Empty Fields", type="primary", key="quick_csv_apply_fill_btn"):
                            if not quick_row:
                                st.warning("Please enter a 'Row Key'")
                            elif insert_syntax:
                                all_fill_steps = [s for s in manager._get_workspace()['steps']['action_detail'] 
                                                if s['keyword'] == 'Fill in data form']
                                
                                applied_count = 0
                                for step in all_fill_steps:
                                    step_id = step['id']
                                    current_value = step['args'].get('value', '')
                                    if not current_value:
                                        st.session_state[f"val_{step_id}"] = insert_syntax
                                        applied_count += 1
                                
                                if applied_count > 0:
                                    st.toast(f"✅ Applied '{insert_syntax}' to {applied_count} empty fields!", icon="✅")
                                    st.rerun()
                                else:
                                    st.info("No empty fields found to apply.")
        else:
            st.info("No CSV data sources found. Add them in Test Data tab.")

    with st.form(key="fill_form_chunked_editor"):
        all_fill_steps = [s for s in manager._get_workspace()['steps'][section_key] if s['keyword'] == 'Fill in data form']
        form_data = {}
        steps_to_delete = []

        filtered_steps = []
        if not search_query:
            filtered_steps = all_fill_steps
        else:
            for step in all_fill_steps:
                loc_name = get_clean_locator_name(step['args'].get('locator_field', {}).get('name', ''))
                if search_query in loc_name.lower():
                    filtered_steps.append(step)

        total_steps = len(filtered_steps)
        num_chunks = 1
        if not search_query:
            THRESHOLD = 10
            if total_steps >= THRESHOLD:
                if total_steps <= 15: num_chunks = 2
                elif total_steps <= 25: num_chunks = 3
                else: num_chunks = 4

        if total_steps == 0: chunks = []
        else: chunks = np.array_split(filtered_steps, num_chunks)

        st.markdown('<div class="scrollable-dialog-container">', unsafe_allow_html=True)
        global_step_counter = 0
        with st.container():
            for i, chunk in enumerate(chunks):
                if len(chunk) == 0: continue
                if search_query: 
                    label = f"Search Results ({len(chunk)} fields found)"
                else:
                    start_num = global_step_counter + 1
                    end_num = global_step_counter + len(chunk)
                    label = f"Fields {start_num} - {end_num}"
                    global_step_counter = end_num

                with st.expander(label, expanded=True):
                    header_cols = st.columns([0.4, 0.2, 0.4, 0.05])
                    header_cols[0].markdown("**📍 Locator Field**")
                    header_cols[1].markdown("**⚙️ Input Type**")
                    header_cols[2].markdown("**⌨️ Value / Setting**")
                    header_cols[3].markdown("**ลบ?**")
                    st.markdown("---")

                    for step in chunk:
                        step_args = step['args']
                        step_id = step['id']
                        form_data[step_id] = {}
                        cols = st.columns([0.4, 0.2, 0.4, 0.05])

                        with cols[0]:
                            selected_loc_obj = step_args.get('locator_field')
                            loc_index = 0
                            if all_locators:
                                try: 
                                    loc_index = [loc.get('name') for loc in all_locators].index(selected_loc_obj.get('name'))
                                except (ValueError, AttributeError): 
                                    loc_index = 0
                            
                            # ✅ รับค่าโดยตรงจาก return value
                            form_data[step_id]['locator_field'] = st.selectbox(
                                "loc", 
                                all_locators, 
                                index=loc_index, 
                                format_func=format_locator,
                                key=f"loc_{step_id}", 
                                label_visibility="collapsed"
                            )

                        with cols[1]:
                            current_type = 'Text'
                            if step_args.get('is_switch_type'): 
                                current_type = 'Switch'
                            elif step_args.get('is_checkbox_type'): 
                                current_type = 'Checkbox'
                            
                            try: 
                                type_index = ['Text', 'Select', 'Checkbox', 'Switch'].index(current_type)
                            except ValueError: 
                                type_index = 0
                            
                            # ✅ รับค่าโดยตรงจาก return value
                            input_type = st.selectbox(
                                "type", 
                                ['Text', 'Select', 'Checkbox', 'Switch'], 
                                index=type_index,
                                key=f"type_{step_id}", 
                                label_visibility="collapsed"
                            )
                            form_data[step_id]['input_type'] = input_type

                        with cols[2]:
                            if input_type in ['Text', 'Select']:
                                # ✅ ดึงค่าจาก session_state (อาจมาจาก CSV Apply)
                                default_value = st.session_state.get(f"val_{step_id}", step_args.get('value', ''))
                                
                                # ✅ รับค่าโดยตรงจาก return value
                                form_data[step_id]['value'] = st.text_input(
                                    "val", 
                                    value=default_value,
                                    key=f"val_{step_id}", 
                                    label_visibility="collapsed"
                                )
                                
                            elif input_type == 'Switch':
                                selected_switch_loc_obj = step_args.get('locator_switch_checked')
                                switch_loc_index = 0
                                if all_locators:
                                    try: 
                                        switch_loc_index = [loc.get('name') for loc in all_locators].index(selected_switch_loc_obj.get('name'))
                                    except (ValueError, AttributeError): 
                                        switch_loc_index = 0
                                
                                # ✅ รับค่าโดยตรงจาก return value
                                form_data[step_id]['locator_switch_checked'] = st.selectbox(
                                    "switch_loc", 
                                    all_locators, 
                                    index=switch_loc_index,
                                    format_func=format_locator, 
                                    key=f"switch_loc_{step_id}",
                                    label_visibility="collapsed", 
                                    help="เลือก Locator ที่ใช้สำหรับติ๊ก Switch"
                                )
                            else:
                                st.caption("(No value needed)")

                        with cols[3]:
                            if st.checkbox("del", key=f"del_{step_id}", label_visibility="collapsed"):
                                steps_to_delete.append(step_id)

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("---")

        save_col, cancel_col = st.columns(2)
        submitted_save = save_col.form_submit_button("💾 บันทึกและปิด", use_container_width=True, type="primary")
        submitted_cancel = cancel_col.form_submit_button("❌ ยกเลิก", use_container_width=True)

        if submitted_save:
            if steps_to_delete:
                for step_id in steps_to_delete: 
                    manager.delete_step(section_key, step_id)
            
            updates_to_save = {}
            for step_id, data in form_data.items():
                if step_id not in steps_to_delete:
                    original_step = next((s for s in all_fill_steps if s['id'] == step_id), None)
                    if original_step:
                        original_step_args = original_step.get('args', {})
                        new_args_for_step = {
                            "locator_field": data.get('locator_field'),
                            "value": data.get('value', ''),
                            "locator_switch_checked": data.get('locator_switch_checked'),
                            "is_checkbox_type": data.get('input_type') == 'Checkbox',
                            "is_switch_type": data.get('input_type') == 'Switch',
                            "select_attribute": original_step_args.get('select_attribute', 'label'),
                            "is_ant_design": original_step_args.get('is_ant_design', False)
                        }
                        
                        if new_args_for_step != original_step_args:
                            updates_to_save[step_id] = new_args_for_step

            if updates_to_save:
                if hasattr(manager, 'batch_update_step_args'):
                    manager.batch_update_step_args(section_key, updates_to_save)
                else:
                    for step_id, new_args in updates_to_save.items():
                        manager.update_step_args(section_key, step_id, new_args)

            st.session_state.show_fill_form_dialog = False
            if 'fill_form_search' in st.session_state: 
                del st.session_state.fill_form_search
            
            # Clear CSV states
            csv_keys = [k for k in st.session_state.keys() if k.startswith('quick_csv_') and '_fill' in k]
            for key in csv_keys:
                del st.session_state[key]
            
            st.rerun()

        if submitted_cancel:
            st.session_state.show_fill_form_dialog = False
            if 'fill_form_search' in st.session_state: 
                del st.session_state.fill_form_search
            st.rerun()

# ======= DIALOG: Verify Detail (FIXED - No Pending Logic) =======
@st.dialog("จัดการฟอร์มตรวจสอบ (Verify Detail Fields)", width="large")
def render_verify_detail_dialog():
    """FIXED: ใช้ปุ่มธรรมดา + rerun แทน pending logic"""
    section_key = "verify_detail"
    ws_state = st.session_state.studio_workspace
    all_locators = ws_state.get('locators', [])

    action_fill_steps = [s for s in manager._get_workspace()['steps']['action_detail'] if s['keyword'] == 'Fill in data form']
    expected_value_map = {}
    for step in action_fill_steps:
        locator_name = step['args'].get('locator_field', {}).get('name')
        value = step['args'].get('value')
        if locator_name and value: 
            expected_value_map[locator_name] = value

    def format_locator(locator_obj):
        if isinstance(locator_obj, dict):
            return get_clean_locator_name(locator_obj.get('name', 'Invalid Locator'))
        return locator_obj

    st.markdown("""
        <style> .scrollable-dialog-container { max-height: 60vh; overflow-y: auto; padding-right: 15px; } </style>
    """, unsafe_allow_html=True)

    search_query = st.text_input("🔍 ค้นหาฟิลด์", key="verify_form_search").lower()
    if st.button("➕ เพิ่ม Field ตรวจสอบใหม่", use_container_width=True):
        kw_info = next((kw for kw in ws_state.get('keywords', []) if kw['name'] == 'Verify data form'), None)
        if kw_info:
            new_step = {
                "id": str(uuid.uuid4()), 
                "keyword": "Verify data form",
                "args": {
                    "locator_field": "", 
                    "expected_value": "", 
                    "select_attribute": "label"
                }
            }
            manager.add_step(section_key, new_step)
            st.rerun()
        else:
            st.error("ไม่พบ Keyword 'Verify data form' ใน common keywords")
    
    st.markdown("---")
    
    # === CSV Quick Insert (ไม่ใช้ pending logic) ===
    with st.expander("📊 Quick Insert from CSV Data", expanded=False):
        st.caption("Select expected value to verify")
        csv_keywords = extract_csv_datasource_keywords(ws_state)
        
        if csv_keywords:
            quick_col1, quick_col2, quick_col3 = st.columns([2, 2, 2])
            
            with quick_col1:
                quick_ds = st.selectbox(
                    "Data Source",
                    options=list(csv_keywords.keys()),
                    key="quick_csv_ds_verify"
                )
            
            if quick_ds:
                ds_info = csv_keywords[quick_ds]
                headers = ds_info.get('headers', [])
                
                if headers:
                    with quick_col2:
                        quick_row = st.text_input(
                            "Row Key",
                            key="quick_csv_row_verify",
                            placeholder="e.g., robotapi"
                        )
                    
                    with quick_col3:
                        if len(headers) > 1:
                            quick_col = st.selectbox(
                                "Column",
                                options=headers[1:],
                                key="quick_csv_col_verify"
                            )
                        else:
                            quick_col = None
                    
                    if quick_row:
                        ds_var = ds_info['ds_var']
                        col_var = ds_info['col_var']
                        
                        if len(headers) > 1 and quick_col:
                            preview_syntax = f"${{{ds_var}['{quick_row}'][${{{col_var}.{quick_col}}}]}}"
                        else:
                            preview_syntax = f"${{{ds_var}['{quick_row}']}}"
                        
                        st.code(preview_syntax, language="robotframework")
                        
                        # ✅ ใช้ปุ่มธรรมดา + rerun
                        if st.button("✅ Apply to All Empty Fields", type="primary", key="quick_csv_apply_verify_btn"):
                            all_verify_steps = [s for s in manager._get_workspace()['steps']['verify_detail'] 
                                               if s['keyword'] == 'Verify data form']
                            
                            for step in all_verify_steps:
                                step_id = step['id']
                                current_value = step['args'].get('expected_value', '')
                                
                                if not current_value:
                                    locator_name = step['args'].get('locator_field', {}).get('name', '')
                                    # ถ้ายังไม่มีค่าจาก expected_value_map ก็ apply
                                    if not expected_value_map.get(locator_name):
                                        st.session_state[f"verify_val_{step_id}"] = preview_syntax
                            
                            st.toast(f"✅ Applied '{preview_syntax}' to empty fields!", icon="✅")
                            st.rerun()  # ← Rerun เพื่อแสดงค่าใหม่
        else:
            st.info("No CSV data sources found. Add them in Test Data tab.")
    
    st.markdown("---")
    
    with st.form(key="verify_detail_chunked_editor"):
        all_verify_steps = [s for s in manager._get_workspace()['steps'][section_key] if s['keyword'] == 'Verify data form']
        form_data = {}
        steps_to_delete = []

        filtered_steps = []
        if not search_query:
            filtered_steps = all_verify_steps
        else:
            for step in all_verify_steps:
                loc_name = get_clean_locator_name(step['args'].get('locator_field', {}).get('name', ''))
                if search_query in loc_name.lower():
                    filtered_steps.append(step)

        total_steps = len(filtered_steps)
        num_chunks = 1
        if not search_query:
            THRESHOLD = 10
            if total_steps >= THRESHOLD:
                if total_steps <= 15: num_chunks = 2
                elif total_steps <= 25: num_chunks = 3
                else: num_chunks = 4

        if total_steps == 0: chunks = []
        else: chunks = np.array_split(filtered_steps, num_chunks)

        st.markdown('<div class="scrollable-dialog-container">', unsafe_allow_html=True)
        global_step_counter = 0
        temp_locators = {}
        
        with st.container():
            for i, chunk in enumerate(chunks):
                if len(chunk) == 0: continue
                if search_query: 
                    label = f"Search Results ({len(chunk)} fields found)"
                else:
                    start_num = global_step_counter + 1
                    end_num = global_step_counter + len(chunk)
                    label = f"Verify Fields {start_num} - {end_num}"
                    global_step_counter = end_num

                with st.expander(label, expanded=True):
                    header_cols = st.columns([0.5, 0.5, 0.05])
                    header_cols[0].markdown("**📍 Locator Field (ที่ต้องการตรวจสอบ)**")
                    header_cols[1].markdown("**⌨️ Expected Value**")
                    header_cols[2].markdown("**ลบ?**")
                    st.markdown("---")

                    for step in chunk:
                        step_args = step['args']
                        step_id = step['id']
                        form_data[step_id] = {}
                        cols = st.columns([0.5, 0.5, 0.05])

                        with cols[0]:
                            selected_loc_obj = step_args.get('locator_field')
                            loc_index = 0
                            if all_locators:
                                try: 
                                    loc_index = [loc.get('name') for loc in all_locators].index(selected_loc_obj.get('name'))
                                except (ValueError, AttributeError): 
                                    loc_index = 0
                            
                            # ✅ รับค่าและเก็บไว้ใน temp
                            selected_locator = st.selectbox(
                                "loc", 
                                all_locators, 
                                index=loc_index, 
                                format_func=format_locator,
                                key=f"verify_loc_{step_id}", 
                                label_visibility="collapsed"
                            )
                            temp_locators[step_id] = selected_locator
                            form_data[step_id]['locator_field'] = selected_locator
                        
                        with cols[1]:
                            # ✅ ดึงค่าจาก session_state ก่อน (อาจมาจาก CSV Apply)
                            current_value = st.session_state.get(f"verify_val_{step_id}")
                            
                            # ถ้ายังไม่มี ลอง auto-fill จาก expected_value_map
                            if not current_value:
                                current_value = step_args.get('expected_value', '')
                                if not current_value and step_id in temp_locators:
                                    locator_name = temp_locators[step_id].get('name') if isinstance(temp_locators[step_id], dict) else ""
                                    current_value = expected_value_map.get(locator_name, '')
                            
                            # ✅ รับค่าโดยตรงจาก return value
                            form_data[step_id]['expected_value'] = st.text_input(
                                "val", 
                                value=current_value,
                                key=f"verify_val_{step_id}", 
                                label_visibility="collapsed"
                            )

                        with cols[3]:
                            if st.checkbox("del", key=f"del_verify_{step_id}", label_visibility="collapsed"):
                                steps_to_delete.append(step_id)

        st.markdown('</div>', unsafe_allow_html=True)
        st.markdown("---")

        save_col, cancel_col = st.columns(2)
        submitted_save = save_col.form_submit_button("💾 บันทึกและปิด", use_container_width=True, type="primary")
        submitted_cancel = cancel_col.form_submit_button("❌ ยกเลิก", use_container_width=True)

        if submitted_save:
            if steps_to_delete:
                for step_id in steps_to_delete: 
                    manager.delete_step(section_key, step_id)
            
            updates_to_save = {}
            for step_id, data in form_data.items():
                if step_id not in steps_to_delete:
                    original_step = next((s for s in all_verify_steps if s['id'] == step_id), None)
                    if original_step:
                        original_step_args = original_step.get('args', {})
                        new_args_for_step = {
                            "locator_field": data.get('locator_field'),
                            "expected_value": data.get('expected_value', ''),
                            "select_attribute": original_step_args.get('select_attribute', 'label')
                        }
                        
                        if new_args_for_step != original_step_args:
                            updates_to_save[step_id] = new_args_for_step

            if updates_to_save:
                if hasattr(manager, 'batch_update_step_args'):
                    manager.batch_update_step_args(section_key, updates_to_save)
                else:
                    for step_id, new_args in updates_to_save.items():
                        manager.update_step_args(section_key, step_id, new_args)

            st.session_state.show_verify_detail_dialog = False
            if 'verify_form_search' in st.session_state: 
                del st.session_state.verify_form_search
            
            # Clear CSV states
            csv_keys = [k for k in st.session_state.keys() if k.startswith('quick_csv_') and '_verify' in k]
            for key in csv_keys:
                del st.session_state[key]
            
            st.rerun()

        if submitted_cancel:
            st.session_state.show_verify_detail_dialog = False
            if 'verify_form_search' in st.session_state: 
                del st.session_state.verify_form_search
            st.rerun()


# ======= CSS =======
def inject_hybrid_css():
    """เพิ่ม CSS (V3.7)
    - Updated .code-preview-container
    - Removed custom green button override
    """
    st.markdown("""
    <style>

        /* --- 1. Live Code Preview --- */
        .code-preview-container {
            max-height: 800px; /* (V3.7) Increased height */
            overflow-y: auto;
            border: 1px solid #30363d;
            border-radius: 8px;
            margin-bottom: 1rem;
            background: #0d1117;
            /* (V3.7) Added sticky position */
            position: sticky;
            top: 60px; /* Adjust this value based on your header height */
        }
        .code-preview-container .stCodeBlock { height: 100%; margin-bottom: 0; }

        /* --- 2. Dialog Button Left-Align --- */
        div[data-testid="stDialog"] div[data-testid="stExpander"] div[data-testid="stButton"] > button { justify-content: flex-start !important; text-align: left; padding-left: 1rem; }

        /* --- 3. Top Tabs --- */
        .stTabs [data-baseweb="tab-list"] { gap: 8px; background: rgba(30, 41, 59, 0.5); padding: 8px; border-radius: 12px; margin-bottom: 1rem; }
        .stTabs [data-baseweb="tab"] { background: transparent; border-radius: 8px; padding: 10px 18px; font-weight: 600; transition: all 0.3s ease; }
        .stTabs [data-baseweb="tab"]:hover { background: rgba(88, 166, 255, 0.1); }
        .stTabs [data-baseweb="tab"][aria-selected="true"] { background: linear-gradient(135deg, rgba(88, 166, 255, 0.2), rgba(88, 166, 255, 0.1)); border-bottom: 3px solid #58a6ff; color: #c9d1d9; }

        /* --- 4. Step Card --- */
        .step-card {
            width: 100%;
            margin-bottom: 0.75rem;
            position: relative;
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 8px;
            transition: all 0.3s ease;
        }
        .step-card:hover { border-color: #8b949e; }

        /* Header Container */
        .step-card > div > div > div > .stColumns {
            border-bottom: 1px solid #30363d;
            padding: 0.5rem 0.75rem;
            align-items: center;
        }
        /* Header Content Wrapper */
        .step-header-content { display: flex; align-items: center; gap: 0.75rem; }
        /* Inline Step Number */
        .step-number-inline {
            font-size: 1.2rem;
            font-weight: 700;
            color: #ffffff;
            background: linear-gradient(135deg, #1f4788 0%, #0d2d5e 100%);
            border: 1px solid #2d5a9e;
            border-radius: 8px;
            padding: 0.4rem 0.6rem;
            min-width: 37px;
            height: 37px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            line-height: 1;
            box-shadow: 0 2px 8px rgba(15, 45, 94, 0.4),
                        0 0 0 1px rgba(45, 90, 158, 0.5),
                        inset 0 1px 0 rgba(255, 255, 255, 0.1);
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.6);
        }
        /* Keyword Display */
        .step-keyword { display: flex; flex-direction: column; justify-content: center; gap: 0rem; }
        .step-keyword-label { font-size: 0.7rem; font-weight: 600; text-transform: uppercase; color: #8b949e; }
        .step-keyword-name { font-size: 1.1rem; font-weight: 600; color: #58a6ff; line-height: 1.3; }


        /* === REVISED TOOLBAR (IMPROVED) === */
        /* Wrapper container - compact alignment */
        .step-card-toolbar-wrapper {
            display: flex;
            justify-content: flex-end;
            align-items: center;
            gap: 0.2rem !important;
            padding: 0 !important;
            margin: 0 !important;
        }

        /* Hide Column wrapper styling completely */
        .step-card-toolbar-wrapper > div[data-testid="column"] {
            padding: 0 !important;
            margin: 0 !important;
            background: transparent !important;
            border: none !important;
            box-shadow: none !important;
            min-width: auto !important;
            width: auto !important;
            flex: 0 0 auto !important;
        }

        .step-card-toolbar-wrapper > div[data-testid="column"]:hover {
            transform: none !important;
            box-shadow: none !important;
            background: transparent !important;
        }

        /* Hide inner div that wraps the button */
        .step-card-toolbar-wrapper div[data-testid="column"] > div {
            padding: 0 !important;
            margin: 0 !important;
            width: 20px !important;
            height: 20px !important;
        }

        /* Button styling - clean and minimal */
        .step-card-toolbar-wrapper .stButton {
            width: 20px !important;
            height: 20px !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        .step-card-toolbar-wrapper .stButton button {
            width: 20px !important;
            height: 20px !important;
            min-width: 20px !important;
            min-height: 20px !important;
            padding: 0 !important;
            margin: 0 !important;
            font-size: 0.8rem !important;
            line-height: 1 !important;
            border-radius: 5px !important;
            background: transparent !important;
            border: 1px solid transparent !important;
            box-shadow: none !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            overflow: hidden;
            color: var(--text-tertiary) !important;
            transition: all 0.15s ease !important;
        }

        /* Hover effects */
        .step-card-toolbar-wrapper .stButton button:hover {
            background: var(--bg-subtle) !important;
            border-color: var(--border-default) !important;
            color: var(--text-primary) !important;
            transform: scale(1.08);
            box-shadow: var(--shadow-sm) !important;
        }

        /* Active state */
        .step-card-toolbar-wrapper .stButton button:active {
            transform: scale(0.95);
            filter: brightness(0.9);
        }

        /* Icon sizing */
        .step-card-toolbar-wrapper .stButton button i,
        .step-card-toolbar-wrapper .stButton button svg {
            font-size: inherit !important;
            width: 1em;
            height: 1em;
        }
        /* === END REVISED TOOLBAR === */


        /* Caption (Argument) Styling */

        /* Caption (Argument) Styling */
        .step-card .stCaption { 
            padding: 0.1rem 1rem 0.6rem 1rem; 
            color: #58a6ff !important;; /* เปลี่ยนเป็นสีฟ้าเหมือน keyword */
            font-size: 0.8rem; 
            font-family: 'SF Mono', 'Monaco', 'Courier New', monospace; 
            line-height: 1.4; 
            margin-top: -0.2rem; 
            display: block; 
            width: 100%; 
            word-wrap: break-word; 
            white-space: normal; /* แสดงหลายบรรทัดได้ */
            overflow-wrap: break-word; /* แบ่งคำยาวๆ */
        }

        /* --- NEW: Inline Edit Section Styling --- */
        .crud-edit-section {
            padding: 1rem 1.25rem;
            background: rgba(30, 41, 59, 0.3); /* Slightly different background */
            border-top: 1px solid #30363d;
            border-radius: 0 0 7px 7px; /* Match card rounding */
        }
        .crud-edit-section h5 { /* Style the 'Edit Step' title */
            margin-top: 0;
            margin-bottom: 1rem;
            color: #c9d1d9;
        }
        .crud-edit-section .stSelectbox, .crud-edit-section .stTextInput {
            margin-bottom: 0.75rem; /* Space between inputs */
        }

        /* --- Existing Styles --- */
        button[kind="secondary"] { background: #21262d; border: 1px solid #30363d; }
        button[kind="secondary"]:hover { background: #30363d; border-color: #8b949e; }
        h4, h3 { color: #58a6ff; border-bottom: 2px solid #30363d; padding-bottom: 0.5rem; margin-bottom: 1rem; }
        .stMetric { background: #161b22; padding: 0.75rem; border-radius: 8px; border: 1px solid #30363d; }
        .stAlert { border-radius: 8px; border-left: 4px solid; }
    </style>
    """, unsafe_allow_html=True)