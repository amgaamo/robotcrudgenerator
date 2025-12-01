"""
Robot Framework Locator Generator - Main Application
Clean architecture with separated backend modules
"""

import streamlit as st
import os
from datetime import datetime
import streamlit.components.v1 as components
import base64
import pandas as pd
import uuid
import json 
import textwrap
import re
from streamlit_option_menu import option_menu
from bs4 import BeautifulSoup

# Backend imports
from modules.session_manager import init_session_state 
from modules.file_manager import (
    scan_robot_project, create_new_robot_file, 
    append_robot_content_intelligently, append_to_api_base,
    read_robot_variables_from_content
)

from modules.utils import (
    get_clean_locator_name, 
    get_file_icon,
    parse_robot_keywords,
    parse_data_sources
)

from modules.styles import get_css
from urllib.parse import urlparse
from modules.ui_test_flow import render_test_flow_tab
from modules.keyword_categorizer import (
    categorize_keywords, 
    get_category_stats, 
    get_expansion_config,
    get_category_priority
)

from modules.menu_locator_manager import render_menu_locator_manager

from modules.dialog_commonkw import render_add_step_dialog_base
from modules.crud_generator import manager as crud_manager
from modules.crud_generator.ui_crud import (
    render_crud_generator_tab,
    render_fill_form_dialog, 
    render_verify_detail_dialog, 
    render_api_csv_step_dialog
)
from modules import kw_manager
from modules.ui_keyword_factory import (
    render_keyword_factory_tab,
    render_kw_factory_fill_form_dialog, 
    render_kw_factory_verify_detail_dialog, 
    render_kw_factory_api_csv_step_dialog
)

from modules.checkbox_keywords_generator import (
    generate_checkbox_template_and_keyword,
    filter_checkbox_locators,
    separate_locators,
    detect_page_name_from_html,
    analyze_checkbox_structure
)

# HTML Parser
try:
    from modules.html_parser import HTMLLocatorParser, generate_robot_framework_variables
    PARSER_AVAILABLE = True
except ImportError:
    PARSER_AVAILABLE = False
    st.warning("HTML Parser module not found.")

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="RF Code Generator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply styles
st.markdown(get_css(), unsafe_allow_html=True)

# ============================================================================
# UI COMPONENTS - SIDEBAR
# ============================================================================

# ============================================================================
# UI COMPONENTS - HELPER FUNCTION FOR COPY BUTTON (เพิ่มใหม่)
# ============================================================================

def copy_button_component(text_to_copy, button_key):
    """
    Ultimate Modern Copy Button - Original beautiful design.
    """
    import base64
    text_bytes = text_to_copy.encode('utf-8')
    b64_text = base64.b64encode(text_bytes).decode()

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            html, body {{
                width: 100%; height: 100%;
                background: transparent !important;
                overflow: hidden;
                display: flex; justify-content: center; align-items: center;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }}
            .copy-button {{
                width: 34px; height: 34px;
                padding: 0;
                background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
                border: 1.5px solid #334155;
                border-radius: 10px;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1);
                color: #94a3b8;
                font-size: 0.9rem;
                display: flex; justify-content: center; align-items: center;
                cursor: pointer;
                transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                position: relative;
                user-select: none; -webkit-user-select: none;
            }}
            .copy-button:hover {{
                background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
                color: #ffffff;
                transform: translateY(-3px) scale(1.05);
                box-shadow: 0 8px 24px rgba(99, 102, 241, 0.5), 0 0 0 4px rgba(99, 102, 241, 0.2);
            }}
            .copy-button:active {{
                transform: translateY(-1px) scale(0.98);
                box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
            }}
            .copy-button.success {{
                background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
                color: #ffffff !important;
                box-shadow: 0 0 30px rgba(16, 185, 129, 0.6), 0 0 0 4px rgba(16, 185, 129, 0.2) !important;
                animation: successPop 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            }}
            @keyframes successPop {{ 0% {{ transform: scale(1); }} 50% {{ transform: scale(1.2); }} 100% {{ transform: scale(1); }} }}
            .copy-button i {{ transition: all 0.3s ease; }}
            .copy-button:hover i {{ transform: scale(1.15) rotate(-5deg); }}
        </style>
    </head>
    <body>
        <button class="copy-button" id="{button_key}" aria-label="Copy to clipboard">
            <i class="bi bi-copy"></i>
        </button>
        <script>
            const button = document.getElementById('{button_key}');
            let isProcessing = false;
            button.onclick = async function(e) {{
                e.preventDefault();
                if (isProcessing) return;
                isProcessing = true;
                const text = atob('{b64_text}');
                try {{
                    await navigator.clipboard.writeText(text);
                    button.classList.add('success');
                    button.innerHTML = '<i class="bi bi-check-lg"></i>';
                    setTimeout(() => {{
                        button.classList.remove('success');
                        button.innerHTML = '<i class="bi bi-copy"></i>';
                        isProcessing = false;
                    }}, 1500);
                }} catch (err) {{
                    console.error('Copy failed:', err);
                }}
            }};
        </script>
    </body>
    </html>
    """
    return html

def render_sidebar():
    """Render sidebar with project navigation"""
    with st.sidebar:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### 📁 Project Path")
        project_path = st.text_input(
            "Project Root",
            value=st.session_state.project_path,
            placeholder="C:/projects/my-robot-project",
            label_visibility="collapsed"
        )

        col1, col2 = st.columns(2)
        with col1:
            if st.button("📂 Set", width='stretch', key="sidebar_set"):
                if project_path:
                    st.session_state.project_path = project_path
                    st.session_state.project_structure = scan_robot_project(project_path)
                    
                    # ✅ รีเซ็ตการโหลด datasources และ locators
                    st.session_state.datasources_auto_loaded = False
                    st.session_state.locators_auto_loaded = False
                    st.session_state.project_keywords_auto_imported = False
                    
                    st.rerun()

        with col2:
            if st.button("🔄 Clear", width='stretch', key="sidebar_clear"):
                st.session_state.project_path = ""
                st.session_state.project_structure = {}
                
                # ✅ รีเซ็ตการโหลด datasources และ locators
                st.session_state.datasources_auto_loaded = False
                st.session_state.locators_auto_loaded = False
                st.session_state.project_keywords_auto_imported = False
                
                st.rerun()

        if st.session_state.project_structure and st.session_state.project_structure.get('folders'):
            st.markdown("---")
            structure = st.session_state.project_structure
            project_name = os.path.basename(st.session_state.project_path)

            st.markdown(f"#### 📦 {project_name}")

            col1, col2 = st.columns([4, 1])
            with col1:
                path_html = f"""
                <div style="font-size: 0.8rem; color: var(--text-dark); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; padding-top: 8px;"
                     title="{st.session_state.project_path}">
                    {st.session_state.project_path}
                </div>
                """
                st.markdown(path_html, unsafe_allow_html=True)
            with col2:
                copy_button_component(st.session_state.project_path, "copy_root_btn")

            st.markdown("---")
            render_folder_tree(structure)
            st.markdown("---")

            col1, col2 = st.columns(2)
            with col1:
                st.metric("📁 Folders", len(structure['folders']))
            with col2:
                st.metric("📄 Files", len(structure['robot_files']))

        st.markdown("---")
        with st.expander("⚙️ Settings", expanded=False):
            st.markdown("**Locator Priority:**")
            st.caption("1️⃣ Unique ID")
            st.caption("2️⃣ Unique Name")
            st.caption("3️⃣ ID + Placeholder")
            st.caption("4️⃣ FormControlName")
            st.caption("5️⃣ Label-based")
            st.caption("6️⃣ Display fields")

        st.markdown("---")
        with st.expander("ℹ️ About", expanded=False):
            st.caption("Version: 1.1.1")
            st.caption("Enhanced with modular backend")
            st.caption("Separated frontend and backend")
            st.caption("Enhanced with collapsible folders")
            st.caption("Professional dark theme")

def render_folder_tree(structure):
    """Render beautiful collapsible folder tree - Redesigned"""
    # --- REMOVED: All previous CSS injection hacks ---
    
    root_path = structure['root']
    folders = structure['folders']
    robot_files = structure['robot_files']
    csv_files = structure.get('csv_files', [])
    all_files = robot_files + csv_files

    files_by_folder = {key: [] for key in folders.keys()}

    for file_path in all_files:
        file_path_slashed = file_path.replace(os.sep, '/')
        best_match_key = ''
        for folder_key in folders.keys():
            if file_path_slashed.startswith(folder_key + '/') and len(folder_key) > len(best_match_key):
                best_match_key = folder_key
        if not best_match_key:
            top_level_folder = file_path_slashed.split('/')[0]
            if top_level_folder in files_by_folder:
                best_match_key = top_level_folder
        if best_match_key:
            files_by_folder[best_match_key].append(file_path)

    sorted_folders = sorted(folders.items(), key=lambda item: str(item[0]))

    for folder_name, folder_path in sorted_folders:
        folder_files = files_by_folder.get(folder_name, [])
        if folder_name not in st.session_state.expanded_folders:
            st.session_state.expanded_folders[folder_name] = False
        is_expanded = st.session_state.expanded_folders[folder_name]

        indent_level = folder_name.count('/')
        display_folder_name = folder_name.split('/')[-1]
        
        folder_icon = "📂" if is_expanded else "📁"
        toggle_icon = "▼" if is_expanded else "▶"
        
        col_folder, col_copy = st.columns([4, 1])
        
        with col_folder:
            if st.button(
                f"{toggle_icon}  {folder_icon} {display_folder_name}/  `{len(folder_files)}`",
                key=f"folder_btn_{folder_name}",
                width='stretch',
                help="Click to expand/collapse"
            ):
                st.session_state.expanded_folders[folder_name] = not is_expanded
                st.rerun()
            
            st.markdown("""
            <style>
                /* ทำให้ Rule นี้เจาะจงเฉพาะปุ่ม folder ใน Sidebar เท่านั้น */
                [data-testid="stSidebar"] button[kind="secondary"][key*="folder_btn_"] {
                    background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(51, 65, 85, 0.4) 100%) !important;
                    backdrop-filter: blur(12px);
                    border: 1px solid rgba(99, 102, 241, 0.3) !important;
                    border-left: 3px solid #6366f1 !important;
                    border-radius: 10px !important;
                    color: #cbd5e1 !important;
                    text-align: left !important;
                    padding: 10px 16px !important;
                    transition: all 0.3s ease !important;
                    /* เพิ่มเติม: ป้องกันการสืบทอดสไตล์ที่ไม่ต้องการ */
                    height: auto !important; /* ให้ความสูงกลับเป็นปกติ */
                    min-height: auto !important;
                    font-size: inherit !important; /* ใช้ font size ปกติ */
                    line-height: inherit !important; /* ใช้ line height ปกติ */
                    justify-content: flex-start !important; /* จัดชิดซ้ายเหมือนเดิม */
                }
                [data-testid="stSidebar"] button[kind="secondary"][key*="folder_btn_"]:hover {
                    border-color: rgba(129, 140, 248, 0.5) !important;
                    box-shadow: 0 4px 16px rgba(99, 102, 241, 0.25) !important;
                    transform: translateX(2px) !important;
                    /* เพิ่มเติม: ป้องกันการสืบทอดสไตล์ที่ไม่ต้องการ */
                    background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(51, 65, 85, 0.4) 100%) !important; /* ป้องกัน hover จาก style.py */
                    filter: none !important;
                }
                 /* เพิ่มเติม: ทำให้ปุ่มอื่นใน Sidebar (ถ้ามี) ไม่โดนผลกระทบจาก style.py */
                [data-testid="stSidebar"] .stButton button:not([key*="folder_btn_"]) {
                    /* อาจจะใส่ default style ของปุ่ม sidebar อื่นๆ ที่นี่ ถ้าต้องการ */
                }
            </style>
            """, unsafe_allow_html=True)
        
        with col_copy:
            # --- REVERTED: Restored original height ---
            components.html(
                copy_button_component(folder_path, f"copy_folder_{folder_name}_btn"), 
                height=48,
                scrolling=False
            )
        
        if is_expanded and folder_files:
            sorted_files = sorted(folder_files)
            
            for i, file_path in enumerate(sorted_files):
                relative_to_folder = os.path.relpath(file_path.replace(os.sep, '/'), folder_name).replace(os.sep, '/')
                parts = relative_to_folder.split('/')
                file_name = parts[-1]
                subfolder_path = '/'.join(parts[:-1])
                
                col_file, col_copy_file = st.columns([4, 1])
                
                with col_file:
                    file_icon = get_file_icon(file_name)
                    display_name = f"{subfolder_path}/{file_name}" if subfolder_path else file_name
                    full_file_path = os.path.join(root_path, file_path)
                    is_last = i == len(sorted_files) - 1
                    
                    file_html = f"""
                    <div style='
                        display: flex;
                        align-items: center;
                        gap: 10px;
                        padding-left: 40px;
                        padding-right: 12px;
                        min-height: 40px; 
                        border-radius: 8px;
                        transition: background 0.2s ease-in-out;
                        cursor: pointer;
                    ' onmouseover="this.style.background='rgba(51, 65, 85, 0.4)';" 
                       onmouseout="this.style.background='transparent';"
                       title="{full_file_path}">
                        <span style='color: #64748b; font-family: monospace; font-size: 1rem;'>
                            {'└─' if is_last else '├─'}
                        </span>
                        <span style='font-size: 1.1rem; margin-top: 2px;'>{file_icon}</span>
                        <span style='
                            color: #cbd5e1;
                            font-size: 0.9rem;
                            font-weight: 500;
                            white-space: nowrap;
                            overflow: hidden;
                            text-overflow: ellipsis;
                        '>
                            {display_name}
                        </span>
                    </div>
                    """
                    st.markdown(file_html, unsafe_allow_html=True)
                
                with col_copy_file:
                    safe_key = file_path.replace(os.sep, '_').replace('/', '_').replace('.', '_')
                    # --- REVERTED: Restored original height ---
                    components.html(
                        copy_button_component(full_file_path, f"copy_file_{safe_key}_btn"), 
                        height=40,
                        scrolling=False
                    )
        
        if indent_level == 0:
            st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)

# ============================================================================
# UI COMPONENTS - MAIN HEADER
# ============================================================================

def render_header():
    """Render main header with enhanced description"""
    header_html = """
    <div style='text-align: center; padding: 0.5rem 0 0.1rem 0;'>
        <h1 class='app-header-title'>
            🤖 Robot Framework Code Generator
        </h1>
        <p style='color: var(--text-muted); font-size: 1rem; margin: 0; line-height: 1.5;'>
            ⚡ <strong>Automate locator generation</strong> · 
            🎯 <strong>Create CRUD tests instantly</strong> · 
            🚀 <strong>Boost productivity</strong>
        </p>
        <p style='color: var(--text-dark); font-size: 0.85rem; margin-top: 0.3rem;'>
            Save hours of manual coding with intelligent HTML parsing and template generation
        </p><br><br>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

# ============================================================================
# Studio Workspace
# ============================================================================


def render_timeline_view():
    """Renders the UI for the Timeline view."""
    ws_state = st.session_state.studio_workspace
    st.subheader("📈 Timeline Editor")
    st.caption("Build your test case by adding steps to the timeline below.")

    # --- ส่วนแสดงผล Timeline ---
    
    # แสดง Anchor เริ่มต้น
    st.markdown("##### --- SUITE SETUP ---")
    
    # Placeholder สำหรับปุ่ม Add Step (จะทำงานใน Step ถัดไป)
    if st.button("⊕ Add Step to Setup", width='stretch', key="add_step_setup"):
        st.info("Command Palette for adding steps will be implemented next.")

    st.markdown("---")
    st.markdown("##### --- TEST CASE ---")

    # แสดง Steps ที่ผู้ใช้สร้างขึ้นมา
    if not ws_state['timeline']:
        st.info("Your timeline is empty. Click 'Add Step' to begin.")
    
    for i, step in enumerate(ws_state['timeline']):
        with st.container(border=True):
            col_content, col_actions = st.columns([4, 1])
            with col_content:
                st.markdown(f"**{i + 1}. {step['keyword']}**")
                # แสดง Arguments แบบย่อ
                args_summary = ", ".join([f"{k}='{v}'" for k, v in step['args'].items()])
                st.caption(args_summary)
            
            with col_actions:
                # --- จัดการปุ่ม Actions ---
                # ปุ่มเลื่อนขึ้น (ถ้าไม่ใช่ Step แรก)
                if i > 0:
                    if st.button("🔼", key=f"up_{i}", help="Move step up"):
                        ws_state['timeline'].insert(i - 1, ws_state['timeline'].pop(i))
                        st.rerun()
                
                # ปุ่มเลื่อนลง (ถ้าไม่ใช่ Step สุดท้าย)
                if i < len(ws_state['timeline']) - 1:
                    if st.button("🔽", key=f"down_{i}", help="Move step down"):
                        ws_state['timeline'].insert(i + 1, ws_state['timeline'].pop(i))
                        st.rerun()

                # ปุ่มลบ
                if st.button("🗑️", key=f"del_{i}", help="Delete step"):
                    ws_state['timeline'].pop(i)
                    st.rerun()

        # Placeholder สำหรับปุ่ม Add Step ระหว่างทาง
        if st.button(f"⊕ Add Step Here", width='stretch', key=f"add_step_after_{i}"):
            st.info("Command Palette for adding steps will be implemented next.")

    st.markdown("---")
    st.markdown("##### --- SUITE TEARDOWN ---")
    if st.button("⊕ Add Step to Teardown", width='stretch', key="add_step_teardown"):
        st.info("Command Palette for adding steps will be implemented next.")

def csv_creator_dialog():
    """Renders the dialog for creating or uploading a CSV file with full logic for both modes."""
    ws_state = st.session_state.studio_workspace

    @st.dialog("Create/Upload CSV Data", width="large")
    def csv_creator():
        st.markdown("#### <i class='fa-solid fa-file-csv'></i> Create or Upload CSV Data", unsafe_allow_html=True)
        
        mode = st.radio(
            "Create From:", ["New File", "Upload Existing File"],
            index=0 if ws_state.get('csv_creator_mode', 'New File') == 'New File' else 1,
            horizontal=True, label_visibility="collapsed"
        )
        ws_state['csv_creator_mode'] = mode
        st.markdown("---")

# ==================== MODE 1: CREATE NEW FILE ====================
        if mode == "New File":
            st.subheader("Create a New CSV File")

            # --- Step 1: กำหนดชื่อไฟล์ ---
            filename_input = st.text_input(
                "1. New File Name (in 'datatest' folder)", 
                value=ws_state.get('csv_new_filename', ''),
                key="csv_new_filename_input",
                placeholder="e.g., login_data.csv"
            )
            ws_state['csv_new_filename'] = filename_input

            # --- Step 2: กำหนดคอลัมน์ ---
            columns_input = st.text_input(
                "2. Define Columns (comma-separated)", 
                value=ws_state.get('csv_new_columns_str', ''),
                key="csv_new_columns_input",
                placeholder="e.g., username,password,role"
            )
            
            # ตรวจสอบว่ามีการเปลี่ยนแปลง columns หรือไม่
            if columns_input != ws_state.get('csv_new_columns_str', ''):
                ws_state['csv_new_columns_str'] = columns_input
                
                if columns_input.strip():
                    columns = [col.strip() for col in columns_input.split(',') if col.strip()]
                    if columns:
                        # เก็บ columns list
                        ws_state['csv_columns_list'] = columns
                        # สร้าง list สำหรับเก็บ rows
                        if 'csv_rows_data' not in ws_state:
                            ws_state['csv_rows_data'] = []
                        st.success(f"✅ Created table with {len(columns)} columns!")
                        st.rerun()
                    else:
                        ws_state['csv_columns_list'] = None
                        ws_state['csv_rows_data'] = []
                else:
                    ws_state['csv_columns_list'] = None
                    ws_state['csv_rows_data'] = []

            # --- Step 3: เพิ่มและจัดการข้อมูล ---
            if ws_state.get('csv_columns_list'):
                st.markdown("---")
                st.caption("3. Add Data Rows")
                
                columns = ws_state['csv_columns_list']
                
                # 📝 ฟอร์มสำหรับเพิ่มแถวใหม่
                with st.expander("➕ Add New Row", expanded=True):
                    st.markdown("**Fill in the values for each column:**")
                    
                    # สร้าง input fields สำหรับแต่ละคอลัมน์
                    new_row_data = {}
                    
                    # แบ่ง columns เป็น 2 คอลัมน์ต่อแถว
                    num_cols = len(columns)
                    cols_per_row = 2
                    
                    for i in range(0, num_cols, cols_per_row):
                        cols = st.columns(cols_per_row)
                        
                        for j in range(cols_per_row):
                            idx = i + j
                            if idx < num_cols:
                                col_name = columns[idx]
                                with cols[j]:
                                    new_row_data[col_name] = st.text_input(
                                        f"**{col_name}**",
                                        key=f"new_row_input_{col_name}",
                                        placeholder=f"Enter {col_name}..."
                                    )
                    
                    st.markdown("<div style='margin: 1rem 0;'></div>", unsafe_allow_html=True)
                    
                    col_add, col_clear = st.columns([1, 1])
                    
                    with col_add:
                        if st.button("✅ Add Row", type="primary", width='stretch', key="add_row_btn"):
                            # ตรวจสอบว่ามีข้อมูลอย่างน้อย 1 field
                            if any(value.strip() for value in new_row_data.values()):
                                if 'csv_rows_data' not in ws_state:
                                    ws_state['csv_rows_data'] = []
                                
                                ws_state['csv_rows_data'].append(new_row_data.copy())
                                st.success(f"✅ Row {len(ws_state['csv_rows_data'])} added!")
                                st.rerun()
                            else:
                                st.warning("⚠️ Please fill in at least one field.")
                    
                    with col_clear:
                        if st.button("🔄 Clear Form", width='stretch', key="clear_form_btn"):
                            st.rerun()

                # 📊 แสดงตารางข้อมูลที่มีอยู่
                st.markdown("---")
                
                if ws_state.get('csv_rows_data'):
                    st.markdown(f"**📋 Data Table ({len(ws_state['csv_rows_data'])} rows)**")
                    st.caption("💡 Click '+' to add row, click cell to edit, click '×' to delete row")
                    
                    # สร้าง DataFrame
                    df = pd.DataFrame(ws_state['csv_rows_data'], columns=columns)
                    
                    # แสดง data_editor พร้อมปุ่มลบในแต่ละแถว
                    edited_df = st.data_editor(
                        df,
                        num_rows="dynamic",  # ให้เพิ่มและลบแถวได้
                        width='stretch',
                        hide_index=False,
                        key="simple_data_editor"
                    )
                    
                    # อัปเดตข้อมูลกลับ
                    ws_state['csv_rows_data'] = edited_df.to_dict('records')
                    
                else:
                    st.info("ℹ️ No data rows added yet. Use the form above to add your first row.")
            
            st.markdown("---")
            
            # --- Step 4: ปุ่ม Save ---
            save_col1, save_col2 = st.columns([1, 1])
            
            with save_col1:
                save_disabled = (
                    not ws_state.get('csv_new_filename') or 
                    not ws_state.get('csv_columns_list') or 
                    not ws_state.get('csv_rows_data')
                )
                
                if st.button(
                    "💾 Save to datatest folder", 
                    type="primary", 
                    width='stretch', 
                    key="save_new_csv",
                    disabled=save_disabled
                ):
                    if not st.session_state.project_path:
                        st.error("⚠️ Please set the project path in the sidebar first.")
                    else:
                        # สร้าง DataFrame จาก rows data
                        df = pd.DataFrame(
                            ws_state['csv_rows_data'], 
                            columns=ws_state['csv_columns_list']
                        )
                        
                        # เรียกใช้ฟังก์ชัน save
                        if save_df_to_csv(
                            st.session_state.project_path, 
                            ws_state['csv_new_filename'], 
                            df
                        ):
                            st.success(f"✅ File '{ws_state['csv_new_filename']}' saved successfully!")
                            st.session_state.project_structure = scan_robot_project(st.session_state.project_path)
                            # รีเซ็ตค่า
                            ws_state['csv_new_filename'] = ''
                            ws_state['csv_new_columns_str'] = ''
                            ws_state['csv_columns_list'] = None
                            ws_state['csv_rows_data'] = []
                            ws_state['show_csv_creator'] = False
                            st.rerun()
            
            with save_col2:
                if st.button(
                    "❌ Cancel", 
                    width='stretch', 
                    key="cancel_new_csv"
                ):
                    # รีเซ็ตค่า
                    ws_state['csv_new_filename'] = ''
                    ws_state['csv_new_columns_str'] = ''
                    ws_state['csv_columns_list'] = None
                    ws_state['csv_rows_data'] = []
                    ws_state['show_csv_creator'] = False
                    st.rerun()
            
            # แสดงสถานะปัจจุบัน
            if ws_state.get('csv_rows_data'):
                st.caption(f"📊 Ready to save: {len(ws_state['csv_rows_data'])} rows x {len(ws_state['csv_columns_list'])} columns")

        # ==================== MODE 2: UPLOAD EXISTING FILE ====================
        elif mode == "Upload Existing File":
            st.subheader("Upload and Edit an Existing CSV")
            
            uploaded_file = st.file_uploader(
                "1. Upload your CSV file", 
                type=['csv'], 
                key="csv_uploader_mode"
            )
            
            if uploaded_file is not None:
                # ตรวจสอบว่าเป็นไฟล์ใหม่หรือไม่
                if uploaded_file.name != ws_state.get('csv_uploaded_filename'):
                    ws_state['csv_uploaded_filename'] = uploaded_file.name
                    ws_state['csv_save_as_name'] = uploaded_file.name
                    
                    try:
                        # อ่านไฟล์ CSV
                        df = pd.read_csv(uploaded_file)
                        ws_state['csv_uploaded_data'] = df
                        st.success(f"✅ Loaded {len(df)} rows and {len(df.columns)} columns!")
                    except Exception as e:
                        st.error(f"❌ Failed to read CSV file: {e}")
                        ws_state['csv_uploaded_data'] = None

                # แสดงส่วน Edit
                if ws_state.get('csv_uploaded_data') is not None:
                    st.text_input(
                        "2. Save As (you can rename the file)", 
                        value=ws_state.get('csv_save_as_name', ''),
                        key="csv_save_as_input",
                        on_change=lambda: ws_state.update({
                            'csv_save_as_name': st.session_state.csv_save_as_input
                        })
                    )
                    
                    st.caption("3. Edit Data")
                    edited_df = st.data_editor(
                        ws_state['csv_uploaded_data'], 
                        num_rows="dynamic", 
                        width='stretch', 
                        key="csv_data_editor_upload"
                    )
                    ws_state['csv_uploaded_data'] = edited_df
                    
                    st.caption(f"Current rows: {len(edited_df)}")

            st.markdown("---")
            
            # ปุ่ม Save สำหรับ Upload mode
            if st.button("💾 Save to datatest folder", type="primary", width='stretch', key="save_uploaded_csv"):
                if not ws_state.get('csv_save_as_name'):
                    st.error("⚠️ Please provide a 'Save As' name.")
                elif ws_state.get('csv_uploaded_data') is None:
                    st.error("⚠️ Please upload a file first.")
                elif not st.session_state.project_path:
                    st.error("⚠️ Please set the project path in the sidebar first.")
                else:
                    if save_df_to_csv(
                        st.session_state.project_path, 
                        ws_state['csv_save_as_name'], 
                        ws_state['csv_uploaded_data']
                    ):
                        st.success(f"✅ File '{ws_state['csv_save_as_name']}' saved successfully!")
                        st.session_state.project_structure = scan_robot_project(st.session_state.project_path)
                        # รีเซ็ตค่า
                        ws_state['csv_uploaded_filename'] = None
                        ws_state['csv_save_as_name'] = ''
                        ws_state['csv_uploaded_data'] = None
                        ws_state['show_csv_creator'] = False
                        st.rerun()

    csv_creator()

def save_df_to_csv(project_path, filename, dataframe):
    """
    Save a pandas DataFrame to a CSV file in the 'datatest' folder.
    
    Args:
        project_path (str): Root path of the project
        filename (str): Name of the CSV file (with or without .csv extension)
        dataframe (pd.DataFrame): The DataFrame to save
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # ตรวจสอบว่ามี .csv extension หรือไม่
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        # สร้างพาธไปยังโฟลเดอร์ datatest
        datatest_folder = os.path.join(project_path, 'resources', 'datatest')
        
        # สร้างโฟลเดอร์ถ้ายังไม่มี
        os.makedirs(datatest_folder, exist_ok=True)
        
        # พาธเต็มของไฟล์
        full_path = os.path.join(datatest_folder, filename)
        
        # บันทึกไฟล์
        dataframe.to_csv(full_path, index=False, encoding='utf-8')
        
        st.info(f"📂 Saved to: {full_path}")
        return True
        
    except Exception as e:
        st.error(f"❌ Error saving file: {str(e)}")
        return False


# ในไฟล์ app.py

def data_source_export_dialog(source, index):
    """
    Renders the dialog to show, copy, and save the generated code for a data source.
    (FIXED: Correctly generates strings and defaults the save path)
    """
    @st.dialog(f"Export Code for: {source.get('name', '').upper()}", width="large")
    def export_dialog():
        ds_name = source.get('name')
        csv_file = source.get('file_name')
        col_name = source.get('col_name')

        if not ds_name or not csv_file or not col_name:
            st.error("Please provide both Data Source Name and CSV File Name and Column Name.")
            return

        col_var = col_name 

        # --- สร้างโค้ดเป็น String ที่ถูกต้อง ---
        name_upper_no_space = ds_name.replace(" ", "").upper()
        var_name = f"CSVPATH_{name_upper_no_space}"
        kw_name = f"Import DataSource {ds_name.upper()}"
        ds_var = f"{name_upper_no_space}"
        
        var_code = f"${{{var_name}}}            ${{CURDIR}}${{/}}datatest${{/}}{csv_file}"
        kw_code = (
            f"\n{kw_name}\n"
            f"    Import datasource file        ${{{var_name}}}\n"
            f"    Set Global Variable           ${{{col_var}}}                             ${{value_col}}\n"
            f"    Set Global Variable           ${{{ds_var}}}                              ${{datasource_val}}"
        )

        # --- UI for Code Display ---
        st.markdown("<h3><b>*** Variables ***</b></h3>", unsafe_allow_html=True)
        st.code(var_code, language="robotframework")

        st.markdown("<h3><b>*** Keywords ***</b></h3>", unsafe_allow_html=True)
        st.code(kw_code, language="robotframework")

        # --- UI for Saving to File ---
        st.markdown("---")
        st.subheader("💾 Save to Project File")
        
        if st.button("Append to datasources.resource", type="primary"):
            project_path = st.session_state.project_path
            if not project_path:
                st.error("Please set the project path in the sidebar first.")
            else:
                target_path = os.path.join(project_path, "resources", "datasources.resource")

                # --- START: ส่วนที่แก้ไข ---
                # เปลี่ยนไปเรียกใช้ฟังก์ชันใหม่ที่ฉลาดกว่า
                success, message = append_robot_content_intelligently(
                    target_path, 
                    variables_code=var_code, 
                    keywords_code=kw_code
                )
                
                if success:
                    # --- แก้ไขตรงนี้ ---
                    relative_path = os.path.relpath(target_path, st.session_state.project_path)
                    # เปลี่ยนจาก st.success หรือ st.toast เป็นการตั้งค่า state
                    st.toast(f"✅ Appended to: `{relative_path}`", icon="🎉")
                    return
                    # --- สิ้นสุดการแก้ไข ---
                else:
                    st.error(message)
                    return
                # --- END: ส่วนที่แก้ไข ---
    export_dialog()

def render_test_data_tab():
    """Renders the UI for the Test Data tab with improved layout - FIXED VERSION."""
    st.markdown("#### 🗃️ Test Data Management", unsafe_allow_html=True)
    ws_state = st.session_state.studio_workspace

    # ✅ Auto-load datasources.resource เมื่อเริ่มต้น
    if 'datasources_auto_loaded' not in st.session_state:
        st.session_state.datasources_auto_loaded = False
    
    if not st.session_state.datasources_auto_loaded and st.session_state.project_path:
        datasources_path = os.path.join(
            st.session_state.project_path, 
            'resources', 
            'datasources.resource'
        )
        
        if os.path.exists(datasources_path):
            try:
                with open(datasources_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                imported_sources = parse_data_sources(content)
                
                if imported_sources:
                    ws_state.setdefault('data_sources', [])
                    existing_names = {s['name'] for s in ws_state['data_sources']}
                    
                    new_sources_added = 0
                    for source in imported_sources:
                        if source['name'] not in existing_names:
                            ws_state['data_sources'].append(source)
                            new_sources_added += 1
                    
                    if new_sources_added > 0:
                        st.success(f"✅ Auto-loaded {new_sources_added} data source links from `datasources.resource`")
                
                st.session_state.datasources_auto_loaded = True
                
            except Exception as e:
                st.warning(f"⚠️ Could not auto-load datasources.resource: {e}")
                st.session_state.datasources_auto_loaded = True
        else:
            st.info(f"ℹ️ No `datasources.resource` found. You can import it manually below.")
            st.session_state.datasources_auto_loaded = True

    # ✅ CSS สำหรับปรับขนาดปุ่ม toggle
    st.markdown("""
    <style>
    button[key="toggle_csv_datasources"],
    button[key="toggle_api_services"] {
        padding: 2px 8px !important;
        min-height: 28px !important;
        height: 28px !important;
        font-size: 0.85rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- CSV Data Sources Section ---
    # ✅ เช็ค state สำหรับ toggle
    if 'show_csv_datasources' not in st.session_state:
        st.session_state.show_csv_datasources = True
    
    with st.container(border=True):
        col1, col2 = st.columns([20, 1])
        
        with col1:
            st.markdown(f"""
            <div style='display: flex; align-items: center; gap: 10px;'>
                <span style='font-size: 1.05rem; font-weight: 600; color: #cbd5e1;'>
                    📊 CSV Data Sources
                </span>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            toggle_icon = "▼" if st.session_state.show_csv_datasources else "▶"
            if st.button(
                toggle_icon, 
                key="toggle_csv_datasources",
                help="Show/Hide",
                use_container_width=True
            ):
                st.session_state.show_csv_datasources = not st.session_state.show_csv_datasources
                st.rerun()
        
        if st.session_state.show_csv_datasources:    
            # --- Small create button at the top ---
            if st.button("➕ Create New CSV File", width='content', type="secondary"):
                ws_state['show_csv_creator'] = True
                st.rerun()
            
            
            # --- Two-column layout for main content ---
            left_panel, right_panel = st.columns([1, 2], gap="large")
            
            # --- LEFT PANEL: Import from datasources.resource ---
            with left_panel:
                st.markdown("##### 📥 Import Data Sources")
                
                uploaded_ds_file = st.file_uploader(
                    "Import from datasources.resource",
                    type=['resource'],
                    key="ds_resource_uploader",
                    help="Upload your datasources.resource file to auto-populate links.",
                    label_visibility="collapsed"
                )

                # --- Import Logic ---
                if uploaded_ds_file:
                    if uploaded_ds_file.file_id != st.session_state.get('last_uploaded_ds_id'):
                        st.session_state['last_uploaded_ds_id'] = uploaded_ds_file.file_id
                        with st.spinner(f"Parsing {uploaded_ds_file.name}..."):
                            try:
                                content = uploaded_ds_file.getvalue().decode("utf-8")
                                imported_sources = parse_data_sources(content)

                                if not imported_sources:
                                    st.warning("No valid 'Import DataSource' keywords found.")
                                else:
                                    ws_state.setdefault('data_sources', [])
                                    existing_names = {s['name'] for s in ws_state['data_sources']}
                                    new_sources_added = 0
                                    for source in imported_sources:
                                        if source['name'] not in existing_names:
                                            ws_state['data_sources'].append(source)
                                            new_sources_added += 1
                                    if new_sources_added > 0:
                                        st.success(f"Successfully imported {new_sources_added} new data source links!")
                                        st.rerun()
                                    else:
                                        st.info("All data sources already exist.")
                            except Exception as e:
                                st.error(f"Failed to parse file: {e}")
            
            # --- RIGHT PANEL: Data Source Links ---
            with right_panel:
                st.markdown("##### 🔗 Data Source Links")
                
                # --- Get CSV files ---
                csv_files_options = []
                if st.session_state.project_structure.get('csv_files'):
                    csv_files_in_datatest = [
                        os.path.basename(f) for f in st.session_state.project_structure['csv_files']
                        if 'resources/datatest' in f.replace(os.sep, '/')
                    ]
                    csv_files_options = sorted(list(set(csv_files_in_datatest)))

                data_sources = ws_state.get('data_sources', [])

                if not data_sources:
                    st.info("No data source links defined. Add one manually or import a file.")
                else:
                    # Header - rendered ONCE
                    st.markdown("""
                        <div class="ds-table-wrapper">
                            <div class="ds-table-header">
                                <div class="ds-header-item">
                                    <i class="fa-solid fa-database"></i>
                                    <span>Data Source Name</span>
                                </div>
                                <div class="ds-header-item">
                                    <i class="fa-solid fa-file-csv"></i>
                                    <span>CSV File</span>
                                </div>
                                <div class="ds-header-item">
                                    <i class="fa-solid fa-table-columns"></i>
                                    <span>Column Variable</span>
                                </div>
                                <div class="ds-header-item">
                                    <i class="fa-solid fa-gears"></i>
                                    <span>Actions</span>
                                </div>
                                <div class="ds-header-item">
                                    <i class="fa-solid fa-trash"></i>
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                    # Data Rows
                    for i, source in enumerate(data_sources):
                        is_imported = source.get('is_imported', False)
                        
                        st.markdown('<div class="ds-row-wrapper">', unsafe_allow_html=True)
                        
                        row_cols = st.columns([2.5, 2.5, 2, 1.5, 0.6])

                        # Column 1: Data Source Name
                        with row_cols[0]:
                            if is_imported:
                                st.markdown(f'<div class="imported-data-box">{source.get("name", "")}</div>', unsafe_allow_html=True)
                            else:
                                name_value = source.get('name', '')
                                source['name'] = st.text_input(
                                    f"DS Name {i}", 
                                    value=name_value, 
                                    key=f"ds_name_{i}",
                                    label_visibility="collapsed", 
                                    placeholder="e.g., DS_USERS",
                                    help="Enter the data source variable name (uppercase recommended)"
                                )
                                if not name_value.strip():
                                    st.markdown(
                                        '<div style="color: #d29922; font-size: 0.75rem; margin-top: 0.25rem;">⚠️ Required</div>',
                                        unsafe_allow_html=True
                                    )

                        # Column 2: CSV File
                        with row_cols[1]:
                            if is_imported:
                                st.markdown(f'<div class="imported-data-box">{source.get("file_name", "")}</div>', unsafe_allow_html=True)
                            else:
                                selected_index = 0
                                current_file = source.get('file_name', '')
                                options_with_empty = [''] + csv_files_options
                                
                                if current_file in options_with_empty:
                                    try: 
                                        selected_index = options_with_empty.index(current_file)
                                    except ValueError: 
                                        selected_index = 0
                                
                                source['file_name'] = st.selectbox(
                                    f"CSV {i}", 
                                    options=options_with_empty, 
                                    index=selected_index, 
                                    key=f"ds_file_{i}", 
                                    label_visibility="collapsed",
                                    format_func=lambda x: x if x else "📂 Select CSV file...",
                                    help="Choose a CSV file from your datatest folder"
                                )
                                if not current_file:
                                    st.markdown(
                                        '<div style="color: #d29922; font-size: 0.75rem; margin-top: 0.25rem;">⚠️ Required</div>',
                                        unsafe_allow_html=True
                                    )

                        # Column 3: Column Variable
                        with row_cols[2]:
                            if is_imported:
                                st.markdown(f'<div class="imported-data-box">{source.get("col_name", "")}</div>', unsafe_allow_html=True)
                            else:
                                col_value = source.get('col_name', '')
                                source['col_name'] = st.text_input(
                                    f"Col {i}", 
                                    value=col_value, 
                                    key=f"ds_col_{i}",
                                    label_visibility="collapsed", 
                                    placeholder="e.g., username",
                                    help="Enter the column variable name (lowercase recommended)"
                                )
                                if not col_value.strip():
                                    st.markdown(
                                        '<div style="color: #d29922; font-size: 0.75rem; margin-top: 0.25rem;">⚠️ Required</div>',
                                        unsafe_allow_html=True
                                    )

                        # Column 4: Actions
                        with row_cols[3]:
                            if is_imported:
                                st.markdown('<div class="imported-status-box">📋 Imported</div>', unsafe_allow_html=True)
                            else:
                                is_complete = (
                                    source.get('name', '').strip() and 
                                    source.get('file_name', '').strip() and 
                                    source.get('col_name', '').strip()
                                )
                                
                                if is_complete:
                                    if st.button("💾 Export", key=f"export_{i}", width='stretch'):
                                        data_source_export_dialog(source, i)
                                else:
                                    st.markdown(
                                        '''<div style="
                                            background: rgba(139, 148, 158, 0.1);
                                            border: 1.5px solid rgba(139, 148, 158, 0.3);
                                            border-radius: 8px;
                                            padding: 0.6rem 1.3rem;
                                            text-align: center;
                                            color: rgba(139, 148, 158, 0.6);
                                            font-weight: 600;
                                            font-size: 0.85rem;
                                            text-transform: uppercase;
                                            cursor: not-allowed;
                                        ">
                                            🔒 Complete Form
                                        </div>''',
                                        unsafe_allow_html=True
                                    )

                        # Column 5: Delete
                        with row_cols[4]:
                            if st.button("🗑️", key=f"del_{i}", help="Delete this data source link", width='stretch', type="secondary"):
                                ws_state['data_sources'].pop(i)
                                st.rerun()
                        
                        st.markdown('</div>', unsafe_allow_html=True)

                st.markdown("---")
                if st.button("🔗 Add Data Source Link (Manual)", width='stretch', type="secondary"):
                    ws_state.setdefault('data_sources', []).append({
                        'name': '', 'file_name': '', 'col_name': '', 'is_imported': False
                    })
                    st.rerun()

    # --- API Services Section ---
    if 'show_api_services' not in st.session_state:
        st.session_state.show_api_services = False
    
    with st.container(border=True):
        col1, col2 = st.columns([20, 1])
        
        with col1:
            st.markdown(f"""
            <div style='display: flex; align-items: center; gap: 10px;'>
                <span style='font-size: 1.05rem; font-weight: 600; color: #cbd5e1;'>
                    🌐 API Services
                </span>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            toggle_icon = "▼" if st.session_state.show_api_services else "▶"
            if st.button(
                toggle_icon, 
                key="toggle_api_services",
                help="Show/Hide",
                use_container_width=True
            ):
                st.session_state.show_api_services = not st.session_state.show_api_services
                st.rerun()
        
        if st.session_state.show_api_services:
            st.markdown("---")
            render_api_generator_tab()

def render_api_generator_tab():
    """Renders the UI for the Intelligent API Keyword Generator."""
    st.markdown("<h4 style='font-size: 1.4rem; margin-bottom: 0.5rem;'> 📡 Intelligent API Keyword Generator</h4>", unsafe_allow_html=True)
    st.caption("Generate robust Robot Framework API keywords from sample request/response data.")

    """Renders the UI for the Intelligent API Keyword Generator."""
    # <<< เพิ่มบรรทัดนี้เข้ามา >>>
    ws_state = st.session_state.studio_workspace
    if 'editing_api_service_id' not in ws_state:
        ws_state['editing_api_service_id'] = None

    # --- Top Action Bar ---
    action_cols = st.columns([3, 1])
    with action_cols[0]:
        if st.button("➕ Create New API Service", width='content', type="primary"):
            new_service = {
                'id': str(uuid.uuid4()),
                'service_name': 'service_newapi',
                'path_var_name': 'VAR_PATH_NEWAPI',
                'endpoint_path': 'api/endpoint/path',
                'http_method': 'POST',
                'req_body_sample': '{\n  "key": "value"\n}',
                'analyzed_fields': {},
                'resp_body_sample': '{\n  "status": "success",\n  "data": {},\n  "message": "Error message"\n}',
                'response_extractions': [],
                
                # --- START: เพิ่ม/แก้ไขค่าเริ่มต้นใหม่ ---
                'headers_type': 'custom', # เปลี่ยนค่าเริ่มต้นเป็น custom
                'bearer_token_var': '${GLOBAL_ACCESS_TOKEN}',
                'custom_header_use_uid_ucode': True, # เปิดใช้ uid/ucode เป็นค่าเริ่มต้น
                'custom_header_manual_pairs': 'Content-Type: application/json', # เพิ่มค่าเริ่มต้น
                # --- END: เพิ่ม/แก้ไขค่าเริ่มต้นใหม่ ---

                'add_status_validation': True,
                'status_field_path': 'status',
                'status_success_value': 'success',
                'error_message_path': 'message'
            }
            ws_state.setdefault('api_services', []).append(new_service)
            st.rerun()
    
    with action_cols[1]:
        if ws_state.get('api_services'):
            if st.button("🗑️ Clear All", width='stretch'):
                ws_state['api_services'] = []
                st.rerun()

    st.markdown("---")

    if ws_state['editing_api_service_id'] is None:
        # ถ้าไม่ใช่ ให้แสดงหน้ารายการ
        render_api_list_view()
    else:
        # ถ้าใช่ ให้แสดงหน้า Editor
        render_api_editor_view()

def render_api_list_view():
    """Displays the list of all created API services."""
    ws_state = st.session_state.studio_workspace
    st.markdown("<h4 style='font-size: 1.3rem; margin-bottom: 0.5rem;'><i class='fa-solid fa-link'></i> Your API Services</h4>", unsafe_allow_html=True)
    if not ws_state.get('api_services'):
        st.info("No API services defined yet. Click 'Create New API Service' to start.")
        return

    for i, service in enumerate(ws_state.get('api_services', [])):
        with st.container(border=True):
            cols = st.columns([4, 1, 1])
            with cols[0]:
                st.markdown(f"<div style='font-size: 1.2rem; font-weight: 600;'>{service.get('service_name', 'service_untitled')}</div><br>", unsafe_allow_html=True)
                st.markdown(f"<p style='font-size: 0.85rem; color: #a3a3a3; margin-top: -8px;'>PATH: <code style='font-size: inherit; padding: 0.2em 0.4em; position: relative; top: -1px;'>{service.get('endpoint_path', '/')}</code></p>", unsafe_allow_html=True)
            with cols[1]:
                if st.button("✏️ Edit", key=f"edit_api_{service['id']}", width='stretch'):
                    ws_state['editing_api_service_id'] = service['id']
                    st.rerun()
            with cols[2]:
                if st.button("🗑️ Delete", key=f"delete_api_{service['id']}", width='stretch'):
                    ws_state['api_services'].pop(i)
                    st.rerun()

def render_api_editor_view():
    """Renders the Two-Panel Editor for a single API service."""
    ws_state = st.session_state.studio_workspace
    service_id = ws_state['editing_api_service_id']

    # ค้นหา service data จาก id
    service_data = next((s for s in ws_state['api_services'] if s['id'] == service_id), None)

    if service_data is None:
        st.error("Service not found. Returning to list.")
        ws_state['editing_api_service_id'] = None
        st.rerun()
        return

    # ปุ่มกลับไปหน้า List
    if st.button("← Back to Service List"):
        ws_state['editing_api_service_id'] = None
        st.rerun()

    st.markdown(f"""
    <br><br><div style='
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 20px;
    '>
        <span style='
            background: rgba(88, 166, 255, 0.15);
            border: 1px solid rgba(88, 166, 255, 0.3);
            color: var(--primary-hover);
            padding: 6px 12px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        '>✏️ Editing</span>
        <span style='
            color: var(--text-primary);
            font-size: 20px;
            font-weight: 700;
        '>{service_data.get('service_name', 'service_untitled')}</span>
    </div>
    """, unsafe_allow_html=True)

    # --- สร้าง Layout 2 Panel หลัก ---
    left_panel, right_panel = st.columns([6, 5], gap="large")

    # --- Panel ซ้าย: Input & Configuration ---
    with left_panel:
        
        st.markdown(f"<h2 style='font-size: 1.2rem;'>Configuration</h2>", unsafe_allow_html=True)
        render_editor_form(service_data)

    # --- Panel ขวา: Live Code Preview ---
    with right_panel:
        st.markdown(f"<h2 style='font-size: 1.2rem;'>Live Code Preview</h2>", unsafe_allow_html=True)
        render_live_code_preview(service_data)

def render_editor_form(service_data):
    """Renders the entire input form for the API service editor."""
    service_id = service_data['id']

    # --- Expander 1: Endpoint & Configuration ---
    with st.expander("📂 Endpoint & Configuration", expanded=True):
        st.text_input(
            "Service Name",
            key=f"editor_service_name_{service_id}",
            value=service_data['service_name'],
            on_change=lambda: service_data.update({'service_name': st.session_state[f"editor_service_name_{service_id}"]})
        )
        cols = st.columns(2)
        with cols[0]:
            st.selectbox(
                "HTTP Method",
                ["POST", "GET", "PUT", "DELETE", "PATCH"],
                key=f"editor_http_method_{service_id}",
                index=["POST", "GET", "PUT", "DELETE", "PATCH"].index(service_data['http_method']),
                on_change=lambda: service_data.update({'http_method': st.session_state[f"editor_http_method_{service_id}"]})
            )
        with cols[1]:
            st.text_input(
                "Endpoint Path (e.g., users/getlist)",
                key=f"editor_endpoint_path_{service_id}",
                value=service_data['endpoint_path'],
                on_change=lambda: service_data.update({'endpoint_path': st.session_state[f"editor_endpoint_path_{service_id}"]})
            )

    # --- Expander 2: Request Options ---
    with st.expander("⚙️ Request Options", expanded=True):
        st.markdown("**Header / Authentication**")
        
        header_options = ['simple', 'bearer', 'custom']
        service_data['headers_type'] = st.selectbox(
            "Header Type",
            options=header_options,
            index=header_options.index(service_data.get('headers_type', 'simple')),
            key=f"editor_header_type_{service_id}"
        )

        if service_data['headers_type'] == 'bearer':
            service_data['bearer_token_var'] = st.text_input(
                "Bearer Token Variable",
                value=service_data.get('bearer_token_var', '${GLOBAL_ACCESS_TOKEN}'),
                key=f"editor_bearer_token_{service_id}"
            )
        elif service_data['headers_type'] == 'custom':
            service_data['custom_header_use_uid_ucode'] = st.checkbox(
                "Use uid/ucode authentication",
                value=service_data.get('custom_header_use_uid_ucode', True),
                key=f"editor_use_uid_ucode_{service_id}",
                help="ถ้าเลือก จะมีการเรียก Login เพื่อเอา uid/ucode มาใส่ใน Header ให้อัตโนมัติ"
            )
        
        service_data['custom_header_manual_pairs'] = st.text_area(
            "Additional Headers (key: value)",
            value=service_data.get('custom_header_manual_pairs', 'Content-Type: application/json'),
            key=f"editor_manual_headers_{service_id}",
            help="ใส่ Header เพิ่มเติม บรรทัดละ 1 คู่, คั่นด้วยเครื่องหมาย colon (:)"
        )

    # --- Expander 3: Request Body & Arguments (ส่วนที่แก้ไขใหม่) ---
    with st.expander("📝 Request Body & Arguments", expanded=True):
        st.text_area(
            "Paste JSON Body Sample",
            key=f"editor_req_body_{service_id}",
            value=service_data['req_body_sample'],
            height=200,
            on_change=lambda: service_data.update({'req_body_sample': st.session_state[f"editor_req_body_{service_id}"]})
        )

        if st.button("✨ Analyze Request & Generate Arguments", key=f"editor_analyze_{service_id}", width='stretch'):
            try:
                service_data['analyzed_fields'] = {}
                if service_data['req_body_sample'].strip():
                    body_json = json.loads(service_data['req_body_sample'])
                    
                    # ✅ ใช้ฟังก์ชันใหม่เพื่อ flatten JSON แบบ nested
                    flattened = flatten_json_for_args(body_json)
                    
                    for path, value in flattened.items():
                        # สร้าง argument name จาก path
                        # เช่น header.cpid -> header_cpid
                        arg_name = path.replace('.', '_').replace('[', '_').replace(']', '')
                        
                        service_data['analyzed_fields'][path] = {
                            "value": value,
                            "is_argument": False,
                            "arg_name": arg_name,
                            "json_path": path,  # เก็บ path ไว้
                            "default_value": ""  # ✅ เพิ่ม field สำหรับ default value
                        }
                    
                st.success(f"Analysis Complete! Found {len(service_data.get('analyzed_fields', {}))} fields.")
                st.rerun()
            except json.JSONDecodeError:
                st.error("Invalid JSON in Request Body.")
            except Exception as e:
                st.error(f"Analysis Error: {e}")

        # ✅ แสดงผลแบบ Tree Structure
        if service_data.get('analyzed_fields'):
            st.markdown("---")
            st.markdown("**Fields to make Arguments:**")
            st.caption("💡 Check fields you want to use as arguments, set custom names, and provide default values")
            
            # จัดกลุ่มตาม parent path
            grouped_fields = {}
            parent_order = []  # ✅ เก็บลำดับที่เจอ parent
            
            for path, field_data in service_data['analyzed_fields'].items():
                parts = path.split('.')
                parent = parts[0] if len(parts) > 1 else "Root"
                
                # ✅ เก็บลำดับที่เจอ parent ครั้งแรก
                if parent not in grouped_fields:
                    grouped_fields[parent] = []
                    parent_order.append(parent)
                
                grouped_fields[parent].append((path, field_data))
            
            # ✅ แสดงแต่ละกลุ่มตามลำดับที่เจอใน JSON
            for parent in parent_order:
                fields = grouped_fields[parent]
                
                with st.container(border=True):
                    st.markdown(f"**📦 {parent}**")
                    
                    # ✅ Header สำหรับตาราง (3 คอลัมน์)
                    st.markdown("""
                        <div style='display: grid; grid-template-columns: 0.5fr 2.5fr 2fr 2fr; 
                                    font-weight: 600; padding: 8px 4px; 
                                    background-color: rgba(128, 128, 128, 0.15); 
                                    border-radius: 4px; margin-bottom: 8px; font-size: 0.85rem;'>
                            <div style='text-align: center;'>Use</div>
                            <div>Field Path</div>
                            <div>Argument Name</div>
                            <div>Assign Value</div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    for path, field_data in sorted(fields, key=lambda x: x[0]):
                        # ✅ เปลี่ยนเป็น 4 คอลัมน์
                        cols = st.columns([0.5, 2.5, 2, 2])
                        
                        # Column 1: Checkbox (Use as Argument)
                        with cols[0]:
                            field_data['is_argument'] = st.checkbox(
                                " ", 
                                value=field_data.get('is_argument', False), 
                                key=f"editor_is_arg_{service_id}_{path}",
                                label_visibility="collapsed"
                            )
                        
                        # Column 2: Field Path
                        with cols[1]:
                            display_path = path.replace(f"{parent}.", "") if parent != "Root" else path
                            # แสดง sample value ข้างหลัง path
                            sample_val = str(field_data.get('value', ''))
                            if len(sample_val) > 30:
                                sample_val = sample_val[:30] + "..."
                            st.markdown(f"`{display_path}`")
                            st.caption(f"Sample: {sample_val}")
                        
                        # Column 3: Argument Name (ใช้ได้เฉพาะเมื่อ Use = True)
                        with cols[2]:
                            field_data['arg_name'] = st.text_input(
                                "Arg Name", 
                                value=field_data.get('arg_name', ''), 
                                key=f"editor_arg_name_{service_id}_{path}", 
                                label_visibility="collapsed",
                                disabled=not field_data['is_argument'],
                                placeholder="arg_name"
                            )
                        
                        # Column 4: Assign Value (✅ เปิดให้แก้ไขได้เสมอ)
                        with cols[3]:
                            # ✅ ถ้ายังไม่มี assigned_value ให้ใช้ค่า sample เดิม
                            if 'assigned_value' not in field_data:
                                field_data['assigned_value'] = str(field_data.get('value', ''))
                            
                            field_data['assigned_value'] = st.text_input(
                                "Assign Value", 
                                value=field_data.get('assigned_value', ''), 
                                key=f"editor_assign_val_{service_id}_{path}", 
                                label_visibility="collapsed",
                                placeholder="value to assign",
                                help="This value will be used in the generated JSON"
                            )
            
            # ปุ่มเพิ่มฟิลด์ใหม่
            st.markdown("---")
            if st.button("➕ Add Custom Field", key=f"add_field_{service_id}", type="secondary"):
                new_path = f"custom_field_{len(service_data['analyzed_fields'])}"
                service_data['analyzed_fields'][new_path] = {
                    "value": "",
                    "is_argument": True,
                    "arg_name": new_path,
                    "json_path": new_path,
                    "default_value": ""
                }
                st.rerun()

    # --- Expander 4: Response Handling ---
    with st.expander("📥 Response Handling & Variable Extraction", expanded=True):
        st.markdown("**Response Validation**")
        service_data['add_status_validation'] = st.checkbox(
            "Enable Response Status Validation",
            value=service_data.get('add_status_validation', True),
            key=f"editor_add_validation_{service_id}",
            help="สร้างโค้ด IF/ELSE เพื่อตรวจสอบว่า API สำเร็จหรือไม่"
        )

        if service_data['add_status_validation']:
            val_cols = st.columns(3)
            with val_cols[0]:
                st.caption("JSON Path to Status")
                service_data['status_field_path'] = st.text_input(
                    "JSON Path to Status",
                    value=service_data.get('status_field_path', 'status'),
                    key=f"editor_status_path_{service_id}",
                    label_visibility="collapsed",
                    placeholder="e.g., status"
                )
            with val_cols[1]:
                st.caption("Expected Success Value")
                service_data['status_success_value'] = st.text_input(
                    "Expected Success Value",
                    value=service_data.get('status_success_value', 'success'),
                    key=f"editor_success_value_{service_id}",
                    label_visibility="collapsed",
                    placeholder="e.g., success"
                )
            with val_cols[2]:
                st.caption("JSON Path to Error Msg")
                service_data['error_message_path'] = st.text_input(
                    "JSON Path to Error Msg",
                    value=service_data.get('error_message_path', 'message'),
                    key=f"editor_error_path_{service_id}",
                    label_visibility="collapsed",
                    placeholder="e.g., message"
                )

        st.markdown("---")
        st.markdown("**Response Body Sample & Variable Extraction**")
        
        st.text_area(
            "Paste JSON Response Sample",
            key=f"editor_resp_body_{service_id}",
            value=service_data['resp_body_sample'],
            height=200,
            on_change=lambda: service_data.update({'resp_body_sample': st.session_state[f"editor_resp_body_{service_id}"]})
        )

        if st.button("🔍 Analyze Response & Find Variables", key=f"editor_analyze_resp_{service_id}", width='stretch'):
            try:
                resp_json = json.loads(service_data['resp_body_sample'])
                found_paths = flatten_json_with_paths(resp_json)
                
                service_data.setdefault('response_extractions', [])
                existing_paths = {item['json_path'] for item in service_data['response_extractions']}
                
                new_items_added = 0
                for path, sample_value in found_paths.items():
                    if path not in existing_paths:
                        service_data['response_extractions'].append({
                            "id": str(uuid.uuid4()),
                            "json_path": path,
                            "sample_value": str(sample_value)[:100],
                            "is_enabled": False,
                            "var_name": generate_variable_name_from_path(path)
                        })
                        new_items_added += 1
                st.success(f"Analysis complete! Found {len(found_paths)} data paths. Added {new_items_added} new potential variables.")
            except json.JSONDecodeError:
                st.error("Invalid JSON in Response Body.")
            except Exception as e:
                st.error(f"Analysis Error: {e}")

        if service_data.get('response_extractions'):
            st.markdown("**Variables to Extract:** (Check to enable)")
            
            with st.container(border=True):
                st.markdown("""<div style='display: grid; grid-template-columns: 1fr 4fr 4fr; font-weight: bold;'>
                            <div>Use</div>
                            <div>Response Data Path</div>
                            <div>Robot Variable Name</div>
                            </div>""", unsafe_allow_html=True)
                
                for item in service_data['response_extractions']:
                    cols = st.columns([1, 4, 4])
                    with cols[0]:
                        item['is_enabled'] = st.checkbox(" ", value=item.get('is_enabled', False), key=f"editor_resp_isenabled_{item['id']}")
                    with cols[1]:
                        st.markdown(f"`{item['json_path']}`")
                        st.caption(f"Sample: {item['sample_value']}")
                    with cols[2]:
                        item['var_name'] = st.text_input("Var Name", value=item['var_name'], key=f"editor_resp_varname_{item['id']}", label_visibility="collapsed", disabled=not item['is_enabled'])
                
                if st.button("Clear unused variables", key=f"editor_clear_unused_{service_id}", help="Remove all variables that are not checked"):
                    service_data['response_extractions'] = [item for item in service_data['response_extractions'] if item.get('is_enabled')]
                    st.rerun()


def flatten_json_for_args(obj, parent_key='', sep='.'):
    """
    Flatten nested JSON สำหรับแสดงเป็น Arguments
    
    ตัวอย่าง:
    {"header": {"cpid": null, "name": "test"}, "detail": {"id": 1}}
    
    จะกลายเป็น:
    {
        "header.cpid": null,
        "header.name": "test",
        "detail.id": 1
    }
    """
    items = {}
    
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            
            if isinstance(v, dict):
                # ถ้าเป็น dict ให้ flatten ต่อ
                items.update(flatten_json_for_args(v, new_key, sep=sep))
            elif isinstance(v, list) and v and isinstance(v[0], dict):
                # ถ้าเป็น array of objects ให้เอาตัวแรก
                items.update(flatten_json_for_args(v[0], f"{new_key}[0]", sep=sep))
            else:
                # ถ้าเป็น primitive value (string, number, boolean, null)
                items[new_key] = v
    elif isinstance(obj, list) and obj:
        # ถ้าเป็น array ให้เอาตัวแรก
        if isinstance(obj[0], dict):
            items.update(flatten_json_for_args(obj[0], f"{parent_key}[0]", sep=sep))
        else:
            items[f"{parent_key}[0]"] = obj[0]
    else:
        items[parent_key] = obj
    
    return items

def generate_set_path_keyword_line(service_data):
    """Generates the single 'Set Global Variable' line for the Set Path Request URL keyword."""
    service_name = service_data.get('service_name', 'untitled')
    path_var_name = service_data.get('path_var_name', 'VAR_PATH_UNKNOWN')
    
    # สร้างชื่อตัวแปรจาก Service Name e.g., service_new_api -> SERVICE_NEW_API_PATH
    service_path_var_name = f"SERVICE_{service_name.replace('service_', '').upper()}_PATH"
    
    # สร้างโค้ดแค่บรรทัดเดียว
    line = f"    Set Global Variable         ${{{service_path_var_name}}}           ${{URLTEST}}/${{API_URLPATH_TEST}}/${{{path_var_name}}}"
    return line



def generate_path_variable_code(service_data):
    """Generates the Robot Framework code for the path variable."""
    service_name = service_data.get('service_name', 'untitled')
    endpoint_path = service_data.get('endpoint_path', '')
    
    # สร้างชื่อตัวแปรจาก Service Name e.g., service_get_company -> VAR_PATH_GETCOMPANY
    path_var_name = f"VAR_PATH_{service_name.replace('service_', '').upper()}"
    service_data['path_var_name'] = path_var_name # เก็บไว้ใช้ภายหลัง
    
    return f"${{{path_var_name}}}    {endpoint_path}"


    # --- 3. Build Preparation & Header Logic (ส่วนที่แก้ไขใหม่) ---
    prep_lines = []
    execute_api_args = [
        f"    ...    servicename={service_data.get('service_name', 'untitled')}",
        f"    ...    method={service_data.get('http_method', 'POST')}",
        f"    ...    urlpath=${{{service_data.get('path_var_name', 'VAR_PATH_UNKNOWN')}}}",
        "    ...    requestbody=${bodydata}",
        "    ...    expectedstatus=200",
    ]
    
    header_type = service_data.get('headers_type', 'simple')
    custom_dict_items = []

    # Step 3.1: Conditional Login for uid/ucode
    if header_type == 'custom' and service_data.get('custom_header_use_uid_ucode'):
        prep_lines.append("\n    api_base.Request Service for get session data    ${headeruser}    ${headerpassword}")
        custom_dict_items.extend(["uid=${GLOBAL_API_UID}", "ucode=${GLOBAL_API_UCODE}"])

    # Step 3.2: Build Header Dictionary from bearer token or manual entries
    if header_type == 'bearer':
        token_var = service_data.get('bearer_token_var', '${GLOBAL_ACCESS_TOKEN}')
        custom_dict_items.append(f"Authorization=Bearer {token_var}")
        
    manual_headers = service_data.get('custom_header_manual_pairs', '')
    if manual_headers.strip():
        for line in manual_headers.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                custom_dict_items.append(f"{key.strip()}={value.strip()}")

    # Step 3.3: Determine Execute API arguments based on what we've built
    if not custom_dict_items:
        # If after everything, there are no custom headers, use 'simple'
        execute_api_args.append("    ...    headers_type=simple")
    else:
        # If there are any custom headers, create the dictionary and use 'custom_headers' type
        execute_api_args.append("    ...    headers_type=custom_headers")
        prep_lines.append(f"    &{{custom_headers_dict}}=    Create Dictionary    {'    '.join(custom_dict_items)}")
        execute_api_args.append("    ...    &{custom_headers}=${custom_headers_dict}")

    # --- 5. Build Response Validation & Variable Extraction ---
    validation_code = []
    if service_data.get('add_status_validation'):
        status_path = service_data.get('status_field_path', 'status')
        success_value = service_data.get('status_success_value', 'success')
        error_path = service_data.get('error_message_path', 'message')
        
        validation_code.extend([
            f"    ${{status_val}}=    Set Variable    ${{GLOBAL_RESPONSE_JSON}}[{status_path}]",
            f"    IF    '${{status_val}}' == '{success_value}'"
        ])
        
        # Add variable extractions inside the IF block
        for mapping in service_data.get('response_extractions', []):
            if mapping.get('is_enabled') and mapping.get('var_name'):
                robot_path = ''.join([f"[{part}]" for part in mapping['json_path'].replace(']', '').replace('[', '.').split('.')])
                validation_code.append(f"        Set Global Variable    ${{{mapping['var_name']}}}    ${{GLOBAL_RESPONSE_JSON}}{robot_path}")
        
        validation_code.extend([
            "    ELSE",
            f"        Fail    API call failed. Status: ${{status_val}}, Message: ${{GLOBAL_RESPONSE_JSON}}[{error_path}]",
            "    END"
        ])
    else: # If no validation, just extract variables
        for mapping in service_data.get('response_extractions', []):
            if mapping.get('is_enabled') and mapping.get('var_name'):
                robot_path = ''.join([f"[{part}]" for part in mapping['json_path'].replace(']', '').replace('[', '.').split('.')])
                validation_code.append(f"    Set Global Variable    ${{{mapping['var_name']}}}    ${{GLOBAL_RESPONSE_JSON}}{robot_path}")

    # --- 6. Assemble the final keyword ---
    final_code = [
        f"{kw_name}",
        f"    [Arguments]    {args_str}",
        *prep_lines,
        body_code,
        "",
        "    utility-services.Execute API Request",
        *execute_api_args,
        "",
        *validation_code
    ]

    return "\n".join(final_code)

def flatten_json_with_paths(obj, parent_path=''):
    """
    Recursively flattens a nested JSON object into a dictionary of {path: value}.
    e.g., {'data': {'user': 'test'}} -> {'data.user': 'test'}
    e.g., {'items': [{'id': 1}]} -> {'items[0].id': 1}
    """
    paths = {}
    if isinstance(obj, dict):
        for key, value in obj.items():
            new_path = f"{parent_path}.{key}" if parent_path else key
            if isinstance(value, (dict, list)):
                paths.update(flatten_json_with_paths(value, new_path))
            else:
                paths[new_path] = value
    elif isinstance(obj, list) and obj: # Check if list is not empty
        for i, item in enumerate(obj):
            # For simplicity, we only parse the first item in an array
            if i == 0:
                new_path = f"{parent_path}[{i}]"
                if isinstance(item, (dict, list)):
                    paths.update(flatten_json_with_paths(item, new_path))
                else:
                    paths[new_path] = item
    return paths

def generate_variable_name_from_path(json_path):
    """Generates a suggested Robot Framework variable name from a JSON path."""
    # Clean up path: remove array indices and split by dots
    cleaned_path = json_path.replace('[0]', '').replace(']', '')
    parts = [p for p in cleaned_path.split('.') if p.lower() not in ['data', 'result']]
    if not parts:
        parts = cleaned_path.split('.')[-1:] # Fallback to the last part
    
    return f"GLOBAL_{'_'.join(parts).upper()}"

def rebuild_json_from_args(analyzed_fields, args_dict):
    """
    สร้าง JSON กลับจาก flat structure พร้อม default values
    
    Args:
        analyzed_fields: dict ที่มี path และ config
        args_dict: dict ของ argument values
    
    Returns:
        dict: JSON structure ที่สมบูรณ์
    """
    result = {}
    
    for path, field_data in analyzed_fields.items():
        if not field_data.get('is_argument'):
            continue
            
        # ดึงค่า
        arg_name = field_data['arg_name']
        default_val = field_data.get('default_value', '')
        
        # ใช้ default value ถ้ามี
        value_placeholder = f"${{{arg_name}}}" if not default_val else default_val
        
        # แยก path
        keys = path.replace('[0]', '').split('.')
        
        # สร้าง nested dict
        current = result
        for i, key in enumerate(keys[:-1]):
            if key not in current:
                current[key] = {}
            current = current[key]
        
        # ใส่ค่าสุดท้าย
        current[keys[-1]] = value_placeholder
    
    return result

def rebuild_json_from_analyzed_fields(analyzed_fields):
    """
    สร้าง JSON กลับจาก analyzed_fields โดยใช้ assigned_value หรือ placeholder
    
    Args:
        analyzed_fields: dict ที่มี path และ field_data
    
    Returns:
        dict: JSON structure ที่สมบูรณ์
    """
    result = {}
    
    for path, field_data in analyzed_fields.items():
        # แยก path
        keys = path.split('.')
        
        # สร้าง nested dict
        current = result
        for i, key in enumerate(keys[:-1]):
            clean_key = key.replace('[0]', '')
            if clean_key not in current:
                current[clean_key] = {}
            current = current[clean_key]
        
        # ใส่ค่าสุดท้าย
        last_key = keys[-1].replace('[0]', '')
        
        if field_data.get('is_argument'):
            # ✅ ถ้า Use = True → ใช้ argument placeholder
            arg_name = field_data['arg_name']
            current[last_key] = f"__PLACEHOLDER_{arg_name}__"
        else:
            # ✅ ถ้า Use = False → ใช้ assigned_value
            value = field_data.get('assigned_value', field_data.get('value', ''))
            
            # แปลงค่าให้ถูกต้องตามประเภท
            if value == 'null' or value == '' or value is None:
                current[last_key] = None
            elif value == 'true':
                current[last_key] = True
            elif value == 'false':
                current[last_key] = False
            elif isinstance(value, str) and value.lstrip('-').isdigit():
                current[last_key] = int(value)
            elif isinstance(value, str):
                try:
                    current[last_key] = float(value)
                except ValueError:
                    current[last_key] = value
            else:
                current[last_key] = value
    
    return result

def generate_main_keyword_code(service_data):
    """Generates the complete main keyword code for the specific service file."""
    kw_name = f"Request {service_data.get('service_name', 'Untitled').replace('_', ' ').title()}"
    
    # --- 1. Build Arguments (✅ ปรับให้ขึ้นบรรทัดใหม่เมื่อมากกว่า 8) ---
    args = ["${headeruser}", "${headerpassword}"]
    for path, field_data in service_data.get('analyzed_fields', {}).items():
        if field_data.get('is_argument'):
            args.append(f"${{{field_data['arg_name']}}}")
    
    # ✅ ถ้ามี arguments มากกว่า 8 ให้ขึ้นบรรทัดใหม่
    if len(args) <= 8:
        args_str = "    ".join(args)
        args_section = f"    [Arguments]    {args_str}"
    else:
        # บรรทัดแรก
        args_lines = ["    [Arguments]    " + "    ".join(args[:8])]
        # บรรทัดถัดไปใช้ ...
        remaining_args = args[8:]
        for i in range(0, len(remaining_args), 8):
            chunk = remaining_args[i:i+8]
            args_lines.append("    ...    " + "    ".join(chunk))
        args_section = "\n".join(args_lines)

    # --- 2. Build Multi-line Catenate for Body ---
    body_code = ""
    try:
        # ✅ สร้าง JSON จาก analyzed_fields (ใช้ assigned_value)
        body_dict = rebuild_json_from_analyzed_fields(service_data.get('analyzed_fields', {}))
        
        # แปลงเป็น JSON string แบบสวยงาม
        pretty_json = json.dumps(body_dict, indent=4, ensure_ascii=False)
        
        # ✅ แทนที่ placeholder ด้วย Robot Framework variables
        replacements = []
        for path, field_data in service_data.get('analyzed_fields', {}).items():
            if field_data.get('is_argument'):
                arg_name = field_data['arg_name']
                placeholder = f'"__PLACEHOLDER_{arg_name}__"'
                replacement = f'${{{arg_name}}}'
                replacements.append((placeholder, replacement))
        
        final_body_str = pretty_json
        for p_str, v_str in replacements:
            final_body_str = final_body_str.replace(p_str, v_str, 1)
        
        body_lines = final_body_str.split('\n')
        if len(body_lines) > 2:
            output_lines = ['    ${bodydata}=    Catenate    {']
            for line in body_lines[1:-1]:
                output_lines.append(f'    ...    {line}')
            output_lines.append('    ...    }')
            body_code = "\n".join(output_lines)
        else:
            body_code = f"    ${{bodydata}}=    Catenate    {final_body_str}"
    except (json.JSONDecodeError, TypeError) as e:
        body_code = f"    ${{bodydata}}=    Catenate    {service_data.get('req_body_sample', '{}')}"

    # --- 3. Build Preparation & Header Logic ---
    prep_lines = []
    execute_api_args = [
        f"    ...    servicename={service_data.get('service_name', 'untitled')}",
        f"    ...    method={service_data.get('http_method', 'POST')}",
        f"    ...    urlpath=${{{service_data.get('path_var_name', 'VAR_PATH_UNKNOWN')}}}",
        "    ...    requestbody=${bodydata}",
        "    ...    expectedstatus=200",
    ]
    
    header_type = service_data.get('headers_type', 'simple')
    custom_dict_items = []

    if header_type == 'custom' and service_data.get('custom_header_use_uid_ucode'):
        prep_lines.append("\n    api_base.Request Service for get session data    ${headeruser}    ${headerpassword}")
        custom_dict_items.extend(["uid=${GLOBAL_API_UID}", "ucode=${GLOBAL_API_UCODE}"])

    if header_type == 'bearer':
        token_var = service_data.get('bearer_token_var', '${GLOBAL_ACCESS_TOKEN}')
        custom_dict_items.append(f"Authorization=Bearer {token_var}")
        
    manual_headers = service_data.get('custom_header_manual_pairs', '')
    if manual_headers.strip():
        for line in manual_headers.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                custom_dict_items.append(f"{key.strip()}={value.strip()}")

    if not custom_dict_items:
        execute_api_args.append("    ...    headers_type=simple")
    else:
        execute_api_args.append("    ...    headers_type=custom_headers")
        prep_lines.append(f"    &{{custom_headers_dict}}=    Create Dictionary    {'    '.join(custom_dict_items)}")
        execute_api_args.append("    ...    &{custom_headers}=${custom_headers_dict}")

    # --- 4. Build Response Validation ---
    validation_code = []
    if service_data.get('add_status_validation'):
        status_path = service_data.get('status_field_path', 'status')
        success_value = service_data.get('status_success_value', 'success')
        error_path = service_data.get('error_message_path', 'message')
        validation_code.extend([
            f"    ${{status_val}}=    Set Variable    ${{GLOBAL_RESPONSE_JSON}}[{status_path}]",
            f"    IF    '${{status_val}}' == '{success_value}'"
        ])
        for mapping in service_data.get('response_extractions', []):
            if mapping.get('is_enabled') and mapping.get('var_name'):
                robot_path = ''.join([f"[{p}]" for p in mapping['json_path'].replace(']', '').replace('[', '.').split('.')])
                validation_code.append(f"        Set Global Variable    ${{{mapping['var_name']}}}    ${{GLOBAL_RESPONSE_JSON}}{robot_path}")
        validation_code.extend([
            "    ELSE",
            f"        Fail    API call failed. Status: ${{status_val}}, Message: ${{GLOBAL_RESPONSE_JSON}}[{error_path}]",
            "    END"
        ])
    else:
        for mapping in service_data.get('response_extractions', []):
            if mapping.get('is_enabled') and mapping.get('var_name'):
                robot_path = ''.join([f"[{p}]" for p in mapping['json_path'].replace(']', '').replace('[', '.').split('.')])
                validation_code.append(f"    Set Global Variable    ${{{mapping['var_name']}}}    ${{GLOBAL_RESPONSE_JSON}}{robot_path}")

    # --- 5. Assemble the final keyword (✅ ใช้ args_section แทน) ---
    final_code = [
        f"{kw_name}",
        args_section,  # ✅ ใช้ตัวแปรที่สร้างไว้
        *prep_lines,
        body_code,
        "",
        "    utility-services.Execute API Request",
        *execute_api_args,
        "",
        *validation_code
    ]

    return "\n".join(final_code)

def render_live_code_preview(service_data):
    """Renders the right panel with generated code and save-to-file functionality."""
    ws_state = st.session_state.studio_workspace
    project_path = st.session_state.project_path

    # --- Section 1: For api_base.resource ---
    with st.container(border=True):
        st.markdown("##### 📦 For `api_base.resource`")
        st.markdown("---")
        st.markdown("<p style='font-size: 1.1rem; color: var(--text-muted);'>1. <code>*** Variables ***</code> section:</p>", unsafe_allow_html=True)
        var_code = generate_path_variable_code(service_data)
        st.code(var_code, language='robotframework')

        st.markdown("<p style='font-size: 1.1rem; color: var(--text-muted);'>2. Inside <code>Set Path Request URL</code> keywords section:</p>", unsafe_allow_html=True)
        kw_line_code = generate_set_path_keyword_line(service_data)
        st.code(kw_line_code, language='robotframework')
        
        if st.button("💾 Append to `api_base.resource`", key=f"save_api_base_{service_data['id']}", type="primary"):
            if not project_path:
                st.error("Project path is not set in the sidebar.")
            else:
                target_path = os.path.join(project_path, "resources", "services", "api_base.resource")
                success, message = append_to_api_base(target_path, var_code, kw_line_code)
                if success:
                    st.success(message)
                    st.balloons()
                else:
                    st.error(message)

    # --- Section 2: For the Service File ---
    with st.container(border=True):
        service_file_name = f"{service_data.get('service_name', 'service_file')}.resource"
        st.markdown(f"##### 📄 For your service file (e.g., `{service_file_name}`)")
        st.markdown("---")
        
        kw_code = generate_main_keyword_code(service_data)
        st.code(kw_code, language='robotframework')

        st.markdown("---")
        st.subheader("Save Options")

        # Initialize session state for save options
        if f"save_option_{service_data['id']}" not in ws_state:
            ws_state[f"save_option_{service_data['id']}"] = "Append to Existing File"

        ws_state[f"save_option_{service_data['id']}"] = st.radio(
            "Mode",
            ["Append to Existing File", "Create New File"],
            key=f"radio_save_mode_{service_data['id']}",
            horizontal=True,
            label_visibility="collapsed"
        )
        
        save_option = ws_state[f"save_option_{service_data['id']}"]

        if save_option == "Append to Existing File":
             # --- START: ส่วนที่แก้ไข ---
            all_robot_files = st.session_state.project_structure.get('robot_files', [])
            
            # เปลี่ยนโฟลเดอร์เป้าหมายเป็น resources/services ตามที่คุณต้องการ
            target_folder_relative = "resources/services"
            
            # กรองไฟล์ให้เหลือเฉพาะในโฟลเดอร์เป้าหมาย
            service_files = [
                f for f in all_robot_files 
                if f.replace(os.sep, '/').startswith(target_folder_relative + '/')
            ]
            
            if not service_files:
                st.warning("No .robot or .resource files found under the `resources/services` folder.")
            else:
                file_options = [f.replace(os.sep, '/') for f in service_files]
                
                selected_file = st.selectbox(
                    "Select a file to append to:",
                    options=sorted(file_options),
                    key=f"select_append_file_{service_data['id']}"
                )
                
                if st.button("➕ Append Keyword", key=f"append_kw_button_{service_data['id']}"):
                    if not project_path:
                        st.error("Project path is not set.")
                    else:
                        full_path = os.path.join(project_path, selected_file)
                            
                        # --- START: ส่วนที่แก้ไข ---
                        # เปลี่ยนไปเรียกใช้ฟังก์ชันใหม่สำหรับจัดการ Block
                        success, message = append_robot_content_intelligently(full_path, keywords_code=kw_code)
                            
                        if success:
                            st.success(f"{message} in `{selected_file}`")
                        else:
                            st.error(f"Failed to append to `{selected_file}`: {message}")
                        # --- END: ส่วนที่แก้ไข ---
        
        elif save_option == "Create New File":
            # --- CREATE NEW UI ---
            st.caption("File will be saved in the `resources/services/` folder.")
            new_file_name = st.text_input(
                "New file name:",
                value=service_file_name,
                key=f"new_file_name_input_{service_data['id']}"
            )
            if st.button("📝 Create and Save File", key=f"create_kw_button_{service_data['id']}"):
                if not project_path:
                    st.error("Project path is not set.")
                elif not new_file_name.endswith(('.robot', '.resource')):
                    st.error("File name must end with .robot or .resource")
                else:
                    # --- START: โค้ดที่เพิ่มเข้ามาเพื่อแก้ไข Error ---
                    # ประกาศตัวแปรที่หายไปก่อนนำไปใช้งาน
                    start_marker = "# --- START: Generated by Robot Framework Code Generator ---"
                    end_marker = "# ---  END: Generated by Robot Framework Code Generator  ---"
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    # --- END: โค้ดที่เพิ่มเข้ามา ---
                                        
                    # Automatically create settings for a new resource file
                    full_content = f"*** Settings ***\nResource    ../../resources/resourcekeywords.resource\n\n*** Keywords ***\n{start_marker}\n# Created: {timestamp}\n\n{kw_code}\n\n{end_marker}"
                    # Save to a dedicated folder
                    save_dir = os.path.join(project_path, "resources", "services")
                    os.makedirs(save_dir, exist_ok=True)
                    full_path = os.path.join(save_dir, new_file_name)
                    
                    success = create_new_robot_file(full_path, full_content)
                    if success:
                        st.success(f"Successfully created file at `{os.path.relpath(full_path, project_path)}`")
                        # Optional: Rescan project to show the new file
                        st.session_state.project_structure = scan_robot_project(project_path)
                        st.rerun()
                    else:
                        st.error("Failed to create the file.")

def render_studio_tab():
    """ 
    Renders the "Studio Workspace"
    (FIXED V10: Added border to container for visibility)
    """

    # --- 1. กำหนด options และ icons ---
    
    tab_options_list = [
        "Assets", 
        "Test Data",
        "Keyword Factory", 
        # "Test Flow",
        "CRUD Generator"
    ]
    
    tab_icons = [
        "safe2-fill",
        "server",
        "gear-wide-connected",
        # "kanban",
        "rocket-takeoff"
    ]   

    if 'main_studio_tab_index' not in st.session_state:
        st.session_state.main_studio_tab_index = 0

    # --- 2. สร้าง Wrapper Div เพื่อบังคับชิดซ้าย (ยังคงจำเป็น) ---
    st.markdown("<div style='width: fit-content; max-width: 100%;'>", unsafe_allow_html=True)

    selected_tab_name = option_menu(
        menu_title=None,
        options=tab_options_list,
        icons=tab_icons,
        
        key="main_studio_tabs",
        orientation="horizontal",
        default_index=st.session_state.main_studio_tab_index,
        
        # --- 3. [ปรับ] CSS เพิ่มกรอบเส้นที่ Container ---
        styles={
            "container": {
                # [ปรับ] เพิ่มกรอบเส้นและ Padding
                "padding": "6px !important", 
                "background-color": "transparent", # พื้นหลังโปร่งใส
                "border": "1px solid #30363d",   # ⭐️ เพิ่มกรอบเส้นสีเทาเข้ม
                "border-radius": "12px",           # ⭐️ เพิ่มความมน
                "margin-bottom": "1rem",
            },
            "icon": {
                "font-size": "1rem", 
                "margin-right": "6px", 
            },
            "nav-link": {
                # สไตล์ของปุ่ม "ไม่ได้เลือก" (เหมือนเดิม)
                "font-size": "0.9rem",
                "font-weight": "600",
                "color": "#8b949e",
                "background-color": "transparent",
                "border-radius": "8px",
                "padding": "8px 14px",
                "transition": "all 0.3s ease",
                "margin": "0 4px",
            },
            "nav-link:hover": {
                "background-color": "rgba(48, 54, 61, 0.7)", 
                "color": "#c9d1d9"
            },
            "nav-link-selected": {
                # สไตล์ของปุ่ม "ถูกเลือก" (เหมือนเดิม)
                "background-color": "#f85149", 
                "color": "#ffffff",
                "border-radius": "8px",
            },
            "nav-link-selected:hover": {
                "background-color": "#6cb0ff", 
                "color": "#ffffff",
            }
        }
    )
    
    # --- 4. ปิด Wrapper Div ---
    st.markdown("</div>", unsafe_allow_html=True) 

    st.markdown(
        "## <br><i class='bi bi-robot'></i> Studio Workspace", 
        unsafe_allow_html=True
    )
    st.caption("A visual editor to build your complete Robot Framework test script.")
    st.markdown("---")
    
    # --- 5. อัปเดต State และแสดงเนื้อหา Tab ---
    st.session_state.main_studio_tab_index = tab_options_list.index(selected_tab_name)
    
    if selected_tab_name == "Assets":
        render_resources_view_new()

    elif selected_tab_name == "Test Data":
        render_test_data_tab()

    elif selected_tab_name == "Keyword Factory":
        render_keyword_factory_tab()

    # elif selected_tab_name == "Test Flow":
    #     render_test_flow_tab()

    elif selected_tab_name == "CRUD Generator":
        render_crud_generator_tab()

def html_editor_dialog():
    """Renders the dialog for editing HTML content."""
    ws_state = st.session_state.studio_workspace
    page_index = ws_state['editing_html_index']
    page_data = ws_state['html_pages'][page_index]

    # ใช้ @st.dialog ครอบฟังก์ชันที่สร้าง Pop-up
    @st.dialog(f"Editing HTML for: {page_data['name']}")
    def edit_html():
        st.markdown("Paste your HTML content below.")
        edited_html = st.text_area(
            "HTML Content", height=400,
            value=page_data['html'],
            key=f"dialog_html_content_{page_index}",
            label_visibility="collapsed"
        )
        if st.button("Save and Close", type="primary"):
            ws_state['html_pages'][page_index]['html'] = edited_html
            ws_state['editing_html_index'] = None
            st.rerun()

    # เรียกใช้ฟังก์ชัน dialog ที่เพิ่งสร้าง
    edit_html()

# ใน app.py

def render_resources_view_new():

    ws_state = st.session_state.studio_workspace
    
    if 'editing_html_index' not in ws_state:
        ws_state['editing_html_index'] = None

    # ✅ เพิ่ม: Auto-load locators จาก pageobjects folder
    if 'locators_auto_loaded' not in st.session_state:
        st.session_state.locators_auto_loaded = False
    
    if not st.session_state.locators_auto_loaded and st.session_state.project_path:
        pageobjects_folder = os.path.join(st.session_state.project_path, 'pageobjects')
        
        if os.path.exists(pageobjects_folder):
            try:
                # ดึงไฟล์ .robot และ .resource ทั้งหมดจากโฟลเดอร์ pageobjects
                locator_files = []
                for root, dirs, files in os.walk(pageobjects_folder):
                    for file in files:
                        if file.endswith(('.robot', '.resource')):
                            locator_files.append(os.path.join(root, file))
                
                if locator_files:
                    total_loaded = 0
                    files_loaded = 0
                    
                    for file_path in locator_files:
                        file_name = os.path.relpath(file_path, st.session_state.project_path)
                        
                        # เช็คว่าไฟล์นี้โหลดแล้วหรือยัง
                        if any(loc.get('page_name') == file_name for loc in ws_state.get('locators', [])):
                            continue
                        
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            locators = read_robot_variables_from_content(content)
                            
                            if locators:
                                for loc in locators:
                                    loc['page_name'] = file_name
                                    if 'id' not in loc or not loc['id']:
                                        loc['id'] = str(uuid.uuid4())
                                
                                ws_state.setdefault('locators', []).extend(locators)
                                total_loaded += len(locators)
                                files_loaded += 1
                        
                        except Exception as e:
                            # ข้ามไฟล์ที่อ่านไม่ได้
                            continue
                    
                    if total_loaded > 0:
                        st.success(f"✅ Auto-loaded {total_loaded} locators from {files_loaded} files in `pageobjects` folder")
                
                st.session_state.locators_auto_loaded = True
                
            except Exception as e:
                st.warning(f"⚠️ Could not auto-load locators from pageobjects: {e}")
                st.session_state.locators_auto_loaded = True
        else:
            st.info(f"ℹ️ No `pageobjects` folder found.")
            st.session_state.locators_auto_loaded = True

    # --- Re-establish the two-column layout ---
    panel_grid = st.columns([1, 1], gap="large")

    # --- LEFT PANEL: COMMON KEYWORDS ---
    with panel_grid[0]:
        st.markdown("#### <i class='fa-solid fa-cubes'></i> Common Keywords", unsafe_allow_html=True)
        
        with st.container(border=True):
            current_kw_file = ws_state.get('common_keyword_path', 'N/A')
            st.caption(f"Loaded from: **{current_kw_file}**")

            uploaded_keyword_file = st.file_uploader(
                "Upload new keywords file to override", type=['robot', 'resource'], 
                key="studio_keyword_uploader_final", label_visibility="collapsed"
            )
            

            if uploaded_keyword_file:
                
                MENU_LOCATOR_NAMES = ['homemenu', 'mainmenu', 'submenu', 'menuname']

                if uploaded_keyword_file.name != ws_state.get('common_keyword_path'):
                    with st.spinner(f"Parsing {uploaded_keyword_file.name}..."):
                        try:
                            content = uploaded_keyword_file.getvalue().decode("utf-8")
                            
                            ws_state['keywords'] = parse_robot_keywords(content)
                            
                            all_variables = read_robot_variables_from_content(content)
                            
                            new_menu_locators = {}
                            new_common_vars = []
                            
                            for v in all_variables:
                                var_name = v.get('name')
                                if var_name in MENU_LOCATOR_NAMES:
                                    new_menu_locators[var_name] = v
                                else:
                                    new_common_vars.append(v)
                            
                            ws_state['common_variables'] = new_common_vars
                            ws_state['menu_locators'] = new_menu_locators 
                            
                            ws_state['common_keyword_path'] = uploaded_keyword_file.name                                
                            st.success(f"Successfully replaced keywords and variables with '{uploaded_keyword_file.name}'!")
                            st.rerun() 
                        except Exception as e:
                            st.error(f"Failed to parse file: {e}")

            # --- Common Variables Display ---
            if ws_state.get('common_variables'):
    
                valid_vars = [v for v in ws_state['common_variables'] if v.get('name')]
    
                if 'show_common_vars' not in st.session_state:
                    st.session_state.show_common_vars = False
                
                st.markdown("""
                <style>
                button[key="toggle_common_vars"] {
                    padding: 2px 8px !important;
                    min-height: 28px !important;
                    height: 28px !important;
                    font-size: 0.85rem !important;
                }
                </style>
                """, unsafe_allow_html=True)
                
                with st.container(border=True):
                    col1, col2 = st.columns([11, 1])
                    
                    with col1:
                        st.markdown(f"""
                        <div style='display: flex; align-items: center; gap: 10px;'>
                            <span style='font-size: 1.05rem; font-weight: 600; color: #28a745;'>
                                ✅ Common Variables
                            </span>
                            <span style='
                                background: rgba(40, 167, 69, 0.2);
                                border: 1px solid rgba(40, 167, 69, 0.4);
                                color: #28a745;
                                padding: 2px 8px;
                                border-radius: 12px;
                                font-size: 0.75rem;
                                font-weight: 600;
                            '>
                                {len(valid_vars)} items
                            </span>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        toggle_icon = "▼" if st.session_state.show_common_vars else "▶"
                        if st.button(
                            toggle_icon, 
                            key="toggle_common_vars",
                            help="Show/Hide",
                            use_container_width=True
                        ):
                            st.session_state.show_common_vars = not st.session_state.show_common_vars
                            st.rerun()
                    
                    if st.session_state.show_common_vars:
                        st.markdown("---")
                        
                        st.markdown("""<style>
                        .common-var-code {
                            background-color: rgba(40, 167, 69, 0.1);
                            border: 1px solid rgba(40, 167, 69, 0.3);
                            color: #28a745;
                            padding: 6px 10px;
                            border-radius: 8px;
                            font-family: monospace;
                            font-size: 0.85rem;
                            display: block;
                            margin-bottom: 6px;
                            white-space: nowrap;
                            overflow: hidden;
                            text-overflow: ellipsis;
                            cursor: pointer;
                            transition: all 0.2s ease;
                        }
                        .common-var-code:hover { 
                            background-color: rgba(40, 167, 69, 0.25);
                            transform: translateX(2px);
                        }
                        </style>""", unsafe_allow_html=True)

                        sorted_vars = sorted(valid_vars, key=lambda x: x.get('name'))
                        
                        if not sorted_vars:
                            st.caption("No valid common variables found in the file.")
                        else:
                            num_columns = 3
                            cols = st.columns(num_columns)
                            
                            for i, var in enumerate(sorted_vars):
                                var_name = var.get('name')
                                prefix = '&' if var.get('type') == 'dict' else '$' 
                                
                                with cols[i % num_columns]:
                                    st.markdown(
                                        f"<div class='common-var-code' title='{prefix}{{{var_name}}}'>{prefix}{{{var_name}}}</div>", 
                                        unsafe_allow_html=True
                                    )

            # --- Keywords Display ---
            if ws_state.get('keywords'):
    
                all_keywords = ws_state['keywords']
    
                if 'show_keywords' not in st.session_state:
                    st.session_state.show_keywords = False
                
                st.markdown("""
                <style>
                button[key="toggle_keywords"] {
                    padding: 2px 8px !important;
                    min-height: 28px !important;
                    height: 28px !important;
                    font-size: 0.85rem !important;
                }
                </style>
                """, unsafe_allow_html=True)
                
                with st.container(border=True):
                    col1, col2 = st.columns([11, 1])
                    
                    with col1:
                        st.markdown(f"""
                        <div style='display: flex; align-items: center; gap: 10px;'>
                            <span style='font-size: 1.05rem; font-weight: 600; color: #cbd5e1;'>
                                📚 Common Keywords
                            </span>
                            <span style='
                                background: rgba(99, 102, 241, 0.2);
                                border: 1px solid rgba(99, 102, 241, 0.4);
                                color: #818cf8;
                                padding: 2px 8px;
                                border-radius: 12px;
                                font-size: 0.75rem;
                                font-weight: 600;
                            '>
                                {len(all_keywords)} items
                            </span>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    with col2:
                        toggle_icon = "▼" if st.session_state.show_keywords else "▶"
                        if st.button(
                            toggle_icon, 
                            key="toggle_keywords",
                            help="Show/Hide",
                            use_container_width=True
                        ):
                            st.session_state.show_keywords = not st.session_state.show_keywords
                            st.rerun()
                    
                    if st.session_state.show_keywords:
                        st.markdown("---")
                        
                        categorized = categorize_keywords(all_keywords)
                        stats = get_category_stats(categorized)
                        expansion_config = get_expansion_config()
                        
                        col_stats1, col_stats2, col_stats3 = st.columns(3)
                        with col_stats1: st.metric("📊 Total Keywords", stats['total_keywords'])
                        with col_stats2: st.metric("📁 Categories", stats['total_categories'])
                        with col_stats3: st.metric("🧩 Others", stats['uncategorized'])
                        
                        st.markdown("---")
                        
                        categories_to_sort = [k for k in categorized.keys() if k != "🧩 Others"]
                        sorted_categories = sorted(categories_to_sort, key=get_category_priority)
                        if "🧩 Others" in categorized and categorized["🧩 Others"]:
                            sorted_categories.append("🧩 Others")

                        mid_point = (len(sorted_categories) + 1) // 2
                        left_col_categories = sorted_categories[:mid_point]
                        right_col_categories = sorted_categories[mid_point:]
                        col1, col2 = st.columns(2)

                        # LEFT COLUMN
                        with col1:
                            for category in left_col_categories:
                                kws = categorized.get(category, [])
                                if not kws: continue
                                
                                is_expanded = expansion_config.get(category, False)
                                
                                with st.expander(f"**{category}** ({len(kws)} keywords)", expanded=is_expanded):
                                    for kw in sorted(kws, key=lambda x: x['name']):
                                        with st.expander(f"`{kw['name']}`", expanded=False):
                                            if kw.get('args'):
                                                args_str = ', '.join([arg["name"] for arg in kw['args']])
                                                st.caption(f"**Args:** `{args_str}`")
                                            else:
                                                st.caption("**Args:** _None_")

                        # RIGHT COLUMN
                        with col2:
                            for category in right_col_categories:
                                kws = categorized.get(category, [])
                                if not kws: continue
                                
                                is_expanded = expansion_config.get(category, False)
                                
                                with st.expander(f"**{category}** ({len(kws)} keywords)", expanded=is_expanded):
                                    for kw in sorted(kws, key=lambda x: x['name']):
                                        with st.expander(f"`{kw['name']}`", expanded=False):
                                            if kw.get('args'):
                                                args_str = ', '.join([arg["name"] for arg in kw['args']])
                                                st.caption(f"**Args:** `{args_str}`")
                                            else:
                                                st.caption("**Args:** _None_")

    # --- RIGHT PANEL: LOCATORS ---
    with panel_grid[1]:
        st.markdown("#### <i class='fa-solid fa-bullseye'></i> Locators", unsafe_allow_html=True)
        with st.container(border=True):
            with st.expander("🍔 Menu Locator Management", expanded=False):
                render_menu_locator_manager()
            
            with st.expander("📁 Load from .robot file(s)", expanded=True):
                
                uploaded_locator_files = st.file_uploader(
                    "Browse for locator files (multi-upload)", 
                    type=['robot', 'resource'], 
                    key="studio_locator_uploader_final_2",
                    accept_multiple_files=True
                )
                
                if uploaded_locator_files:
                    total_loaded = 0
                    new_files_processed = False

                    for uploaded_file in uploaded_locator_files:
                        if any(loc.get('page_name') == uploaded_file.name for loc in ws_state['locators']):
                            st.toast(f"File '{uploaded_file.name}' is already loaded. Skipping.", icon="⚠️")
                            continue
                        
                        new_files_processed = True
                        with st.spinner(f"Loading from {uploaded_file.name}..."):
                            content = uploaded_file.getvalue().decode("utf-8")
                            locators = read_robot_variables_from_content(content)
                            for loc in locators:
                                loc['page_name'] = uploaded_file.name
                                if 'id' not in loc or not loc['id']:
                                    loc['id'] = str(uuid.uuid4())
                            ws_state['locators'].extend(locators)
                            total_loaded += len(locators)

                    if new_files_processed: st.success(f"Loaded {total_loaded} new locators.")
                    if new_files_processed: st.rerun()
            
            with st.expander("📄 Add from HTML", expanded=True):
                for i, page in enumerate(ws_state['html_pages']):
                    # -------------------------------------------------------
                    # 1. ปรับ UI: Category (ซ้าย) -> Name (ขวา)
                    # -------------------------------------------------------
                    # col1: Category (20%)
                    # col2: Page Name (40%) - ใช้เป็น Prefix กรณี OTHER
                    # col3: Edit Button (30%)
                    # col4: Delete Button (10%)
                    col1, col2, col3, col4 = st.columns([1.8, 2.5, 1.2, 0.8])
                    
                    # ส่วนที่ 1: Dropdown Category (ย้ายมาไว้ข้างหน้า)
                    # Col 1: Category Dropdown
                    with col1:
                        if 'category_mode' not in page: page['category_mode'] = 'MAINLIST'
                        page['category_mode'] = st.selectbox(
                            f"Cat {i}", 
                            ["MAINLIST", "DETAIL", "OTHER"],
                            key=f"cat_select_{i}",
                            index=["MAINLIST", "DETAIL", "OTHER"].index(page.get('category_mode', 'MAINLIST')),
                            label_visibility="collapsed"
                        )

                    # Col 2: Page Name (ทำหน้าที่เป็น Prefix ด้วยถ้าเลือก OTHER)
                    with col2:
                        # เปลี่ยน Placeholder ให้สื่อความหมาย
                        ph_text = "PREFIX_NAME (UPPERCASE)" if page['category_mode'] == 'OTHER' else "Page Name"
                        page['name'] = st.text_input(
                            f"Page Name {i}", 
                            value=page['name'], 
                            key=f"studio_html_page_name_{i}", 
                            label_visibility="collapsed", 
                            placeholder=ph_text
                        )

                    # Col 3: Edit HTML
                    with col3:
                        if st.button(f"✏️ Edit HTML", key=f"studio_edit_html_{i}", width='stretch'):
                            ws_state['editing_html_index'] = i
                            st.rerun()
                    
                    # Col 4: Delete Page
                    with col4:
                         if len(ws_state['html_pages']) > 1:
                            if st.button(f"🗑️", key=f"studio_remove_html_page_{i}", help="Remove page", width='stretch'):
                                ws_state['html_pages'].pop(i)
                                st.rerun()

                if st.button("➕ Add another HTML page", width='stretch', type="secondary"):
                    ws_state['html_pages'].append({
                        'name': f'Page {len(ws_state["html_pages"]) + 1}', 
                        'html': '',
                        'category_mode': 'MAINLIST'
                    })
                    st.rerun()
                
                st.markdown("---")
                
                # -------------------------------------------------------
                # BUTTON: Find All Locators
                # -------------------------------------------------------
                if st.button("Find All Locators from HTML", width='stretch', type="primary"):
                    with st.spinner("Finding locators..."):
                        parser = HTMLLocatorParser()
                        new_locators_found = 0
                        new_checkbox_locators = 0

                        # Reset checkbox & Clean old locators
                        ws_state['checkbox_locators'] = []
                        html_page_names = [p['name'] for p in ws_state.get('html_pages', [])]
                        ws_state['locators'] = [
                            loc for loc in ws_state.get('locators', [])
                            if loc.get('page_name') not in html_page_names
                        ]

                        for page in ws_state['html_pages']:
                            if page['html']:
                                # ✅ LOGIC 1: กำหนด Prefix
                                prefix_str = ""
                                if page.get('category_mode') == 'OTHER':
                                    # OTHER: ใช้ Page Name แปลงเป็น Upper Case
                                    raw_name = page.get('name', '').strip().upper()
                                    prefix_str = re.sub(r'[^A-Z0-9_]', '_', raw_name) # ตัดอักขระพิเศษ
                                else:
                                    # MAINLIST/DETAIL: ใช้ตามนั้น
                                    prefix_str = page.get('category_mode', '')

                                # ✅ LOGIC 2: Checkbox (คงเดิม)
                                checkbox_analysis = analyze_checkbox_structure(page['html'])
                                soup = BeautifulSoup(page['html'], 'html.parser')
                                # (Checkbox Detection Logic - แบบย่อ)
                                if checkbox_analysis.get('framework') == 'ant_design':
                                    ant_checkboxes = soup.find_all('div', class_=lambda x: x and 'ant-checkbox-wrapper' in x)
                                    for ant_cb in ant_checkboxes:
                                        label_text = None
                                        for span in ant_cb.find_all('span', recursive=True):
                                            text = span.get_text(strip=True)
                                            if text: label_text = text; break
                                        if label_text:
                                            # Checkbox มักมีชื่อเฉพาะอยู่แล้ว อาจไม่ต้องเติม Prefix หรือเติมก็ได้
                                            var_name = label_text.replace(' ', '_').replace('-', '_').upper() + '_CHECKBOX'
                                            xpath = checkbox_analysis['pattern'].replace('::labelcheckbox::', label_text)
                                            checkbox_loc = {'id': str(uuid.uuid4()), 'name': f"LOCATOR_{var_name}", 'value': xpath, 'page_name': page['name'], 'label': label_text}
                                            ws_state.setdefault('checkbox_locators', []).append(checkbox_loc)
                                            new_checkbox_locators += 1
                                # (Skipping Bootstrap/Standard logic for brevity, assuming consistent with existing)
                                
                                if new_checkbox_locators > 0:
                                    page['html_content_snapshot'] = page['html']
                                    page['checkbox_pattern'] = checkbox_analysis

                                # ✅ LOGIC 3: Parse Normal Locators (ส่ง Prefix เข้าไป)
                                # แก้ไข: เรียก parse_html พร้อม page_category
                                all_fields = parser.parse_html(page['html'], page_category=prefix_str)
                                
                                for field in all_fields:
                                    if '_CHECKBOX' in field.variable.upper(): continue
                                    
                                    # Parser จัดการเติม Prefix ให้แล้วใน field.variable
                                    new_loc_name = f"LOCATOR_{field.variable}"

                                    if not any(loc['name'] == new_loc_name for loc in ws_state['locators']):
                                        ws_state['locators'].append({
                                            'id': str(uuid.uuid4()),
                                            'name': new_loc_name,
                                            'value': field.xpath,
                                            'page_name': page['name']
                                        })
                                        new_locators_found += 1
                        
                        st.success(f"Found {new_locators_found} new locators and {new_checkbox_locators} new checkboxes.")
                        st.rerun()

            # ============================================================
            # 2. DUPLICATE LOCATOR CHECKER (ส่วนเพิ่มใหม่)
            # ============================================================
            all_current_locators = ws_state.get('locators', [])
            locator_counts = {}
            for loc in all_current_locators:
                name = loc['name']
                if name not in locator_counts: locator_counts[name] = []
                locator_counts[name].append(loc)
            
            duplicates = {name: items for name, items in locator_counts.items() if len(items) > 1}
            
            if duplicates:
                st.markdown("---")
                with st.container(border=True):
                    st.markdown(f"#### ⚠️ Found {len(duplicates)} Duplicate Locator Names")
                    
                    col_dup_1, col_dup_2 = st.columns(2)
                    
                    # Option A: Remove
                    with col_dup_1:
                        if st.button("🗑️ Remove Duplicates (Keep 1st)", use_container_width=True, type="secondary"):
                            unique_locators = []
                            seen_names = set()
                            for loc in all_current_locators:
                                if loc['name'] not in seen_names:
                                    unique_locators.append(loc)
                                    seen_names.add(loc['name'])
                            ws_state['locators'] = unique_locators
                            st.rerun()

                    # Option B: Rename
                    with col_dup_2:
                        dup_prefix = st.text_input("Insert Prefix (e.g. DUP_)", value="DUP_")
                        if st.button(f"✏️ Rename Duplicates", use_container_width=True, type="primary"):
                            temp_seen_counts = {}
                            renamed_count = 0
                            for loc in ws_state['locators']:
                                name = loc['name']
                                if name in duplicates:
                                    temp_seen_counts[name] = temp_seen_counts.get(name, 0) + 1
                                    if temp_seen_counts[name] > 1:
                                        # แทรก Prefix หลัง Underscore ตัวที่ 2 (LOCATOR_MAINLIST_...)
                                        parts = name.split('_')
                                        if len(parts) >= 3:
                                            new_parts = parts[:2] + [dup_prefix.strip('_')] + parts[2:]
                                            loc['name'] = "_".join(new_parts)
                                        else:
                                            loc['name'] = f"{name}_{dup_prefix.strip('_')}"
                                        renamed_count += 1
                            st.success(f"Renamed {renamed_count} items.")
                            st.rerun()

    # --- HTML Editor Dialog ---
    if ws_state.get('editing_html_index') is not None:
        if ws_state['editing_html_index'] < len(ws_state['html_pages']):
            html_editor_dialog()

    # --- 3. LOCATOR STAGING AREA (Collapsible) ---
    if ws_state.get('locators') or ws_state.get('checkbox_locators'): # <-- ปรับเงื่อนไข
        for idx, loc in enumerate(ws_state.get('locators', [])):
            if 'id' not in loc or not loc['id']:
                ws_state['locators'][idx]['id'] = str(uuid.uuid4())
        
        with st.expander("#### 📝 Locator Staging Area", expanded=True):
            
            html_page_names = [p['name'] for p in ws_state.get('html_pages', [])]
            all_file_locators = [
                loc for loc in ws_state.get('locators', []) 
                if loc.get('page_name') not in html_page_names
            ]
            
            locators_by_file = {}
            for loc in all_file_locators:
                filename = loc.get('page_name')
                if not filename: continue
                if filename not in locators_by_file:
                    locators_by_file[filename] = []
                locators_by_file[filename].append(loc)

            st.markdown("<h6>🔒 From Files (Loaded)</h6>", unsafe_allow_html=True)
            
            # ✅ แยกแสดงไฟล์ที่ auto-load และ manual upload
            auto_loaded_files = []
            manual_loaded_files = []
            
            for filename in sorted(locators_by_file.keys()):
                # เช็คว่าเป็นไฟล์จาก pageobjects หรือไม่
                if filename.replace(os.sep, '/').startswith('pageobjects/'):
                    auto_loaded_files.append(filename)
                else:
                    manual_loaded_files.append(filename)
            
            # ✅ แสดง Auto-loaded files
            if auto_loaded_files:
                st.markdown("**🤖 Auto-loaded from `pageobjects` folder:**")
                for filename in auto_loaded_files:
                    locators_in_file = locators_by_file[filename]
                    
                    with st.expander(f"📄 **{filename}** ({len(locators_in_file)} items)", expanded=False):
                        
                        if st.button(
                            f"🗑️ Unload locators from '{os.path.basename(filename)}'", 
                            key=f"unload_auto_file_{filename.replace('.', '_').replace('/', '_').replace(os.sep, '_')}",
                            width='content',
                            type="secondary"
                        ):
                            ws_state['locators'] = [
                                loc for loc in ws_state['locators'] 
                                if loc.get('page_name') != filename
                            ]
                            st.success(f"Unloaded {len(locators_in_file)} locators from '{filename}'.")
                            st.rerun()
                       
                        st.markdown("""
                            <style>
                            .locator-grid-container { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
                            .locator-pill {
                                background-color: rgba(88, 166, 255, 0.1);
                                border: 1px solid rgba(88, 166, 255, 0.2);
                                color: #cbd5e1; padding: 5px 10px; border-radius: 12px;
                                font-family: monospace; font-size: 0.8rem;
                                white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: left;
                            }
                            </style>
                        """, unsafe_allow_html=True)
                        
                        html_grid = "<div class='locator-grid-container'>"
                        for loc in sorted(locators_in_file, key=lambda x: x['name']):
                            clean_name = get_clean_locator_name(loc['name'])
                            html_grid += f"<div class='locator-pill' title='{clean_name}'>{clean_name}</div>"
                        html_grid += "</div>"
                        st.markdown(html_grid, unsafe_allow_html=True)
            
            # ✅ แสดง Manually uploaded files
            if manual_loaded_files:
                if auto_loaded_files:
                    st.markdown("---")
                st.markdown("**📤 Manually Uploaded:**")
                for filename in manual_loaded_files:
                    locators_in_file = locators_by_file[filename]
                    
                    with st.expander(f"📄 **{filename}** ({len(locators_in_file)} items)", expanded=False):
                        
                        if st.button(
                            f"🗑️ Unload locators from '{filename}'", 
                            key=f"unload_manual_file_{filename.replace('.', '_').replace('/', '_').replace(os.sep, '_')}",
                            width='content',
                            type="secondary"
                        ):
                            ws_state['locators'] = [
                                loc for loc in ws_state['locators'] 
                                if loc.get('page_name') != filename
                            ]
                            st.success(f"Unloaded {len(locators_in_file)} locators from '{filename}'.")
                            st.rerun()
                       
                        st.markdown("""
                            <style>
                            .locator-grid-container { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; }
                            .locator-pill {
                                background-color: rgba(88, 166, 255, 0.1);
                                border: 1px solid rgba(88, 166, 255, 0.2);
                                color: #cbd5e1; padding: 5px 10px; border-radius: 12px;
                                font-family: monospace; font-size: 0.8rem;
                                white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: left;
                            }
                            </style>
                        """, unsafe_allow_html=True)
                        
                        html_grid = "<div class='locator-grid-container'>"
                        for loc in sorted(locators_in_file, key=lambda x: x['name']):
                            clean_name = get_clean_locator_name(loc['name'])
                            html_grid += f"<div class='locator-pill' title='{clean_name}'>{clean_name}</div>"
                        html_grid += "</div>"
                        st.markdown(html_grid, unsafe_allow_html=True)
            
            # ถ้าไม่มีไฟล์เลย
            if not auto_loaded_files and not manual_loaded_files:
                with st.container(border=True):
                    st.caption("No locators loaded from files yet.")

            # ส่วน HTML Locators (✏️ From HTML (Editable))
            st.markdown("<h6>✏️ From HTML (Editable)</h6>", unsafe_allow_html=True)
            
            # ✅ ดึง Checkbox locators มาจัดกลุ่มตาม Page
            html_locators_by_page = {}
            for i, loc in enumerate(ws_state['locators']):
                if loc.get('page_name') in html_page_names:
                    page_name = loc['page_name']
                    if page_name not in html_locators_by_page:
                        html_locators_by_page[page_name] = []
                    html_locators_by_page[page_name].append((i, loc))
            
            checkbox_locators_by_page = {}
            for loc in ws_state.get('checkbox_locators', []):
                if loc.get('page_name') in html_page_names:
                    page_name = loc['page_name']
                    if page_name not in checkbox_locators_by_page:
                        checkbox_locators_by_page[page_name] = []
                    checkbox_locators_by_page[page_name].append(loc)

            if not html_locators_by_page and not checkbox_locators_by_page:
                with st.container(border=True):
                    st.caption("No locators added from HTML yet.")
            else:
                st.markdown("""
                    <style>
                    .locator-header {
                        display: grid; grid-template-columns: 50% 42% 8%;
                        font-weight: 900; padding: 8px 4px;
                        background-color: rgba(128, 128, 128, 0.15);
                        border-radius: 4px; margin-bottom: 8px; font-size: 0.9rem;
                        background-color: rgba(88, 166, 255, 0.15);
                        border: 1px solid rgba(88, 166, 255, 0.3);
                        color: #a3c9ff;
                        text-align: center;
                    }
                    .locator-header div { padding: 0 4px; }
                    input[key*="loc_name_"],
                    input[key*="loc_value_"] {
                        font-size: 0.7rem !important; /* 👈 ปรับขนาดฟอนต์ตรงนี้ */
                        font-family: monospace !important;
                    }
                    </style>
                """, unsafe_allow_html=True)
                
                # ✅ แก้ไข: วนลูปตาม html_page_names เพื่อให้แสดงผลทุกหน้า
                for page_name in html_page_names:
                    locators_in_page = html_locators_by_page.get(page_name, [])
                    checkboxes_in_page = checkbox_locators_by_page.get(page_name, [])
                    
                    if not locators_in_page and not checkboxes_in_page:
                        continue # ข้ามถ้าหน้านี้ไม่มีอะไรเลย

                    # ✅ สร้าง Title แบบไดนามิก
                    expander_title = f"📄 **{page_name}** ({len(locators_in_page)} locators"
                    if checkboxes_in_page:
                        expander_title += f", {len(checkboxes_in_page)} checkboxes"
                    expander_title += ")"
                    
                    with st.expander(expander_title, expanded=True):
                        
                        # ✅ Logic ใหม่: แสดงปุ่มตามสถานะ
                        
                        # หา page data
                        page_data = None
                        for p in ws_state.get('html_pages', []):
                            if p['name'] == page_name:
                                page_data = p
                                break
                        
                        # กรณีที่ 1: เจอ checkbox จาก auto-detect → แสดงปุ่ม "Found X Checkbox(es)"
                        if checkboxes_in_page and len(checkboxes_in_page) > 0:
                            if st.button(
                                f"✅ Found {len(checkboxes_in_page)} Checkbox(es) - Click to Suggest Handling", 
                                key=f"gen_cb_btn_{page_name.replace(' ','_')}", 
                                type="primary",
                                use_container_width=True
                            ):
                                if page_data:
                                    page_html = page_data.get('html_content_snapshot', page_data.get('html', ''))
                                    
                                    if page_html:
                                        try:
                                            # Analyze checkbox structure
                                            checkbox_analysis = analyze_checkbox_structure(page_html)
                                            
                                            # หา labels
                                            soup = BeautifulSoup(page_html, 'html.parser')
                                            found_labels = []
                                            
                                            if checkbox_analysis.get('framework') == 'ant_design':
                                                ant_checkboxes = soup.find_all('div', class_=lambda x: x and 'ant-checkbox-wrapper' in x)
                                                for ant_cb in ant_checkboxes:
                                                    label_spans = ant_cb.find_all('span', recursive=True)
                                                    for span in label_spans:
                                                        span_classes = span.get('class', [])
                                                        if isinstance(span_classes, str):
                                                            span_classes = span_classes.split()
                                                        if any('ant-checkbox' in cls for cls in span_classes):
                                                            continue
                                                        text = span.get_text(strip=True)
                                                        if text:
                                                            found_labels.append(text)
                                                            break
                                            
                                            # บันทึกข้อมูล
                                            st.session_state['html_content'] = page_html
                                            st.session_state['checkbox_page_name'] = page_name
                                            st.session_state['checkbox_pattern'] = checkbox_analysis.get('pattern', '')
                                            st.session_state['checkbox_framework'] = checkbox_analysis.get('framework', 'standard')
                                            st.session_state['checkbox_description'] = checkbox_analysis.get('description', '')
                                            st.session_state['checkbox_found_labels'] = found_labels
                                            
                                            # เปิด Dialog
                                            st.session_state['show_checkbox_generator'] = True
                                            st.rerun()
                                            
                                        except Exception as e:
                                            st.error(f"Error analyzing checkbox: {e}")
                                    else:
                                        st.error("HTML content not found")
                            
                            st.markdown("---")
                        
                        # กรณีที่ 2: ไม่เจอ checkbox จาก auto-detect → แสดงปุ่ม manual
                        elif page_data and page_data.get('html'):
                            st.info("ℹ️ No checkboxes detected automatically. You can manually analyze the HTML structure.")
                            
                            if st.button(
                                f"🔲 Manually Analyze Checkbox Structure", 
                                key=f"manual_analyze_cb_{page_name.replace(' ','_')}", 
                                type="secondary",
                                use_container_width=True
                            ):
                                page_html = page_data.get('html', '')
                                
                                if page_html:
                                    try:
                                        # Analyze checkbox structure
                                        checkbox_analysis = analyze_checkbox_structure(page_html)
                                        
                                        # หา labels (ถึงแม้จะไม่เจอก็พยายามหา)
                                        soup = BeautifulSoup(page_html, 'html.parser')
                                        found_labels = []
                                        
                                        # ลอง detect หลายแบบ
                                        frameworks_to_try = ['ant_design', 'bootstrap', 'standard']
                                        
                                        for fw in frameworks_to_try:
                                            if fw == 'ant_design':
                                                checkboxes = soup.find_all('div', class_=lambda x: x and 'ant-checkbox-wrapper' in x)
                                                for cb in checkboxes:
                                                    label_spans = cb.find_all('span', recursive=True)
                                                    for span in label_spans:
                                                        span_classes = span.get('class', [])
                                                        if isinstance(span_classes, str):
                                                            span_classes = span_classes.split()
                                                        if any('ant-checkbox' in cls for cls in span_classes):
                                                            continue
                                                        text = span.get_text(strip=True)
                                                        if text:
                                                            found_labels.append(text)
                                                            break
                                            
                                            elif fw == 'bootstrap':
                                                checkboxes = soup.find_all('input', class_=lambda x: x and 'form-check-input' in x, type='checkbox')
                                                for cb in checkboxes:
                                                    label = cb.find_next_sibling('label', class_='form-check-label')
                                                    if label:
                                                        found_labels.append(label.get_text(strip=True))
                                            
                                            elif fw == 'standard':
                                                checkboxes = soup.find_all('input', type='checkbox')
                                                for cb in checkboxes:
                                                    cb_id = cb.get('id')
                                                    label = None
                                                    
                                                    if cb_id:
                                                        label = soup.find('label', attrs={'for': cb_id})
                                                    
                                                    if not label:
                                                        label = cb.find_next_sibling('label')
                                                    
                                                    if not label:
                                                        label = cb.find_parent('label')
                                                    
                                                    if label:
                                                        found_labels.append(label.get_text(strip=True))
                                            
                                            if found_labels:
                                                break
                                        
                                        # บันทึกข้อมูล
                                        st.session_state['html_content'] = page_html
                                        st.session_state['checkbox_page_name'] = page_name
                                        st.session_state['checkbox_pattern'] = checkbox_analysis.get('pattern', '')
                                        st.session_state['checkbox_framework'] = checkbox_analysis.get('framework', 'standard')
                                        st.session_state['checkbox_description'] = checkbox_analysis.get('description', '')
                                        st.session_state['checkbox_found_labels'] = found_labels
                                        
                                        # เปิด Dialog
                                        st.session_state['show_checkbox_generator'] = True
                                        st.rerun()
                                        
                                    except Exception as e:
                                        st.error(f"Error analyzing checkbox: {e}")
                            
                            st.markdown("---")

                        # ส่วนแสดงผล Locator แบบ 2 คอลัมน์
                        mid_point = (len(locators_in_page) + 1) // 2
                        left_locators = locators_in_page[:mid_point]
                        right_locators = locators_in_page[mid_point:]
                        left_panel, right_panel = st.columns([1, 1], gap="medium")
                        
                        with left_panel:
                            with st.container(border=True):
                                st.markdown('<div class="locator-header"><div>Name</div><div>Value</div><div style="text-align: center;">Del</div></div>', unsafe_allow_html=True)
                                for original_index, locator_data in left_locators:
                                    loc_id = locator_data.get('id')
                                    if not loc_id:
                                        loc_id = str(uuid.uuid4())
                                        locator_data['id'] = loc_id
                                        ws_state['locators'][original_index]['id'] = loc_id   
                                                                         
                                    col_name, col_value, col_action = st.columns([50,42 ,10])
                                    with col_name: new_name = st.text_input("Name", value=locator_data['name'], key=f"loc_name_L_{page_name}_{loc_id}", label_visibility="collapsed", placeholder="Name")
                                    with col_value: new_value = st.text_input("Value", value=locator_data['value'], key=f"loc_value_L_{page_name}_{loc_id}", label_visibility="collapsed", placeholder="XPath")
                                    with col_action:
                                        if st.button("🗑️", key=f"loc_del_L_{page_name}_{loc_id}", help="Delete", width='stretch'):
                                            ws_state['locators'] = [loc for loc in ws_state['locators'] if loc.get('id') != loc_id]
                                            st.rerun()
                                    
                                    if new_name != locator_data['name'] or new_value != locator_data['value']:
                                        for idx, loc in enumerate(ws_state['locators']):
                                            if loc.get('id') == loc_id:
                                                ws_state['locators'][idx]['name'] = new_name
                                                ws_state['locators'][idx]['value'] = new_value
                                                break
                        
                        with right_panel:
                            with st.container(border=True):
                                st.markdown('<div class="locator-header"><div>Name</div><div>Value</div><div style="text-align: center;">Del</div></div>', unsafe_allow_html=True)
                                if right_locators:
                                    for original_index, locator_data in right_locators:
                                        loc_id = locator_data.get('id')
                                        if not loc_id:
                                            loc_id = str(uuid.uuid4())
                                            locator_data['id'] = loc_id
                                            ws_state['locators'][original_index]['id'] = loc_id
                                        
                                        col_name, col_value, col_action = st.columns([50, 42, 10])
                                        with col_name: new_name = st.text_input("Name", value=locator_data['name'], key=f"loc_name_R_{page_name}_{loc_id}", label_visibility="collapsed", placeholder="Name")
                                        with col_value: new_value = st.text_input("Value", value=locator_data['value'], key=f"loc_value_R_{page_name}_{loc_id}", label_visibility="collapsed", placeholder="XPath")
                                        with col_action:
                                            if st.button("🗑️", key=f"loc_del_R_{page_name}_{loc_id}", help="Delete", width='stretch'):
                                                ws_state['locators'] = [loc for loc in ws_state['locators'] if loc.get('id') != loc_id]
                                                st.rerun()
                                        if new_name != locator_data['name'] or new_value != locator_data['value']:
                                            for idx, loc in enumerate(ws_state['locators']):
                                                if loc.get('id') == loc_id:
                                                    ws_state['locators'][idx]['name'] = new_name
                                                    ws_state['locators'][idx]['value'] = new_value
                                                    break
                                else:
                                    st.caption("(Empty)")

            show_checkbox_generator_ui()
            # ส่วน Export Options
            # ========================================================
            # 💾 EXPORT OPTIONS (แก้ไข Logic ปุ่ม Reload ให้ชัวร์)
            # ========================================================
            st.markdown("---")
            st.subheader("💾 Export Options")
            
            if 'locator_save_option' not in st.session_state:
                st.session_state.locator_save_option = "Append to Existing File"

            st.session_state.locator_save_option = st.radio(
                "Save Mode",
                ["Append to Existing File", "Create New File"],
                key="radio_locator_save_mode",
                horizontal=True,
                label_visibility="collapsed"
            )
            save_option = st.session_state.locator_save_option

            # Prepare Locators String
            html_locators = [loc for loc in ws_state['locators'] if loc.get('page_name') in [p['name'] for p in ws_state.get('html_pages', [])]]
            locators_string = ""
            if html_locators:
                 named_locators = [loc for loc in html_locators if loc['name']]
                 if named_locators:
                     max_len = max(len(f"${{{loc['name']}}}") for loc in named_locators) + 4
                     locators_string = "\n".join([f"{f'${{{loc['name']}}}'.ljust(max_len)}{loc['value']}" for loc in sorted(named_locators, key=lambda x: x['name'])])

            # --------------------------------------------------------
            # MODE 1: APPEND TO EXISTING FILE
            # --------------------------------------------------------
            if save_option == "Append to Existing File":
                all_robot_files = st.session_state.project_structure.get('robot_files', [])
                pageobject_files = [f for f in all_robot_files if f.replace(os.sep, '/').startswith('pageobjects/')]
                
                if not pageobject_files:
                    st.warning("No files found in `pageobjects` folder.")
                else:
                    selected_file = st.selectbox("Select file:", options=sorted([f.replace(os.sep, '/') for f in pageobject_files]), key="locator_append_target")
                    show_checkbox_template_status()

                    # [ปุ่ม Save]
                    if st.button("➕ Append Locators", key="append_locators_btn"):
                        has_locators = bool(html_locators and locators_string)
                        has_checkbox_template = st.session_state.get('checkbox_template', {}).get('enabled', False)

                        if not has_locators and not has_checkbox_template:
                            st.warning("No data to save.")
                        else:
                            full_path = os.path.join(st.session_state.project_path, selected_file)
                            
                            # Perform Save
                            success_loc = True
                            if has_locators:
                                success_loc, _ = append_robot_content_intelligently(full_path, variables_code=locators_string)
                            
                            success_cb = True
                            if has_checkbox_template:
                                success_cb, _ = append_checkbox_template_to_file(full_path)
                            
                            if success_loc and success_cb:
                                # ✅ 1. ตั้งค่า State ว่าสำเร็จ
                                st.session_state['locator_append_success_file'] = selected_file
                                st.session_state['checkbox_template'] = {'enabled': False}
                                # ❌ สำคัญ: ห้ามใส่ st.rerun() ตรงนี้ เพื่อให้โค้ดไหลลงไปแสดงปุ่ม Reload ด้านล่าง

                    # [ปุ่ม Reload] - เช็ค State จากด้านบน
                    if st.session_state.get('locator_append_success_file') == selected_file:
                        st.markdown("""<div style='background:#e6fffa;padding:10px;border-radius:5px;border:1px solid #38b2ac;color:#2c7a7b;margin-top:10px;'>✅ Saved! Click Reload to update assets.</div>""", unsafe_allow_html=True)
                        
                        if st.button("🔄 Reload Assets", key="reload_ui_append", type="primary", use_container_width=True):
                            # 1. หาชื่อ Page ของ HTML ที่ค้างอยู่
                            html_page_names = [p['name'] for p in ws_state.get('html_pages', [])]
                            
                            # 2. ลบ Locator ที่มาจาก HTML เหล่านั้นออกจาก Memory
                            ws_state['locators'] = [
                                loc for loc in ws_state['locators'] 
                                if loc.get('page_name') not in html_page_names
                            ]
                            
                            # 3. เคลียร์ HTML Input และ Checkbox ให้ว่างเปล่า
                            ws_state['html_pages'] = [{'name': 'Page 1', 'html': '', 'category_mode': 'MAINLIST'}]
                            ws_state['checkbox_locators'] = []

                            # 4. สั่งโหลดไฟล์จาก Disk ใหม่ (เพื่อให้ Locator ที่เพิ่ง Save ไป โผล่มาในส่วน From Files แทน)
                            st.session_state.locators_auto_loaded = False
                            
                            # 5. เคลียร์สถานะ Success
                            del st.session_state['locator_append_success_file']
                            st.rerun()

            # --------------------------------------------------------
            # MODE 2: CREATE NEW FILE
            # --------------------------------------------------------
            elif save_option == "Create New File":
                new_file_name = st.text_input("New file name:", value="new_locators.robot", key="locator_new_filename")
                show_checkbox_template_status()
                
                # [ปุ่ม Save]
                if st.button("📝 Create File", key="create_locators_btn"):
                    if not new_file_name.endswith(('.robot', '.resource')):
                        st.error("Invalid extension.")
                    else:
                        full_content = generate_file_content_with_checkbox(locators_string)
                        save_dir = os.path.join(st.session_state.project_path, "pageobjects")
                        os.makedirs(save_dir, exist_ok=True)
                        full_path = os.path.join(save_dir, new_file_name)
                        
                        success = create_new_robot_file(full_path, full_content)
                        if success:
                            # ✅ 1. ตั้งค่า State ว่าสำเร็จ
                            st.session_state['show_file_created_success'] = {'path': os.path.relpath(full_path, st.session_state.project_path)}
                            st.session_state['checkbox_template'] = {'enabled': False}
                            st.session_state.project_structure = scan_robot_project(st.session_state.project_path)
                            # ❌ สำคัญ: ห้ามใส่ st.rerun() ตรงนี้

                # [ปุ่ม Reload] - เช็ค State จากด้านบน
                if 'show_file_created_success' in st.session_state and st.session_state.show_file_created_success:
                    st.markdown(f"""<div style='background:#e6fffa;padding:10px;border-radius:5px;border:1px solid #38b2ac;color:#2c7a7b;margin-top:10px;'>✅ Created: {st.session_state.show_file_created_success['path']}</div>""", unsafe_allow_html=True)
                    
                    if st.button("🔄 Reload Assets", key="reload_ui_create", type="primary", use_container_width=True):
                        # 1. หาชื่อ Page ของ HTML ที่ค้างอยู่
                        html_page_names = [p['name'] for p in ws_state.get('html_pages', [])]
                        
                        # 2. ลบ Locator ที่มาจาก HTML เหล่านั้นออกจาก Memory
                        ws_state['locators'] = [
                            loc for loc in ws_state['locators'] 
                            if loc.get('page_name') not in html_page_names
                        ]
                        
                        # 3. เคลียร์ HTML Input และ Checkbox ให้ว่างเปล่า
                        ws_state['html_pages'] = [{'name': 'Page 1', 'html': '', 'category_mode': 'MAINLIST'}]
                        ws_state['checkbox_locators'] = []

                        # 4. สั่งโหลดไฟล์จาก Disk ใหม่
                        st.session_state.locators_auto_loaded = False
                        
                        # 5. เคลียร์สถานะ Success
                        del st.session_state.show_file_created_success
                        st.rerun()


# ========================================================================
# 1. ฟังก์ชันแยก Checkbox จาก Locators ปกติ
# ========================================================================

def separate_checkbox_from_locators(all_locators):
    """
    แยก normal locators และ checkbox locators
    
    Args:
        all_locators: List of all locators
    
    Returns:
        tuple: (normal_locators, checkbox_locators)
    """
    normal = []
    checkbox = []
    
    for loc in all_locators:
        if '_CHECKBOX' in loc.get('name', '').upper():
            checkbox.append(loc)
        else:
            normal.append(loc)
    
    return normal, checkbox


# ========================================================================
# 2. ฟังก์ชันแสดง Checkbox Count + ปุ่ม Generate
# ========================================================================

def show_checkbox_count_and_button():
    """
    แสดงจำนวน checkbox และปุ่ม Generate
    เรียกใช้หลังจาก st.markdown("From HTML (Editable)")
    """
    ws_state = st.session_state.studio_workspace
    checkbox_count = len(ws_state.get('checkbox_locators', []))
    
    if checkbox_count > 0:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info(f"🔲 Found {checkbox_count} checkboxes")
        
        with col2:
            if st.button("🔲 Generate", key="gen_checkbox_btn", use_container_width=True):
                st.session_state['show_checkbox_generator'] = True
                st.rerun()


# ========================================================================
# 3. ฟังก์ชัน UI Checkbox Generator (Form สำหรับ config)
# ========================================================================

def show_checkbox_generator_ui():
    """
    แสดง UI สำหรับ config checkbox template
    """
    if not st.session_state.get('show_checkbox_generator', False):
        return
    
    st.markdown("---")
    st.markdown("#### 📋 Checkbox Template Generator")
    
    # ดึงข้อมูลที่บันทึกไว้
    page_name = st.session_state.get('checkbox_page_name', 'Page')
    detected_pattern = st.session_state.get('checkbox_pattern', '')
    framework = st.session_state.get('checkbox_framework', 'standard')
    description = st.session_state.get('checkbox_description', '')
    
    with st.container(border=True):
        # แสดงข้อมูล framework ที่ detect ได้
        st.info(f"🎯 Detected Framework: **{framework.upper().replace('_', ' ')}**")
        st.caption(f"Pattern: {description}")
        
        # Input: Page Name
        page_name = st.text_input(
            "Page Name:",
            value=page_name,
            key="checkbox_page_name_input",
            help="Auto-detected from HTML. You can edit it.",
            placeholder="e.g., RoleManagement"
        )
                
        # Preview
        if page_name and detected_pattern:
            st.markdown("---")
            st.markdown("**Suggestion:**")
            
            try:
                generated_code = generate_checkbox_template_and_keyword(page_name, detected_pattern)
                
                variables_preview = generated_code.get('variables', '# Error').replace('*** Variables ***\n', '').strip()
                keywords_preview = generated_code.get('keywords', '# Error').replace('*** Keywords ***\n', '').strip()
                
                st.markdown("`*** Variables ***`")
                st.code(variables_preview, language="robotframework")
                
                st.markdown("`*** Keywords ***`")
                st.code(keywords_preview, language="robotframework")
                
            except Exception as e:
                st.error(f"Error generating preview: {e}")
        
            if st.button("❌ Close", key="cancel_checkbox_btn", use_container_width=True):
                st.session_state['show_checkbox_generator'] = False
                st.rerun()

# ========================================================================
# 4. ฟังก์ชัน Append Checkbox (ใช้ใน Append Button)
# ========================================================================

def append_checkbox_template_to_file(file_path):
    """
    Append checkbox template และ keyword เข้าไฟล์
    
    Args:
        file_path: Path to robot file
    
    Returns:
        tuple: (success, message)
    """
    checkbox_template = st.session_state.get('checkbox_template', {})
    
    if not checkbox_template.get('enabled'):
        return True, "No checkbox template to append"
    
    try:        
        # Generate template and keyword
        result = generate_checkbox_template_and_keyword(
            checkbox_template['page_name'],
            checkbox_template['xpath']
        )
        
        # Append checkbox variable
        success1, msg1 = append_robot_content_intelligently(
            file_path,
            variables_code=result['variables']
        )
        
        # Append checkbox keyword
        success2, msg2 = append_robot_content_intelligently(
            file_path,
            keywords_code=result['keywords']
        )
        
        # Clear template after append
        st.session_state['checkbox_template'] = {'enabled': False}
        
        if success1 and success2:
            return True, "✅ Locators and checkbox template appended"
        else:
            return False, f"Error: {msg1}, {msg2}"
    
    except Exception as e:
        return False, f"Error appending checkbox: {str(e)}"


# ========================================================================
# 5. ฟังก์ชัน Generate Content สำหรับ Create New File
# ========================================================================

def generate_file_content_with_checkbox(locators_string):
    """
    Generate file content รวม checkbox template
    
    Args:
        locators_string: String of normal locators
    
    Returns:
        str: Full file content
    """
    import textwrap
    
    # Generate checkbox content if enabled
    checkbox_content = ""
    checkbox_template = st.session_state.get('checkbox_template', {})
    
    if checkbox_template.get('enabled'):
        try:            
            result = generate_checkbox_template_and_keyword(
                checkbox_template['page_name'],
                checkbox_template['xpath']
            )
            checkbox_content = "\n\n" + result['variables'] + "\n" + result['keywords']
        except Exception as e:
            st.warning(f"Could not generate checkbox template: {e}")
    
    # Create full content
    full_content = textwrap.dedent(f"""
*** Settings ***
Resource            ../resources/commonkeywords.resource

*** Variables ***

# --- START: Generated by Robot Framework Code Generator ---

{locators_string}

# ---  END: Generated by Robot Framework Code Generator  ---
{checkbox_content}
""")
    
    return full_content


# ========================================================================
# 6. ฟังก์ชันแสดงสถานะ Checkbox Template (Optional)
# ========================================================================

def show_checkbox_template_status():
    """
    แสดงสถานะ checkbox template ที่จะ export
    เรียกใช้ในส่วน Export Options
    """
    checkbox_template = st.session_state.get('checkbox_template', {})
    
    if checkbox_template.get('enabled'):
        with st.container(border=True):
            st.markdown("**📋 Checkbox Template:**")
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.caption(f"✅ Page: {checkbox_template['page_name']}")
                st.caption(f"✅ Variable: ${{{checkbox_template['variable']}}}")
                st.caption(f"✅ Keyword: {checkbox_template['keyword']}")
            
            with col2:
                if st.button("❌ Remove", key="remove_checkbox_template"):
                    st.session_state['checkbox_template'] = {'enabled': False}
                    st.rerun()

# ============================================================================
# MAIN APPLICATION
# ============================================================================

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point"""
    init_session_state() # 1. เรียก Init State ก่อนเสมอ
    
    st.markdown(
        '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">',
        unsafe_allow_html=True
    )

    ws_state = st.session_state.studio_workspace

    # 2. [ย้ายมา] กำหนด Callback Functions สำหรับ Dialogs ทั้งหมด
    
    # --- Callback สำหรับ Test Flow ---
    def add_step_to_timeline(context_timeline_key, new_step):
        ws_state.setdefault(context_timeline_key, []).append(new_step)

    # --- Callbacks และ Filters สำหรับ CRUD ---
    def add_step_to_crud(context_dict, new_step):
        section_key = context_dict.get("key")
        if section_key:
            crud_manager.add_step(section_key, new_step)

    def crud_keyword_filter(keyword):
        kw_name = keyword.get('name', '').lower()
        return not (kw_name.startswith('import datasource') or kw_name.startswith('request service'))

    # --- Callbacks และ Filters สำหรับ Keyword Factory ---
    def add_step_to_kw(context_dict, new_step):
        kw_id = context_dict.get("key")
        if kw_id:
            if new_step.get('keyword') == 'IF Condition' and 'args' not in new_step:
                 new_step['args'] = {'condition': ''}
            elif new_step.get('keyword') == 'END':
                 new_step['args'] = {}
            kw_manager.add_step(kw_id, new_step)

    def kw_factory_filter(keyword):
        all_generated_kw_names = [kw['name'] for kw in kw_manager.get_all_keywords()]
        kw_name = keyword.get('name', '')
        if kw_name.lower().startswith(('import datasource', 'request service')): return False
        if kw_name in ['IF Condition', 'ELSE IF Condition', 'ELSE', 'END']: return True
        if kw_name in all_generated_kw_names: return False
        return True

    # 3. [สำคัญ] บล็อกสำหรับตรวจสอบและวาด Dialogs ทั้งหมด
    
    # --- CRUD Dialogs ---
    if st.session_state.get('show_crud_add_dialog'):
        render_add_step_dialog_base(
            dialog_state_key='show_crud_add_dialog',
            context_state_key='crud_add_dialog_context',
            selected_kw_state_key='selected_kw_crud',
            add_step_callback=add_step_to_crud,
            ws_state=ws_state,
            title=f"Add New Step to CRUD Flow",
            keyword_filter_func=crud_keyword_filter,
            search_state_key="kw_search_dialog_crud",
            recently_used_state_key="recently_used_keywords_crud"
        )
        return  # <--- 🛑 [สำคัญมาก] ต้องมี RETURN

    elif st.session_state.get('show_api_csv_dialog'): # (CRUD)
        render_api_csv_step_dialog()
        return  # <--- 🛑 [สำคัญมาก] ต้องมี RETURN
        
    elif st.session_state.get('show_fill_form_dialog'): # (CRUD)
        render_fill_form_dialog()
        return  # <--- 🛑 [สำคัญมาก] ต้องมี RETURN
        
    elif st.session_state.get('show_verify_detail_dialog'): # (CRUD)
        render_verify_detail_dialog()
        return  # <--- 🛑 [สำคัญมาก] ต้องมี RETURN

    elif st.session_state.get('show_kw_factory_dialog'):  # (CRUD - Import from KW Factory)
        from modules.crud_generator.ui_crud import render_kw_factory_import_dialog
        render_kw_factory_import_dialog()
        return  # <--- 🛑 [สำคัญมาก] ต้องมี RETURN

    # --- Test Flow Dialog ---
    elif st.session_state.get('show_add_dialog'):
        render_add_step_dialog_base(
            dialog_state_key='show_add_dialog',
            context_state_key='add_dialog_timeline',
            selected_kw_state_key='selected_kw',
            add_step_callback=add_step_to_timeline,
            ws_state=ws_state,
            title=f"Add New Step to {st.session_state.get('add_dialog_section', 'Timeline')}",
            search_state_key="kw_search_dialog_testflow",
            recently_used_state_key="recently_used_keywords"
        )
        return  # <--- 🛑 [สำคัญมาก] ต้องมี RETURN

    # --- Keyword Factory Dialogs ---
    elif st.session_state.get('show_kw_factory_add_dialog'):
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
        )
        return  # <--- 🛑 [สำคัญมาก] ต้องมี RETURN
        
    elif st.session_state.get('show_kw_factory_fill_form_dialog'):
        render_kw_factory_fill_form_dialog()
        return  # <--- 🛑 [สำคัญมาก] ต้องมี RETURN
        
    elif st.session_state.get('show_kw_factory_verify_dialog'):
        render_kw_factory_verify_detail_dialog()
        return  # <--- 🛑 [สำคัญมาก] ต้องมี RETURN
        
    elif st.session_state.get('show_kw_factory_api_csv_dialog'):
        render_kw_factory_api_csv_step_dialog()
        return  # <--- 🛑 [สำคัญมาก] ต้องมี RETURN

    # --- Studio Dialog (จาก app.py) ---
    elif ws_state.get('show_csv_creator'):
        csv_creator_dialog() # (ฟังก์ชันนี้อยู่ใน app.py อยู่แล้ว)
        return  # <--- 🛑 [สำคัญมาก] ต้องมี RETURN

    # 4. ถ้าไม่มี Dialog ไหนเปิดอยู่ ให้วาดหน้าหลักตามปกติ
    render_sidebar()
    render_header()
    
    if not PARSER_AVAILABLE:
        st.error("HTML Parser module not available. Please check installation."); return

    render_studio_tab() # <-- เรียก Tab UI (ซึ่งตอนนี้ไม่มี Dialog แฝง)

if __name__ == "__main__":
    main()