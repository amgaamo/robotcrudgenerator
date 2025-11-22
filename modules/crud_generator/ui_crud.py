"""
UI Module for the CRUD Generator Tab
(Complete Code - Hybrid Style with Top-Tabs)
(Version 3.10 - CSV Step Dialog now stores configuration)
(MODIFIED: Standardized buttons)
"""
import streamlit as st
import numpy as np
import json
import os 
import re
import uuid
from . import manager
from ..session_manager import get_clean_locator_name
from ..ui_common import render_argument_input, render_step_card_compact, extract_csv_datasource_keywords, ARGUMENT_PRESETS
from ..dialog_commonkw import render_add_step_dialog_base
from modules.utils import format_args_as_string, util_get_csv_first_column_values

# ======= ENTRY POINT FUNCTION =======
def render_crud_generator_tab():
    """
    Main entry point สำหรับ CRUD Generator Tab
    """
    inject_hybrid_css()
    render_crud_generator_tab_improved()

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

    # ✅ Sync keywords from Keyword Factory
    num_factory_kw = manager.sync_keyword_factory_keywords()

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
        st.markdown("#### 🎯 CRUD Test Generator", unsafe_allow_html=True)
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

            # --- 4.2 Phase Navigation (Buttons แทน Tabs) ---
            if 'crud_active_phase' not in st.session_state:
                st.session_state.crud_active_phase = 'actions'

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("🛠️ 1. Setup", use_container_width=True,
                        type="primary" if st.session_state.crud_active_phase == 'setup' else "secondary"):
                    st.session_state.crud_active_phase = 'setup'
                    st.rerun()
            with col2:
                if st.button("⚡ 2. Actions", use_container_width=True,
                        type="primary" if st.session_state.crud_active_phase == 'actions' else "secondary"):
                    st.session_state.crud_active_phase = 'actions'
                    st.rerun()
            with col3:
                if st.button("✅ 3. Verify", use_container_width=True,
                        type="primary" if st.session_state.crud_active_phase == 'verify' else "secondary"):
                    st.session_state.crud_active_phase = 'verify'
                    st.rerun()
            with col4:
                if st.button("🧹 4. Teardown", use_container_width=True,
                        type="primary" if st.session_state.crud_active_phase == 'teardown' else "secondary"):
                    st.session_state.crud_active_phase = 'teardown'
                    st.rerun()

            st.markdown("---")

            # Render phase ตาม state
            if st.session_state.crud_active_phase == 'setup':
                render_setup_phase(ws)
            elif st.session_state.crud_active_phase == 'actions':
                render_actions_phase(ws)
            elif st.session_state.crud_active_phase == 'verify':
                render_verification_phase(ws)
            elif st.session_state.crud_active_phase == 'teardown':
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
    """Phase 3: Verification - (REVISED) 5 sub-sections"""
    st.markdown("### ✅ Verification Phase")

    def set_verify_sub(sub_name):
        st.session_state.verify_active_sub = sub_name

    # --- (แก้ไข) ใช้ state_key ใหม่ (ตรงกับชื่อ list) ---
    if 'verify_active_sub' not in st.session_state:
        st.session_state.verify_active_sub = 'verify_list_search' # <--- ค่าเริ่มต้นใหม่
    active_sub = st.session_state.verify_active_sub

    # --- (แก้ไข) Navigation 5 ปุ่ม (ปรับ args ให้ตรงกับ state_key ใหม่) ---
    sub_col1, sub_col2, sub_col3, sub_col4, sub_col5 = st.columns([
        1.2, 1.1, 1, 1, 1 # (ปรับขนาดปุ่ม)
    ])
    with sub_col1:
        st.button("📝 List Search", use_container_width=True,
            type="primary" if active_sub == 'verify_list_search' else "secondary",
            on_click=set_verify_sub, args=('verify_list_search',)) # <--- แก้ไข args
    with sub_col2:
        st.button("📊 List Table", use_container_width=True,
            type="primary" if active_sub == 'verify_list_table' else "secondary",
            on_click=set_verify_sub, args=('verify_list_table',)) # <--- แก้ไข args
    with sub_col3:
        st.button("🔘 List Nav", use_container_width=True,
            type="primary" if active_sub == 'verify_list_nav' else "secondary",
            on_click=set_verify_sub, args=('verify_list_nav',)) # <--- แก้ไข args
    with sub_col4:
        st.button("🔍 Detail Page", use_container_width=True,
            type="primary" if active_sub == 'verify_detail_page' else "secondary",
            on_click=set_verify_sub, args=('verify_detail_page',)) # <--- แก้ไข args
    with sub_col5:
        st.button("↩️ Detail Back", use_container_width=True,
            type="primary" if active_sub == 'verify_detail_back' else "secondary",
            on_click=set_verify_sub, args=('verify_detail_back',)) # <--- แก้ไข args

    # --- (Container logic - ถูกต้องแล้ว) ---
    with st.container(border=True):
        if active_sub == 'verify_list_search':
            render_verify_list_actions_search(ws)
        elif active_sub == 'verify_list_table':
            render_verify_list_verification_table(ws)
        elif active_sub == 'verify_list_nav':
            render_verify_list_actions_navigate(ws)
        elif active_sub == 'verify_detail_page':
            render_verify_detail_page(ws)
        elif active_sub == 'verify_detail_back':
            render_verify_detail_actions_back(ws)

def render_teardown_phase(ws):
    """Phase 4: Teardown - (REVISED) 2 sub-sections"""
    st.markdown("### 🧹 Teardown Phase")

    # --- (เพิ่ม) State Management ---
    def set_teardown_sub(sub_name):
        st.session_state.teardown_active_sub = sub_name

    if 'teardown_active_sub' not in st.session_state:
        st.session_state.teardown_active_sub = 'suite_teardown'
    active_sub = st.session_state.teardown_active_sub

    # --- (เพิ่ม) Sub-navigation buttons ---
    sub_nav_col1, sub_nav_col2 = st.columns(2)
    with sub_nav_col1:
        st.button("🧹 Suite Teardown", use_container_width=True,
            type="primary" if active_sub == 'suite_teardown' else "secondary",
            on_click=set_teardown_sub, args=('suite_teardown',))
    with sub_nav_col2:
        st.button("🔧 Test Teardown", use_container_width=True,
            type="primary" if active_sub == 'test_teardown' else "secondary",
            on_click=set_teardown_sub, args=('test_teardown',))

    # --- (เปลี่ยน) Container logic ---
    with st.container(border=True):
        if active_sub == 'suite_teardown':
            render_suite_teardown_section(ws) # <--- เรียกฟังก์ชันใหม่ 1
        elif active_sub == 'test_teardown':
            render_test_teardown_section(ws) # <--- เรียกฟังก์ชันใหม่ 2


# ======= INDIVIDUAL SECTION RENDERERS =======

# --- Helper to open API/CSV dialog ---
def _open_api_csv_dialog(section_key):
    st.session_state['show_api_csv_dialog'] = True
    st.session_state['api_csv_dialog_context'] = {"key": section_key}
    if 'csv_api_dialog_selection' in st.session_state:
        del st.session_state['csv_api_dialog_selection'] # Clear previous selection
    st.rerun()

# --- Helper to open KW Factory dialog ---
def _open_kw_factory_dialog(section_key):
    _save_current_tab_state()
    st.session_state['show_kw_factory_dialog'] = True
    st.session_state['kw_factory_dialog_context'] = {"key": section_key}
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
    num_factory_kw = len(ws.get('keyword_factory_keywords', []))
    if num_factory_kw > 0:
        st.info(f"🏭 {num_factory_kw} custom keyword(s) available from Keyword Factory")

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
            render_step_card_compact(step, i, 'suite_setup', ws, manager, card_prefix="crud")

    # --- (MODIFIED) Add buttons in columns ---
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("➕ Add Step", use_container_width=True, key="crud_add_suite_setup"):
            st.session_state['show_crud_add_dialog'] = True
            st.session_state['crud_add_dialog_context'] = {"key": "suite_setup"}
            st.rerun()
    with col2:
        if st.button("⚡ Import KW API/CSV", use_container_width=True, key="crud_add_api_csv_setup"): # Changed label
            _open_api_csv_dialog("suite_setup")
    with col3: # Added
        if st.button("🏭 Import from KW Factory", use_container_width=True, key="crud_import_kw_setup"):
            _open_kw_factory_dialog("suite_setup")

def render_test_setup_section(ws):
    """Test Setup Section"""
    st.markdown("#### 🔧 Test Setup Steps")
    st.caption("Runs BEFORE EACH test case (usually empty for CRUD)")

    steps = ws['steps']['test_setup']

    if not steps:
        st.info("No test setup steps defined. This is optional.")
    else:
        for i, step in enumerate(steps):
            render_step_card_compact(step, i, 'test_setup', ws, manager, card_prefix="crud")

    # --- (MODIFIED) Add buttons in columns ---
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("➕ Add Test Setup Step", use_container_width=True, key="add_test_setup"):
            st.session_state['show_crud_add_dialog'] = True
            st.session_state['crud_add_dialog_context'] = {"key": "test_setup"}
            st.rerun()
    with col2:
        if st.button("⚡ Import KW API/CSV", use_container_width=True, key="crud_add_api_csv_test_setup"): # Changed label
            _open_api_csv_dialog("test_setup")
    with col3: # Added
        if st.button("🏭 Import from KW Factory", use_container_width=True, key="crud_import_kw_test_setup"):
            _open_kw_factory_dialog("test_setup")

def render_list_actions_section(ws):
    """List Page Actions Section"""
    st.markdown("#### 📝 Main List Page Actions")
    st.caption("Actions on the list/table page (Search, Click New, etc.)")

    steps = ws['steps']['action_list']

    if not steps:
        st.info("No actions yet. Typically: Search, Click 'New' button")
    else:
        for i, step in enumerate(steps):
            render_step_card_compact(step, i, 'action_list', ws, manager, card_prefix="crud")

    # --- (MODIFIED) Add buttons in columns ---
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add List Action Step", use_container_width=True, key="add_action_list"):
            st.session_state['show_crud_add_dialog'] = True
            st.session_state['crud_add_dialog_context'] = {"key": "action_list"}
            st.rerun()
    with col2: # Changed
        if st.button("🏭 Import from KW Factory", use_container_width=True, key="crud_import_kw_action_list"):
            _open_kw_factory_dialog("action_list")

def render_fill_form_section(ws):
    """Fill Form Section - Reads/Writes to 'action_form'"""
    st.markdown("#### ✏️ Fill Form Fields")
    st.caption("Add fill steps manually or import from Keyword Factory")

    # === (แก้ไข) อ่านจาก action_form และไม่กรอง ===
    section_key = 'action_form' 
    fill_steps = ws['steps'].get(section_key, []) 
    # === (สิ้นสุดการแก้ไข) ===

    if not fill_steps:
        st.info("No fill steps yet. Click 'Add Fill Step' or 'Import from Keyword Factory' below.")
    else:
        # (แสดง steps)
        for i, step in enumerate(fill_steps):
            render_step_card_compact(step, i, section_key, ws, manager, card_prefix="crud_form") # (ใช้ section_key)

    # --- (แก้ไข) Buttons ชี้ไปที่ action_form ---
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add Fill Step", use_container_width=True, key="add_fill_step"):
            _save_current_tab_state()
            st.session_state['show_crud_add_dialog'] = True
            st.session_state['crud_add_dialog_context'] = {"key": section_key, "filter": "fill"} # (ใช้ section_key)
            st.rerun()
    with col2:
        if st.button("🏭 Import from KW Factory", use_container_width=True, key="crud_import_kw_fill"):
            _save_current_tab_state()
            _open_kw_factory_dialog(section_key) # (ใช้ section_key)

def render_detail_actions_section(ws):
    """Detail Actions Section - Reads/Writes to 'action_detail'"""
    st.markdown("#### 🔘 Other Detail Actions")
    st.caption("Actions AFTER filling form (Save, Submit, Click Modal OK)")

    # === (แก้ไข) อ่านจาก action_detail และไม่กรอง ===
    section_key = 'action_detail'
    other_steps = ws['steps'].get(section_key, [])
    # === (สิ้นสุดการแก้ไข) ===

    if not other_steps:
        st.info("No other actions. Typically: Click Save, Click Modal OK")
    else:
        for i, step in enumerate(other_steps):
            render_step_card_compact(step, i, section_key, ws, manager, card_prefix="crud_detail_actions") # (ใช้ section_key)

    # --- (Buttons ชี้ไปที่ action_detail - ถูกต้องอยู่แล้ว) ---
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add Detail Action Step", use_container_width=True, key="add_action_detail"):
            _save_current_tab_state()
            st.session_state['show_crud_add_dialog'] = True
            st.session_state['crud_add_dialog_context'] = {"key": section_key}
            st.rerun()
    with col2:
        if st.button("🏭 Import from KW Factory", use_container_width=True, key="crud_import_kw_action_detail"):
            _save_current_tab_state()
            _open_kw_factory_dialog(section_key)

# (ฟังก์ชันใหม่ 1)
def render_verify_list_actions_search(ws):
    """(Verify Sub) 1. Main List Actions (Search)"""
    st.markdown("#### 📝 Main List Actions (Search)")
    st.caption("ขั้นตอนการค้นหาข้อมูลในตารางหลัก (Search, Wait)")

    # --- (แก้ไข) อ่านจาก list ใหม่ และ ไม่กรอง ---
    section_key = 'verify_list_search' # <-- Key ใหม่
    search_steps = ws['steps'].get(section_key, [])
    # --- (สิ้นสุดการแก้ไข) ---

    if not search_steps:
        st.info("ไม่พบขั้นตอนการค้นหา (Search, Wait).")
    else:
        for i, step in enumerate(search_steps):
            render_step_card_compact(step, i, section_key, ws, manager, card_prefix="crud_vlist_search") # (ใช้ section_key)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add Search/Wait Step", use_container_width=True, key="add_verify_list_search"): # (แก้ชื่อปุ่ม)
            st.session_state['show_crud_add_dialog'] = True
            st.session_state['crud_add_dialog_context'] = {"key": section_key} # (ใช้ section_key)
            st.rerun()
    with col2:
        if st.button("🏭 Import from KW Factory", use_container_width=True, key="crud_import_kw_verify_list_search"):
            _open_kw_factory_dialog(section_key) # (ใช้ section_key)

# (ฟังก์ชันใหม่ 2)
def render_verify_list_verification_table(ws):
    """(Verify Sub) 2. Main List Verification (Data Table)"""
    st.markdown("#### 📊 Main List Verification (Data Table)")
    st.caption("ขั้นตอนการตรวจสอบผลลัพธ์ในตาราง")

    # --- (แก้ไข) อ่านจาก list ใหม่ และ ไม่กรอง ---
    section_key = 'verify_list_table' # <-- Key ใหม่
    all_table_steps = ws['steps'].get(section_key, [])
    # --- (สิ้นสุดการแก้ไข) ---
    
    if not all_table_steps:
        # (ข้อความนี้จะแสดงเฉพาะตอน List ว่างจริงๆ)
        st.warning("ไม่พบขั้นตอนการตรวจสอบตาราง.") 
    else:
        # (แสดงผลทุก Step ที่อยู่ใน List นี้)
        for i, step in enumerate(all_table_steps):
            if step['keyword'] == 'Verify Result of data table':
                with st.expander(f"🔧 Edit Table Verification (Step {i+1})", expanded=True):
                    # Pass the correct section_key
                    render_step_toolbar(step, i, section_key, len(all_table_steps)) 
                    render_table_verification_ui(step, ws)
            else:
                # (เผื่อผู้ใช้ Add Step อื่นเข้ามา)
                render_step_card_compact(step, i, section_key, ws, manager, card_prefix="crud_vlist_table")

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add Table Verify Step", use_container_width=True, key="add_verify_list_table"): # (แก้ชื่อปุ่ม)
            st.session_state['show_crud_add_dialog'] = True
            st.session_state['crud_add_dialog_context'] = {"key": section_key} # (ใช้ section_key)
            st.rerun()
    with col2:
        if st.button("🏭 Import from KW Factory", use_container_width=True, key="crud_import_kw_verify_list_table"):
            _open_kw_factory_dialog(section_key) # (ใช้ section_key)

# (ฟังก์ชันใหม่ 3)
def render_verify_list_actions_navigate(ws):
    """(Verify Sub) 3. Main List Actions (Navigate to Detail)"""
    st.markdown("#### 🔘 Main List Actions (Navigate to Detail)")
    st.caption("ขั้นตอนการคลิกปุ่ม View/Edit เพื่อไปหน้า Detail")

    # --- (แก้ไข) อ่านจาก list ใหม่ และ ไม่กรอง ---
    section_key = 'verify_list_nav' # <-- Key ใหม่
    nav_steps = ws['steps'].get(section_key, [])
    # --- (สิ้นสุดการแก้ไข) ---

    if not nav_steps:
        st.info("ไม่พบขั้นตอนการคลิกปุ่ม View/Edit.")
    else:
        for i, step in enumerate(nav_steps):
            render_step_card_compact(step, i, section_key, ws, manager, card_prefix="crud_vlist_nav") # (ใช้ section_key)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add Navigation Step", use_container_width=True, key="add_verify_list_nav"):
            st.session_state['show_crud_add_dialog'] = True
            st.session_state['crud_add_dialog_context'] = {"key": section_key} # (ใช้ section_key)
            st.rerun()
    with col2:
        if st.button("🏭 Import from KW Factory", use_container_width=True, key="crud_import_kw_verify_list_nav"):
            _open_kw_factory_dialog(section_key) # (ใช้ section_key)

# (ฟังก์ชันใหม่ 4)
def render_verify_detail_page(ws):
    """(Verify Sub) 4. Verify Detail Page"""
    st.markdown("#### 🔍 Verify Detail Page")
    st.caption("Add verify steps manually or import from Keyword Factory")

    # --- (แก้ไข) อ่านจาก list ใหม่ และ ไม่กรอง ---
    section_key = 'verify_detail_page' # <-- Key ใหม่
    verify_steps = ws['steps'].get(section_key, [])
    # --- (สิ้นสุดการแก้ไข) ---

    if not verify_steps:
        st.info("No verify steps yet. Click 'Add Verify Step' or 'Import from Keyword Factory' below.")
    else:
        for i, step in enumerate(verify_steps):
            render_step_card_compact(step, i, section_key, ws, manager, card_prefix="crud_vdetail_page") # (ใช้ section_key)

    # --- Buttons ---
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add Verify Step", use_container_width=True, key="add_verify_detail_page"):
            st.session_state['show_crud_add_dialog'] = True
            st.session_state['crud_add_dialog_context'] = {"key": section_key, "filter": "verify"} # (ใช้ section_key)
            st.rerun()
    with col2:
        if st.button("🏭 Import from KW Factory", use_container_width=True, key="crud_import_kw_verify_detail_page"):
            _open_kw_factory_dialog(section_key) # (ใช้ section_key)

# (ฟังก์ชันใหม่ 5)
def render_verify_detail_actions_back(ws):
    """(Verify Sub) 5. Verify Detail Actions (Back)"""
    st.markdown("#### ↩️ Detail Actions (Back)")
    st.caption("ขั้นตอนการคลิกปุ่ม Back เพื่อกลับไปหน้า List")

    # --- (แก้ไข) อ่านจาก list ใหม่ และ ไม่กรอง ---
    section_key = 'verify_detail_back' # <-- Key ใหม่
    back_steps = ws['steps'].get(section_key, [])
    # --- (สิ้นสุดการแก้ไข) ---

    if not back_steps:
        st.info("ไม่พบขั้นตอนการคลิกปุ่ม Back.")
    else:
        for i, step in enumerate(back_steps):
            render_step_card_compact(step, i, section_key, ws, manager, card_prefix="crud_vdetail_back") # (ใช้ section_key)

    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("➕ Add Back Step", use_container_width=True, key="add_verify_detail_back"): # (แก้ชื่อปุ่ม)
            st.session_state['show_crud_add_dialog'] = True
            st.session_state['crud_add_dialog_context'] = {"key": section_key} # (ใช้ section_key)
            st.rerun()
    with col2:
        if st.button("🏭 Import from KW Factory", use_container_width=True, key="crud_import_kw_verify_detail_back"):
            _open_kw_factory_dialog(section_key) # (ใช้ section_key)

def render_suite_teardown_section(ws):
    """Suite Teardown Section (แยกออกมา)"""
    st.markdown("#### 🧹 Suite Teardown Steps")
    st.caption("Runs ONCE after all tests (Logout, Close Browser)")

    steps = ws['steps']['suite_teardown']

    if not steps:
        st.info("No teardown steps. Typically: Logout, Close All Browsers")
    else:
        for i, step in enumerate(steps):
            render_step_card_compact(step, i, 'suite_teardown', ws, manager, card_prefix="crud")

    # --- (มาจากโค้ดเดิม) 3 ปุ่มสำหรับ 'suite_teardown' ---
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("➕ Add Teardown Step", use_container_width=True, key="crud_add_suite_teardown"):
            st.session_state['show_crud_add_dialog'] = True
            st.session_state['crud_add_dialog_context'] = {"key": "suite_teardown"}
            st.rerun()
    with col2:
        if st.button("⚡ Import KW API/CSV", use_container_width=True, key="crud_add_api_csv_suite_teardown"):
            _open_api_csv_dialog("suite_teardown")
    with col3:
        if st.button("🏭 Import from KW Factory", use_container_width=True, key="crud_import_kw_suite_teardown"):
            _open_kw_factory_dialog("suite_teardown")

def render_test_teardown_section(ws):
    """Test Teardown Section (แยกออกมา)"""
    st.markdown("#### 🔧 Test Teardown Steps")
    st.caption("Runs AFTER EACH test case (Optional)")

    test_td_steps = ws['steps']['test_teardown']
    if not test_td_steps:
        st.info("No test teardown steps defined.")
    else:
        for i, step in enumerate(test_td_steps):
            render_step_card_compact(step, i, 'test_teardown', ws, manager, card_prefix="crud")

    # --- (มาจากโค้ดเดิม) 3 ปุ่มสำหรับ 'test_teardown' ---
    col_td1, col_td2, col_td3 = st.columns(3)
    with col_td1:
        if st.button("➕ Add Test Teardown Step", use_container_width=True, key="crud_add_test_teardown"):
            st.session_state['show_crud_add_dialog'] = True
            st.session_state['crud_add_dialog_context'] = {"key": "test_teardown"}
            st.rerun()
    with col_td2:
        if st.button("⚡ Import KW API/CSV", use_container_width=True, key="crud_add_api_csv_test_teardown"):
            _open_api_csv_dialog("test_teardown")
    with col_td3:
        if st.button("🏭 Import from KW Factory", use_container_width=True, key="crud_import_kw_test_teardown"):
            _open_kw_factory_dialog("test_teardown")

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
@st.dialog("Import Data Source or API Step", width="large") # (MODIFIED) Changed title
def render_api_csv_step_dialog():
    """
    Dialog to select and add CSV Data Source or API Service steps.
    (V3.11 - Enhanced with value insertion, Back button)
    (MODIFIED: Title)
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

        _restore_tab_state()
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


# ======= DIALOG: Import from Keyword Factory =======
@st.dialog("Import Keyword from Keyword Factory", width="large", dismissible=False)
def render_kw_factory_import_dialog():
      
    context = st.session_state.get('kw_factory_dialog_context', {})
    section_key = context.get("key")

    if not section_key:
        st.error("Error: Section context not found.")
        st.session_state['show_kw_factory_dialog'] = False
        st.rerun()
        return

    # Get Keyword Factory keywords and workspace
    ws = st.session_state.crud_generator_workspace
    ws_state = st.session_state.studio_workspace
    factory_keywords = ws.get('keyword_factory_keywords', [])

    # Initialize selection state
    if 'selected_factory_kw' not in st.session_state:
        st.session_state.selected_factory_kw = None
    
    selected_kw = st.session_state.selected_factory_kw
    
    # ✅ เคลียร์ค่าเก่าทุกครั้งที่เปิด dialog ใหม่
    if 'kw_factory_dialog_initialized' not in st.session_state:
        # เคลียร์ argument widget keys ทั้งหมด
        keys_to_clear = [key for key in st.session_state.keys() 
                        if key.startswith('kw_factory_arg_')]
        for key in keys_to_clear:
            del st.session_state[key]
        
        # เคลียร์ CSV quick insert keys
        csv_keys = [
            'quick_csv_ds_kw_factory',
            'quick_csv_row_kw_factory', 
            'quick_csv_col_kw_factory',
            'quick_csv_target_kw_factory'
        ]
        for key in csv_keys:
            if key in st.session_state:
                del st.session_state[key]
        
        st.session_state['kw_factory_dialog_initialized'] = True

    # Cleanup function
    def close_dialog():
        st.session_state['show_kw_factory_dialog'] = False
        if 'kw_factory_dialog_context' in st.session_state:
            del st.session_state['kw_factory_dialog_context']
        if 'selected_factory_kw' in st.session_state:
            del st.session_state['selected_factory_kw']
        
        # ✅ Reset initialization flag
        if 'kw_factory_dialog_initialized' in st.session_state:
            del st.session_state['kw_factory_dialog_initialized']
        
        # Clean up form inputs - เคลียร์ทั้งหมด
        keys_to_clear = [key for key in st.session_state.keys() 
                        if key.startswith('kw_factory_arg_')]
        for key in keys_to_clear:
            del st.session_state[key]
        
        # ✅ เคลียร์ CSV keys
        csv_keys = [
            'quick_csv_ds_kw_factory',
            'quick_csv_row_kw_factory',
            'quick_csv_col_kw_factory',
            'quick_csv_target_kw_factory',
            'quick_csv_insert_btn_kw_factory'
        ]
        for key in csv_keys:
            if key in st.session_state:
                del st.session_state[key]
        
        _restore_tab_state() # (MODIFIED) Restore tab state
        st.rerun()

    # Back Button
    if st.button("← Back to Workspace", key="back_kw_factory", type="primary"):
        close_dialog()
    
    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

    # Check if there are any keywords
    if not factory_keywords:
        st.info("🏭 No custom keywords found in Keyword Factory yet.")
        st.markdown("---")
        if st.button("❌ Close", use_container_width=True):
            close_dialog()
        return

    # Two Column Layout
    left_col, right_col = st.columns([0.45, 0.55], gap="medium")

# ========== LEFT COLUMN: Keyword Selection ==========
    with left_col:
        st.markdown("### 🔍 Select Keyword")
        
        # Search (เหมือนเดิม)
        search_query = st.text_input(
            "Search", 
            key="search_factory_kw",
            placeholder="🔎 Type to filter keywords...",
            label_visibility="collapsed"
        ).lower()

        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

        # Filter keywords (เหมือนเดิม)
        filtered_keywords = [
            kw for kw in factory_keywords 
            if search_query in kw.get('name', '').lower()
        ]

        if not filtered_keywords:
            st.warning(f"No keywords found matching '{search_query}'")
        else:           
            # === (เริ่มแก้ไขการแสดงผลปุ่ม) ===
            st.markdown("""
                <style>
                    /* Target buttons within the dialog's left column */
                    div[data-testid="stDialog"] .stButton button[kind="secondary"] {
                        justify-content: flex-start !important; /* Align text left */
                        text-align: left !important;
                    }
                </style>
            """, unsafe_allow_html=True)
            for kw in filtered_keywords:
                kw_name = kw.get('name', 'Untitled Keyword')
                kw_id = kw.get('id', kw_name)
                # (ลบ kw_args ออก ไม่ใช้แล้ว)
                
                # Check if selected
                is_selected = selected_kw and selected_kw.get('id') == kw_id
                
                # --- ใช้ Style คล้าย dialog_commonkw ---
                # (ใช้ icon + ชื่อ)
                icon = "⚙️" # Assume all factory keywords might have args
                button_label = f"{icon}  {kw_name}" 
                button_key = f"select_kw_{kw_id}"

                # ใช้ st.button แบบ secondary เสมอ
                if st.button(
                    button_label,
                    key=button_key,
                    use_container_width=True,
                    type="secondary" # <-- ใช้ secondary เสมอ
                ):
                    st.session_state.selected_factory_kw = kw
                    st.rerun()

                # --- เพิ่ม CSS สำหรับ Highlight ปุ่มที่เลือก ---
                # (เลียนแบบ dialog_commonkw แต่ใช้ key ของ dialog นี้)
                if is_selected:
                    button_test_id = f"stButton-secondary-{button_key}"
                    st.markdown(f'<style>.stButton button[data-testid="{button_test_id}"] {{ background-color: #316dca; border-color: #539bf5; color: #ffffff; font-weight: 600; box-shadow: 0 0 0 1px #539bf5; }}</style>', unsafe_allow_html=True)
            # === (สิ้นสุดการแก้ไขการแสดงผลปุ่ม) ===

# ========== RIGHT COLUMN: Configuration ==========
    with right_col:
        st.markdown(
                "<div style='font-size: 25px; font-weight: 600; margin-bottom: 0.5rem;'>⚙️ Configure Arguments</div>", 
                unsafe_allow_html=True
            )
        
        if not selected_kw:
            st.info("👈 Select a keyword from the left to configure its arguments")
        else:
            # === (2. Style Keyword Info like the image) ===
            with st.container(border=True): # Wrap in a bordered container
                # Use slightly larger font for name, keep doc as caption
                st.markdown(
                    f"<div style='font-size: 1.3rem; font-weight: 600; color: #1E90FF; margin-bottom: 0.2rem;'>{selected_kw.get('name')}</div>",
                    unsafe_allow_html=True
                )
                kw_doc = selected_kw.get('doc', '')
                if kw_doc:
                    st.caption(kw_doc)
                        
            kw_args = selected_kw.get('args', [])
            
            if not kw_args:
                st.info("ℹ️ This keyword has no arguments")
            else:              
                # CSV Quick Insert
                csv_keywords = extract_csv_datasource_keywords(ws_state)
                if csv_keywords and kw_args:
                    with st.expander("📊 Quick Insert from CSV Data", expanded=False):
                        st.caption("Insert CSV value into a specific argument")
                        
                        col_ds, col_test = st.columns([1, 1])
                        
                        quick_ds = None
                        with col_ds:
                            quick_ds = st.selectbox(
                                "Data Source",
                                options=list(csv_keywords.keys()),
                                key="quick_csv_ds_kw_factory"
                            )
                        
                        quick_row_val = ""
                        with col_test:
                            first_col_options = []
                            if quick_ds:
                                ds_info = csv_keywords.get(quick_ds, {})
                                csv_filename = ds_info.get('csv_filename', '')
                                project_path = st.session_state.get('project_path', '')
                                first_col_options = util_get_csv_first_column_values(project_path, csv_filename)
                            
                            if first_col_options:
                                quick_row_val = st.selectbox(
                                    "Row Data Key",
                                    options=first_col_options,
                                    key="quick_csv_row_kw_factory"
                                )
                            else:
                                quick_row_val = st.text_input(
                                    "Row Data Key",
                                    key="quick_csv_row_kw_factory",
                                    placeholder="e.g., robotapi"
                                )
                        
                        quick_col = None
                        col_column, col_target = st.columns([1, 1])
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
                                            key="quick_csv_col_kw_factory"
                                        )
                        
                        target_arg = None
                        with col_target:
                            # Get all text arguments (not locators, not presets)
                            text_args = []
                            for arg in kw_args:
                                arg_name = arg.get('name', '').strip('${}')
                                is_locator = any(s in arg_name.lower() for s in ['locator', 'field', 'button', 'element', 'menu'])
                                is_preset = arg_name in ARGUMENT_PRESETS
                                if not is_locator and not is_preset:
                                    text_args.append(arg_name)
                            
                            if text_args:
                                target_arg = st.selectbox(
                                    "Insert to →",
                                    options=text_args,
                                    key="quick_csv_target_kw_factory"
                                )
                            else:
                                st.caption("_No text args_")
                        
                        # Generate insert syntax
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
                            
                            # Insert button
                            if st.button("✅ Insert", type="primary", use_container_width=True, 
                                        key="quick_csv_insert_btn_kw_factory"):
                                if not target_arg:
                                    st.warning("Please select a target argument 'Insert to →'")
                                elif not quick_row_val:
                                    st.warning("Please enter a 'Row Key'")
                                elif insert_syntax:
                                    # Insert into session_state
                                    for i, arg in enumerate(kw_args):
                                        arg_name = arg.get('name', '').strip('${}')
                                        if arg_name == target_arg:
                                            key = f"kw_factory_arg_{selected_kw['id']}_{arg_name}_{i}"
                                            st.session_state[key] = insert_syntax
                                            st.toast(f"✅ Inserted '{insert_syntax}' into '{target_arg}'", icon="✅")
                                            st.rerun()
                                            break
                elif csv_keywords and not kw_args:
                    st.info("This keyword has no arguments.")
                
                if csv_keywords:
                    st.markdown("---")
                
                # Render argument inputs
                for i, arg in enumerate(kw_args):
                    # Copy arg to avoid mutating original
                    arg_info = arg.copy() if isinstance(arg, dict) else {'name': str(arg), 'default': ''}
                    arg_name = arg_info.get('name', f'arg_{i}')
                    
                    # Clean argument name
                    clean_arg_name = arg_name.strip('${}')
                    arg_info['name'] = clean_arg_name
                    
                    # Generate unique key
                    key = f"kw_factory_arg_{selected_kw['id']}_{clean_arg_name}_{i}"
                    
                    # Get current value from session_state (this is the key part!)
                    current_value_in_state = st.session_state.get(key)
                    
                    # ✅ Update arg_info['default'] with value from session_state
                    if current_value_in_state is not None:
                        arg_info['default'] = current_value_in_state
                    
                    # Render input
                    render_argument_input(
                        arg_info=arg_info,
                        ws_state=ws_state,
                        unique_key_prefix=key,
                        current_value=current_value_in_state,
                        selected_kw_name=selected_kw.get('name')
                    )
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Add button at bottom
            st.markdown("---")
            if st.button(
                f"✅ Import '{selected_kw.get('name')}'",
                type="primary",
                use_container_width=True,
                key="import_kw_factory_btn"
            ):
                # Collect argument values
                args_dict = {}
                for i, arg in enumerate(kw_args):
                    arg_name = arg.get('name', '')
                    clean_arg_name = arg_name.strip('${}') # (MODIFIED) Clean name
                    key = f"kw_factory_arg_{selected_kw['id']}_{clean_arg_name}_{i}" # (MODIFIED) Use clean name in key
                    args_dict[arg_name] = st.session_state.get(key, '')
                
                # Create step
                new_step = {
                    "id": str(uuid.uuid4()),
                    "keyword": selected_kw.get('name'),
                    "args": args_dict,
                    "type": "keyword_factory"
                }
                
                # Add step
                manager.add_step(section_key, new_step)
                
                # ✅ แสดง success แล้วปิด dialog (ไม่ sleep)
                st.success(f"✅ Imported '{selected_kw.get('name')}' successfully!")
                
                # ✅ ปิด dialog และ rerun
                close_dialog()

# ======= DIALOG: Fill Form =======
@st.dialog("จัดการฟอร์มทั้งหมด (Fill Form Fields)", width="large")
def render_fill_form_dialog():
    """Works with 'action_form'"""
    section_key = "action_form" # <--- แก้ไขตรงนี้
    ws = manager._get_workspace() # <-- Added _get_workspace() for consistency
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
        manager.add_fill_form_step(section_key) # <-- Use section_key
        st.rerun()
    st.markdown("---")

    # === CSV Quick Insert (ไม่ใช้ pending logic) ===
    with st.expander("📊 Quick Insert from CSV Data", expanded=False):
        st.caption("Select a value to insert into empty fields")
        csv_keywords = extract_csv_datasource_keywords(ws_state)
        
        if csv_keywords:
            col_ds, col_test = st.columns([1, 1])
            
            with col_ds:
                quick_ds = st.selectbox(
                    "Data Source",
                    options=list(csv_keywords.keys()),
                    key="quick_csv_ds_fill"
                )
            
            if quick_ds:
                ds_info = csv_keywords[quick_ds]
                headers = ds_info.get('headers', [])
                
                if headers:
                    with col_test:
                        first_col_options = []
                        if quick_ds:
                            ds_info = csv_keywords[quick_ds]
                            csv_filename = ds_info.get('csv_filename', '')
                            project_path = st.session_state.get('project_path', '')
                            first_col_options = util_get_csv_first_column_values(project_path, csv_filename)
                        
                        if first_col_options:
                            quick_row = st.selectbox(
                                "Row Data Key",
                                options=first_col_options,
                                key="quick_csv_row_fill"
                            )
                        else:
                            quick_row = st.text_input(
                                "Row Data Key",
                                key="quick_csv_row_fill",
                                placeholder="e.g., robotapi"
                            )
                    
                    with col_column:
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
                                # (แก้ไข) อ่าน steps จาก section_key ('action_form')
                                all_fill_steps_for_apply = [s for s in manager._get_workspace()['steps'][section_key] 
                                                        if s['keyword'] == 'Fill in data form']
                                
                                applied_count = 0
                                for step in all_fill_steps_for_apply: # <-- Use filtered list
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
        # (แก้ไข) อ่าน steps จาก section_key ('action_form')
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
                                    loc_name_to_find = selected_loc_obj.get('name') if isinstance(selected_loc_obj, dict) else selected_loc_obj
                                    if loc_name_to_find: # Added check
                                        loc_index = [loc.get('name') for loc in all_locators].index(loc_name_to_find)
                                except (ValueError, AttributeError, TypeError): # Added TypeError
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
                            # (Add handling for Select type if needed based on locator suffix)
                            
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
                                        switch_loc_name_to_find = selected_switch_loc_obj.get('name') if isinstance(selected_switch_loc_obj, dict) else selected_switch_loc_obj
                                        if switch_loc_name_to_find: # Added check
                                            switch_loc_index = [loc.get('name') for loc in all_locators].index(switch_loc_name_to_find)
                                    except (ValueError, AttributeError, TypeError): # Added TypeError
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
                            # (Checkbox does not need a value input here)
                            # else: 
                            #     st.caption("(No value needed)") # Removed for Checkbox

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
                    manager.delete_step(section_key, step_id) # <-- Use section_key
            
            updates_to_save = {}
            # (Re-fetch steps in case some were deleted)
            current_steps_in_section = [s for s in manager._get_workspace()['steps'][section_key] if s['keyword'] == 'Fill in data form']
            
            for step_id, data in form_data.items():
                if step_id not in steps_to_delete:
                    # Find original step based on current state after potential deletions
                    original_step = next((s for s in current_steps_in_section if s['id'] == step_id), None)
                    if original_step:
                        original_step_args = original_step.get('args', {})
                        
                        # Build new args based on form data for this step_id
                        new_args_for_step = {
                            "locator_field": data.get('locator_field'),
                            "value": data.get('value', ''), # Default empty if not Text/Select
                            "locator_switch_checked": data.get('locator_switch_checked'), # Default None if not Switch
                            "is_checkbox_type": data.get('input_type') == 'Checkbox',
                            "is_switch_type": data.get('input_type') == 'Switch',
                            # Preserve potentially existing args not directly edited here
                            "select_attribute": original_step_args.get('select_attribute', 'label'), 
                            "is_ant_design": original_step_args.get('is_ant_design', False)
                        }
                        # Clear value if it's not Text/Select
                        if new_args_for_step['is_checkbox_type'] or new_args_for_step['is_switch_type']:
                            new_args_for_step['value'] = '' # Or keep original? Let's clear for now.
                        # Clear switch locator if not Switch type
                        if not new_args_for_step['is_switch_type']:
                             new_args_for_step['locator_switch_checked'] = None # Or keep original? Let's clear.

                        # Compare with original args to see if update is needed
                        if new_args_for_step != original_step_args:
                            updates_to_save[step_id] = new_args_for_step

            if updates_to_save:
                # Use batch update if available, otherwise loop
                if hasattr(manager, 'batch_update_step_args'):
                    manager.batch_update_step_args(section_key, updates_to_save) # <-- Use section_key
                else: # Fallback if batch update doesn't exist
                    for step_id, new_args in updates_to_save.items():
                        manager.update_step_args(section_key, step_id, new_args) # <-- Use section_key

            # Close dialog state and clean up search/CSV state
            st.session_state.show_fill_form_dialog = False
            if 'fill_form_search' in st.session_state: 
                del st.session_state.fill_form_search
            
            csv_keys = [k for k in st.session_state.keys() if k.startswith('quick_csv_') and '_fill' in k]
            for key in csv_keys:
                if key in st.session_state: # Check if key exists before deleting
                    del st.session_state[key]
            
            st.rerun()

        if submitted_cancel:
            st.session_state.show_fill_form_dialog = False
            if 'fill_form_search' in st.session_state: 
                del st.session_state.fill_form_search
            # Clean up CSV state on cancel too
            csv_keys = [k for k in st.session_state.keys() if k.startswith('quick_csv_') and '_fill' in k]
            for key in csv_keys:
                 if key in st.session_state:
                     del st.session_state[key]
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
            col_ds, col_test = st.columns([1, 1])
            
            with col_ds:
                quick_ds = st.selectbox(
                    "Data Source",
                    options=list(csv_keywords.keys()),
                    key="quick_csv_ds_verify"
                )
            
            if quick_ds:
                ds_info = csv_keywords[quick_ds]
                headers = ds_info.get('headers', [])
                
                if headers:
                    with col_test:
                        first_col_options = []
                        if quick_ds:
                            ds_info = csv_keywords[quick_ds]
                            csv_filename = ds_info.get('csv_filename', '')
                            project_path = st.session_state.get('project_path', '')
                            first_col_options = util_get_csv_first_column_values(project_path, csv_filename)
                        
                        if first_col_options:
                            quick_row = st.selectbox(
                                "Row Data Key",
                                options=first_col_options,
                                key="quick_csv_row_verify"
                            )
                        else:
                            quick_row = st.text_input(
                                "Row Data Key",
                                key="quick_csv_row_verify",
                                placeholder="e.g., robotapi"
                            )
                        col_column, col_preview = st.columns([1, 1])
                    
                    with col_column:
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

def _save_current_tab_state():
    """บันทึก tab และ sub-section state ปัจจุบัน"""
    # บันทึก sub-sections ทุก phase
    if 'setup_active_sub' in st.session_state:
        st.session_state['saved_setup_sub'] = st.session_state['setup_active_sub']
    if 'actions_active_sub' in st.session_state:
        st.session_state['saved_actions_sub'] = st.session_state['actions_active_sub']
    if 'verify_active_sub' in st.session_state:
        st.session_state['saved_verify_sub'] = st.session_state['verify_active_sub']
    if 'teardown_active_sub' in st.session_state:
        st.session_state['saved_teardown_sub'] = st.session_state['teardown_active_sub']

def _restore_tab_state():
    """กู้คืน tab และ sub-section state ที่บันทึกไว้"""
    # กู้คืน sub-sections
    if 'saved_setup_sub' in st.session_state:
        st.session_state['setup_active_sub'] = st.session_state['saved_setup_sub']
    if 'saved_actions_sub' in st.session_state:
        st.session_state['actions_active_sub'] = st.session_state['saved_actions_sub']
    if 'saved_verify_sub' in st.session_state:
        st.session_state['verify_active_sub'] = st.session_state['saved_verify_sub']
    if 'saved_teardown_sub' in st.session_state:
        st.session_state['teardown_active_sub'] = st.session_state['saved_teardown_sub']