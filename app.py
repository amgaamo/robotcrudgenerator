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

# Backend imports
from modules.session_manager import init_session_state, get_clean_locator_name 
from modules.file_manager import (
    scan_robot_project, create_new_robot_file, 
    parse_robot_keywords, read_robot_variables_from_content,
    append_robot_content_intelligently, append_to_api_base,
    parse_data_sources_from_resource
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
from modules.crud_generator.ui_crud import render_crud_generator_tab

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

def get_file_icon(file_name):
    """Return an emoji icon based on file extension."""
    if file_name.endswith('.robot'):
        return "📝"  # Robot icon
    elif file_name.endswith('.resource'):
        return "📝"  # Gear/Resource icon
    elif file_name.endswith('.py'):
        return "🐍"  # Python icon
    elif file_name.endswith('.txt'):
        return "📝"  # Text file icon
    else:
        return "📄"  # Generic file icon

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
            if st.button("📂 Set", use_container_width=True, key="sidebar_set"):
                if project_path:
                    st.session_state.project_path = project_path
                    st.session_state.project_structure = scan_robot_project(project_path)
                    st.rerun()

        with col2:
            if st.button("🔄 Clear", use_container_width=True, key="sidebar_clear"):
                st.session_state.project_path = ""
                st.session_state.project_structure = {}
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
                use_container_width=True,
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
        </p>
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
    if st.button("⊕ Add Step to Setup", use_container_width=True, key="add_step_setup"):
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
        if st.button(f"⊕ Add Step Here", use_container_width=True, key=f"add_step_after_{i}"):
            st.info("Command Palette for adding steps will be implemented next.")

    st.markdown("---")
    st.markdown("##### --- SUITE TEARDOWN ---")
    if st.button("⊕ Add Step to Teardown", use_container_width=True, key="add_step_teardown"):
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
                        if st.button("✅ Add Row", type="primary", use_container_width=True, key="add_row_btn"):
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
                        if st.button("🔄 Clear Form", use_container_width=True, key="clear_form_btn"):
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
                        use_container_width=True,
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
                    use_container_width=True, 
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
                    use_container_width=True, 
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
                        use_container_width=True, 
                        key="csv_data_editor_upload"
                    )
                    ws_state['csv_uploaded_data'] = edited_df
                    
                    st.caption(f"Current rows: {len(edited_df)}")

            st.markdown("---")
            
            # ปุ่ม Save สำหรับ Upload mode
            if st.button("💾 Save to datatest folder", type="primary", use_container_width=True, key="save_uploaded_csv"):
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
        ds_var = f"DS_{name_upper_no_space}"
        
        var_code = f"${{{var_name}}}            ${{CURDIR}}${{/}}datatest${{/}}{csv_file}"
        kw_code = (
            f"\n{kw_name}\n"
            f"    Import datasource file        ${{{var_name}}}\n"
            f"    Set Global Variable           ${{{col_var}}}                     ${{value_col}}\n"
            f"    Set Global Variable           ${{{ds_var}}}               ${{datasource_val}}"
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
                    relative_path = os.path.relpath(full_path, st.session_state.project_path)
                    # เปลี่ยนจาก st.success หรือ st.toast เป็นการตั้งค่า state
                    st.session_state.file_created_message = f"✅ Successfully created file: `{relative_path}`"
                    # --- สิ้นสุดการแก้ไข ---
                else:
                    st.error(message)
                # --- END: ส่วนที่แก้ไข ---
    export_dialog()

def render_test_data_tab():
    """Renders the UI for the Test Data tab with improved layout - FIXED VERSION."""
    st.markdown("#### 🗃️ Test Data Management", unsafe_allow_html=True)
    ws_state = st.session_state.studio_workspace

    # --- CSV Data Sources Section ---
    with st.expander("📊 CSV Data Sources", expanded=True):
        
        # --- Small create button at the top ---
        if st.button("➕ Create New CSV File", use_container_width=False, type="secondary"):
            ws_state['show_csv_creator'] = True
            st.rerun()
        
        st.markdown("---")
        
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
                            imported_sources = parse_data_sources_from_resource(content)

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
                                if st.button("💾 Export", key=f"export_{i}", use_container_width=True):
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
                        if st.button("🗑️", key=f"del_{i}", help="Delete this data source link", use_container_width=True, type="secondary"):
                            ws_state['data_sources'].pop(i)
                            st.rerun()
                    
                    st.markdown('</div>', unsafe_allow_html=True)

            st.markdown("---")
            if st.button("🔗 Add Data Source Link (Manual)", use_container_width=True, type="secondary"):
                ws_state.setdefault('data_sources', []).append({
                    'name': '', 'file_name': '', 'col_name': '', 'is_imported': False
                })
                st.rerun()

    # --- API Services Section (keep existing) ---
    with st.expander("🌐 API Services", expanded=False):
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
        if st.button("➕ Create New API Service", use_container_width=False, type="primary"):
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
            if st.button("🗑️ Clear All", use_container_width=True):
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
                if st.button("✏️ Edit", key=f"edit_api_{service['id']}", use_container_width=True):
                    ws_state['editing_api_service_id'] = service['id']
                    st.rerun()
            with cols[2]:
                if st.button("🗑️ Delete", key=f"delete_api_{service['id']}", use_container_width=True):
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

    # --- START: ปรับปรุง Expander "Request Options & Validation" ---
    with st.expander("⚙️ Request Options", expanded=True):
        st.markdown("**Header / Authentication**")
        
        # --- ตัวเลือก Header Type ---
        header_options = ['simple', 'bearer', 'custom']
        service_data['headers_type'] = st.selectbox(
            "Header Type",
            options=header_options,
            index=header_options.index(service_data.get('headers_type', 'simple')),
            key=f"editor_header_type_{service_id}"
        )

        # --- UI ตามเงื่อนไข ---
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
        
        # --- Additional Headers (อยู่ข้างนอก ใช้ได้กับทุก Type) ---
        service_data['custom_header_manual_pairs'] = st.text_area(
            "Additional Headers (key: value)",
            value=service_data.get('custom_header_manual_pairs', 'Content-Type: application/json'),
            key=f"editor_manual_headers_{service_id}",
            help="ใส่ Header เพิ่มเติม บรรทัดละ 1 คู่, คั่นด้วยเครื่องหมาย colon (:)"
        )
    # --- END: ปรับปรุง Expander ---

    # --- Expander 3: Request Body & Arguments ---
    with st.expander("📝 Request Body & Arguments"):
        st.text_area(
            "Paste JSON Body Sample",
            key=f"editor_req_body_{service_id}",
            value=service_data['req_body_sample'],
            height=200,
            on_change=lambda: service_data.update({'req_body_sample': st.session_state[f"editor_req_body_{service_id}"]})
        )

        if st.button("✨ Analyze Request & Generate Arguments", key=f"editor_analyze_{service_id}", use_container_width=True):
            # (Logic การ Analyze เดิม)
            try:
                service_data['analyzed_fields'] = {}
                if service_data['req_body_sample'].strip():
                    body_json = json.loads(service_data['req_body_sample'])
                    if isinstance(body_json, dict):
                        for key, value in body_json.items():
                            service_data['analyzed_fields'][key] = {"value": value, "is_argument": False, "arg_name": key}
                st.success("Analysis Complete!")
            except json.JSONDecodeError:
                st.error("Invalid JSON in Request Body.")
            except Exception as e:
                st.error(f"Analysis Error: {e}")

        if service_data.get('analyzed_fields'):
            st.markdown("**Fields to make Arguments:**")
            for key, arg_details in service_data['analyzed_fields'].items():
                cols = st.columns([1, 4, 3])
                with cols[0]:
                    arg_details['is_argument'] = st.checkbox(" ", value=arg_details.get('is_argument', False), key=f"editor_is_arg_{key}_{service_id}")
                with cols[1]:
                    st.code(f'"{key}": {json.dumps(arg_details["value"])}', language="json")
                with cols[2]:
                    arg_details['arg_name'] = st.text_input("Arg Name", value=arg_details.get('arg_name', key), key=f"editor_arg_name_{key}_{service_id}", label_visibility="collapsed", disabled=not arg_details['is_argument'])

    # --- Expander 4: Response Handling ---
                # --- START: โค้ดฉบับสมบูรณ์สำหรับ Expander "Response Handling & Variable Extraction" ---
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
                    
                    # --- ส่วนของ Text Area ที่หายไป ถูกเพิ่มกลับเข้ามาแล้ว ---
                    st.text_area(
                        "Paste JSON Response Sample",
                        key=f"editor_resp_body_{service_id}",
                        value=service_data['resp_body_sample'],
                        height=200,
                        on_change=lambda: service_data.update({'resp_body_sample': st.session_state[f"editor_resp_body_{service_id}"]})
                    )

                    if st.button("🔍 Analyze Response & Find Variables", key=f"editor_analyze_resp_{service_id}", use_container_width=True):
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
                # --- END: โค้ดฉบับสมบูรณ์ ---

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

def generate_main_keyword_code(service_data):
    """Generates the complete main keyword code for the specific service file."""
    kw_name = f"Request {service_data.get('service_name', 'Untitled').replace('_', ' ').title()}"
    
    # --- 1. Build Arguments ---
    args = ["${headeruser}", "${headerpassword}"]
    for field_data in service_data.get('analyzed_fields', {}).values():
        if field_data.get('is_argument'):
            args.append(f"${{{field_data['arg_name']}}}")
    args_str = "    ".join(args)

    # --- 2. Build Multi-line Catenate for Body ---
    body_code = ""
    try:
        body_dict = json.loads(service_data.get('req_body_sample', '{}'))
        replacements = []
        for key, field_data in service_data.get('analyzed_fields', {}).items():
            if field_data.get('is_argument'):
                placeholder = f"__PLACEHOLDER_{field_data['arg_name']}__"
                if key in body_dict:
                    body_dict[key] = placeholder
                    replacements.append((f'"{placeholder}"', f'${{{field_data["arg_name"]}}}'))
        pretty_json = json.dumps(body_dict, indent=4, ensure_ascii=False)
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
    except (json.JSONDecodeError, TypeError):
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

    # Step 3.1: Conditional Login for uid/ucode
    if header_type == 'custom' and service_data.get('custom_header_use_uid_ucode'):
        prep_lines.append("    api_base.Request Service for get session data    ${headeruser}    ${headerpassword}")
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
        validation_code.extend([f"    ${{status_val}}=    Set Variable    ${{GLOBAL_RESPONSE_JSON}}[{status_path}]",f"    IF    '${{status_val}}' == '{success_value}'"])
        for mapping in service_data.get('response_extractions', []):
            if mapping.get('is_enabled') and mapping.get('var_name'):
                robot_path = ''.join([f"[{p}]" for p in mapping['json_path'].replace(']', '').replace('[', '.').split('.')])
                validation_code.append(f"        Set Global Variable    ${{{mapping['var_name']}}}    ${{GLOBAL_RESPONSE_JSON}}{robot_path}")
        validation_code.extend(["    ELSE",f"        Fail    API call failed. Status: ${{status_val}}, Message: ${{GLOBAL_RESPONSE_JSON}}[{error_path}]","    END"])
    else:
        for mapping in service_data.get('response_extractions', []):
            if mapping.get('is_enabled') and mapping.get('var_name'):
                robot_path = ''.join([f"[{p}]" for p in mapping['json_path'].replace(']', '').replace('[', '.').split('.')])
                validation_code.append(f"    Set Global Variable    ${{{mapping['var_name']}}}    ${{GLOBAL_RESPONSE_JSON}}{robot_path}")

    # --- 5. Assemble the final keyword ---
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
    """ Renders the "Studio Workspace" using the new three-tab layout. """
    st.markdown("### 🤖 Studio Workspace")
    st.caption("A visual editor to build your complete Robot Framework test script.")

    if st.session_state.studio_workspace.get('show_csv_creator'):
        csv_creator_dialog()

    # --- 1. สร้าง 3 แท็บหลัก ---
    tab_assets, tab_data, tab_flow, tab_crud = st.tabs([
        "📚 Assets", 
        "🗃️ Test Data", 
        "📈 Test Flow",
        "✨ CRUD Generator"
    ])

    # --- 2. เนื้อหาของแท็บ Assets ---
    with tab_assets:
        render_resources_view_new()

    # --- 3. เนื้อหาของแท็บ Test Data ---
    with tab_data:
        render_test_data_tab()

    # --- 4. เนื้อหาของแท็บ Test Flow ---
    with tab_flow:
        render_test_flow_tab()

    with tab_crud:
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

def render_resources_view_new():
    """ 
    Renders the Resources view in a two-column layout with collapsible sections and bug fixes.
    """
    ws_state = st.session_state.studio_workspace
    
    if 'editing_html_index' not in ws_state:
        ws_state['editing_html_index'] = None

    # --- Re-establish the two-column layout ---
    panel_grid = st.columns([1, 1], gap="large")

    # --- LEFT PANEL: COMMON KEYWORDS ---
    with panel_grid[0]:
        st.markdown("#### <i class='fa-solid fa-cubes'></i> Common Keywords", unsafe_allow_html=True)
        
        with st.container(border=True):
            # 🎯 1. แสดงสถานะของไฟล์ที่กำลังใช้งานอยู่
            current_kw_file = ws_state.get('common_keyword_path', 'N/A')
            st.caption(f"Loaded from: **{current_kw_file}**")

            uploaded_keyword_file = st.file_uploader(
                "Upload new keywords file to override", type=['robot', 'resource'], 
                key="studio_keyword_uploader_final", label_visibility="collapsed"
            )
            
            if uploaded_keyword_file:
                # 🎯 2. ตรวจสอบว่าไฟล์ที่อัปโหลดเป็นไฟล์ใหม่จริงๆ (ป้องกันการ rerun ซ้ำ)
                if uploaded_keyword_file.name != ws_state.get('common_keyword_path'):
                    with st.spinner(f"Parsing {uploaded_keyword_file.name}..."):
                        try:
                            content = uploaded_keyword_file.getvalue().decode("utf-8")
                            # 🎯 3. เขียนทับ (Overwrite) keywords และชื่อไฟล์เดิม
                            ws_state['keywords'] = parse_robot_keywords(content)
                            ws_state['common_keyword_path'] = uploaded_keyword_file.name
                            st.success(f"Successfully replaced keywords with '{uploaded_keyword_file.name}'!")
                            # สั่ง rerun เพื่อให้ UI อัปเดตทั้งหมด
                            st.rerun() 
                        except Exception as e:
                            st.error(f"Failed to parse file: {e}")

            # ========== START: ส่วนที่แก้ไขใหม่ ==========
            if ws_state.get('keywords'):
                # --- ใช้ Module ใหม่สำหรับการจัดกลุ่ม Keywords (Task-Based Workflow) ---
                with st.expander("Show/Hide Loaded Keywords", expanded=True):
                    all_keywords = ws_state['keywords']
                    
                    # ========== START: เพิ่ม CSS เพื่อลดช่องว่างระหว่าง Expander ==========
                    st.markdown("""
                        <style>
                            [data-testid="stExpander"] {
                                margin-bottom: 1px !important; /* ลดช่องว่างด้านล่างของแต่ละ Expander */
                            }
                        </style>
                    """, unsafe_allow_html=True)
                    # ========== END: สิ้นสุดส่วนที่เพิ่ม ==========

                    # เรียกใช้ฟังก์ชันจาก module
                    categorized = categorize_keywords(all_keywords)
                    stats = get_category_stats(categorized)
                    expansion_config = get_expansion_config()
                    
                    # แสดงสถิติโดยรวม
                    col_stats1, col_stats2, col_stats3 = st.columns(3)
                    with col_stats1:
                        st.metric("📊 Total Keywords", stats['total_keywords'])
                    with col_stats2:
                        st.metric("📁 Categories", stats['total_categories'])
                    with col_stats3:
                        st.metric("🧩 Others", stats['uncategorized'])
                    
                    st.markdown("---")
                    
                    # 🎯 START: แก้ไขการเรียงลำดับและจัดคอลัมน์
                    
                    # 1. แก้ไขการเรียงลำดับให้ถูกต้องสมบูรณ์
                    categories_to_sort = [k for k in categorized.keys() if k != "🧩 Others"]
                    sorted_categories = sorted(categories_to_sort, key=get_category_priority)
                    if "🧩 Others" in categorized and categorized["🧩 Others"]:
                        sorted_categories.append("🧩 Others")

                    # 2. แบ่งรายการหมวดหมู่เพื่อแสดงผลเป็น 2 คอลัมน์
                    mid_point = (len(sorted_categories) + 1) // 2
                    left_col_categories = sorted_categories[:mid_point]
                    right_col_categories = sorted_categories[mid_point:]

                    col1, col2 = st.columns(2)

                    # --- แสดงผลคอลัมน์ซ้าย ---
                    with col1:
                        for category in left_col_categories:
                            kws = categorized.get(category, [])
                            if not kws:
                                continue
                            
                            is_expanded = expansion_config.get(category, False)
                            with st.expander(f"**{category}**", expanded=is_expanded):
                                for kw in sorted(kws, key=lambda x: x['name']):
                                    with st.expander(f"`{kw['name']}`"):
                                        if kw.get('doc'):
                                            st.info(f"**Doc:** {kw['doc']}")
                                        else:
                                            st.caption("_No documentation available_")
                                        
                                        if kw.get('args'):
                                            args_str = " ".join([f"`{arg['name']}`" for arg in kw.get('args', [])])
                                            st.markdown(f"**Args:** {args_str}")
                                        else:
                                            st.markdown("**Args:** _None_")

                    # --- แสดงผลคอลัมน์ขวา ---
                    with col2:
                        for category in right_col_categories:
                            kws = categorized.get(category, [])
                            if not kws:
                                continue
                            
                            is_expanded = expansion_config.get(category, False)
                            with st.expander(f"**{category}**", expanded=is_expanded):
                                for kw in sorted(kws, key=lambda x: x['name']):
                                    with st.expander(f"`{kw['name']}`"):
                                        if kw.get('doc'):
                                            st.info(f"**Doc:** {kw['doc']}")
                                        else:
                                            st.caption("_No documentation available_")
                                        
                                        if kw.get('args'):
                                            args_str = " ".join([f"`{arg['name']}`" for arg in kw.get('args', [])])
                                            st.markdown(f"**Args:** {args_str}")
                                        else:
                                            st.markdown("**Args:** _None_")

    # --- RIGHT PANEL: LOCATORS ---
    with panel_grid[1]:
        st.markdown("#### <i class='fa-solid fa-bullseye'></i> Locators", unsafe_allow_html=True)
        with st.container(border=True):
            with st.expander("📁 Load from .robot file"):
                uploaded_locator_file = st.file_uploader("Browse for a locator file", type=['robot', 'resource'], key="studio_locator_uploader_final_2")
                if uploaded_locator_file:
                    with st.spinner(f"Loading from {uploaded_locator_file.name}..."):
                        content = uploaded_locator_file.getvalue().decode("utf-8")
                        locators = read_robot_variables_from_content(content)
                        for loc in locators:
                            loc['page_name'] = uploaded_locator_file.name
                        ws_state['locators'].extend(locators)
                        st.success(f"Loaded {len(locators)} locators.")

            with st.expander("📄 Add from HTML", expanded=True):
                for i, page in enumerate(ws_state['html_pages']):
                    col1, col2, col3 = st.columns([0.6, 0.3, 0.1])
                    with col1:
                        page['name'] = st.text_input(f"Page Name {i+1}", value=page['name'], key=f"studio_html_page_name_{i}", label_visibility="collapsed", placeholder=f"Page Name {i+1}")
                    with col2:
                        if st.button(f"✏️ Edit HTML", key=f"studio_edit_html_{i}", use_container_width=True):
                            ws_state['editing_html_index'] = i
                            st.rerun()
                    with col3:
                         if len(ws_state['html_pages']) > 1:
                            if st.button(f"🗑️", key=f"studio_remove_html_page_{i}", help="Remove this page", use_container_width=True):
                                ws_state['html_pages'].pop(i)
                                st.rerun()

                if st.button("➕ Add another HTML page", use_container_width=True, type="secondary"):
                    ws_state['html_pages'].append({'name': f'Page {len(ws_state["html_pages"]) + 1}', 'html': ''})
                    st.rerun()
                
                st.markdown("---")
                if st.button("Find All Locators from HTML", use_container_width=True, type="primary"):
                    with st.spinner("Finding locators..."):
                        parser = HTMLLocatorParser()
                        new_locators_found = 0
                        for page in ws_state['html_pages']:
                            if page['html']:
                                fields = parser.parse_html(page['html'])
                                for field in fields:
                                    new_loc_name = f"LOCATOR_{field.variable}"
                                    if not any(loc['name'] == new_loc_name for loc in ws_state['locators']):
                                        ws_state['locators'].append({
                                            'id': str(uuid.uuid4()),
                                            'name': new_loc_name,
                                            'value': field.xpath,
                                            'page_name': page['name']
                                        })
                                        new_locators_found += 1
                        st.success(f"Found {new_locators_found} new locators.")
                        st.rerun()

    # --- HTML Editor Dialog ---
    if ws_state.get('editing_html_index') is not None:
        if ws_state['editing_html_index'] < len(ws_state['html_pages']):
            html_editor_dialog()

    # --- 3. LOCATOR STAGING AREA (Collapsible) ---
    if ws_state.get('locators'):
        for idx, loc in enumerate(ws_state['locators']):
            if 'id' not in loc or not loc['id']:
                ws_state['locators'][idx]['id'] = str(uuid.uuid4())
        with st.expander("#### 📝 Locator Staging Area", expanded=True):
            
            file_locators = [loc for loc in ws_state['locators'] if loc.get('page_name') not in [p['name'] for p in ws_state.get('html_pages', [])]]
            html_locators_with_indices = {i: loc for i, loc in enumerate(ws_state['locators']) if loc.get('page_name') in [p['name'] for p in ws_state.get('html_pages', [])]}

            st.markdown("<h6>🔒 From Files (Read-Only)</h6>", unsafe_allow_html=True)
            if file_locators:
                with st.expander(f"Loaded {len(file_locators)} locators from files", expanded=False):
                    # 🎯 START: แก้ไขโค้ดส่วนนี้ทั้งหมด
                    # 1. เพิ่ม CSS สำหรับจัดสไตล์ให้สวยงาม
                    st.markdown("""
                        <style>
                        .locator-grid-container {
                            display: grid;
                            grid-template-columns: repeat(4, 1fr);
                            gap: 8px;
                        }
                        .locator-pill {
                            background-color: rgba(88, 166, 255, 0.1);
                            border: 1px solid rgba(88, 166, 255, 0.2);
                            color: #cbd5e1;
                            padding: 5px 10px;
                            border-radius: 12px;
                            font-family: monospace;
                            font-size: 0.8rem;
                            white-space: nowrap;
                            overflow: hidden;
                            text-overflow: ellipsis;
                            text-align: left;
                        }
                        </style>
                    """, unsafe_allow_html=True)
                    
                    # 2. สร้าง HTML สำหรับ Grid Layout
                    html_grid = "<div class='locator-grid-container'>"
                    for loc in sorted(file_locators, key=lambda x: x['name']):
                        clean_name = get_clean_locator_name(loc['name'])
                        html_grid += f"<div class='locator-pill' title='{clean_name}'>{clean_name}</div>"
                    html_grid += "</div>"
                    
                    # 3. แสดงผล HTML ที่สร้างขึ้น
                    st.markdown(html_grid, unsafe_allow_html=True)

                    # 🎯 END: สิ้นสุดการแก้ไข
            else:
                with st.container(border=True):
                    st.caption("No locators loaded from files yet.")

            # --- "From HTML" Display (Table Layout with Expandable Pages) ---
            st.markdown("<h6>✏️ From HTML (Editable)</h6>", unsafe_allow_html=True)
            
            # 1. จัดกลุ่ม Locators ตาม page_name
            html_locators_by_page = {}
            for i, loc in enumerate(ws_state['locators']):
                if loc.get('page_name') in [p['name'] for p in ws_state.get('html_pages', [])]:
                    page_name = loc['page_name']
                    if page_name not in html_locators_by_page:
                        html_locators_by_page[page_name] = []
                    html_locators_by_page[page_name].append((i, loc))

            if not html_locators_by_page:
                with st.container(border=True):
                    st.caption("No locators added from HTML yet.")
            else:
                # --- CSS สำหรับ Table ---
                st.markdown("""
                    <style>
                    .locator-header {
                        display: grid;
                        grid-template-columns: 40% 50% 10%;
                        font-weight: 600;
                        padding: 8px 4px;
                        background-color: rgba(128, 128, 128, 0.15);
                        border-radius: 4px;
                        margin-bottom: 8px;
                        font-size: 0.9rem;
                    }
                    .locator-header div {
                        padding: 0 4px;
                    }
                    </style>
                """, unsafe_allow_html=True)
                
                # 2. วนลูปแสดงแต่ละ Page ใน Expander แยก
                for page_name, locators_in_page in html_locators_by_page.items():
                    with st.expander(f"📄 **{page_name}** ({len(locators_in_page)} items)", expanded=True):
                        
                        # 3. แบ่ง Locators ในแต่ละ Page ออกเป็น 2 ฝั่ง (ซ้าย-ขวา)
                        mid_point = (len(locators_in_page) + 1) // 2
                        left_locators = locators_in_page[:mid_point]
                        right_locators = locators_in_page[mid_point:]
                        
                        # 4. สร้าง Layout ซ้าย-ขวา
                        left_panel, right_panel = st.columns([1, 1], gap="medium")
                        
                        # --- LEFT PANEL ---
                        with left_panel:
                            with st.container(border=True):
                                st.markdown("""
                                    <div class="locator-header">
                                        <div>Name</div>
                                        <div>Value</div>
                                        <div style="text-align: center;">Del</div>
                                    </div>
                                """, unsafe_allow_html=True)
                                
                                for original_index, locator_data in left_locators:
                                    # ใช้ id เป็น unique key
                                    loc_id = locator_data.get('id')
                                    if not loc_id:
                                        # ถ้าไม่มี id (กรณีที่ไม่ควรเกิด) ให้สร้างใหม่
                                        loc_id = str(uuid.uuid4())
                                        locator_data['id'] = loc_id
                                        ws_state['locators'][original_index]['id'] = loc_id   
                                                                         
                                    col_name, col_value, col_action = st.columns([40, 50, 10])
                                    
                                    with col_name:
                                        new_name = st.text_input(
                                            "Name", 
                                            value=locator_data['name'], 
                                            key=f"loc_name_L_{page_name}_{loc_id}",
                                            label_visibility="collapsed",
                                            placeholder="Name"
                                        )
                                    
                                    with col_value:
                                        new_value = st.text_input(
                                            "Value", 
                                            value=locator_data['value'], 
                                            key=f"loc_value_L_{page_name}_{loc_id}",
                                            label_visibility="collapsed",
                                            placeholder="XPath"
                                        )
                                    
                                    with col_action:
                                        if st.button("🗑️", key=f"loc_del_L_{page_name}_{loc_id}", help="Delete", use_container_width=True):
                                            # ลบโดยใช้ id เท่านั้น
                                            ws_state['locators'] = [
                                                loc for loc in ws_state['locators'] 
                                                if loc.get('id') != loc_id
                                            ]
                                            st.rerun()
                                    
                                    # อัปเดตค่าถ้ามีการเปลี่ยนแปลง
                                    if new_name != locator_data['name'] or new_value != locator_data['value']:
                                        # ใช้ id ในการค้นหาและอัปเดต
                                        for idx, loc in enumerate(ws_state['locators']):
                                            if loc.get('id') == loc_id:
                                                ws_state['locators'][idx]['name'] = new_name
                                                ws_state['locators'][idx]['value'] = new_value
                                                break
                        
                        # --- RIGHT PANEL ---
                        with right_panel:
                            with st.container(border=True):
                                st.markdown("""
                                    <div class="locator-header">
                                        <div>Name</div>
                                        <div>Value</div>
                                        <div style="text-align: center;">Del</div>
                                    </div>
                                """, unsafe_allow_html=True)
                                
                                if right_locators:
                                    for original_index, locator_data in right_locators:
                                        loc_id = locator_data.get('id')  # ✅ เอา default ออก
                                        if not loc_id:
                                            # ถ้าไม่มี id (กรณีที่ไม่ควรเกิด) ให้สร้างใหม่
                                            loc_id = str(uuid.uuid4())
                                            locator_data['id'] = loc_id
                                            ws_state['locators'][original_index]['id'] = loc_id
                                        
                                        col_name, col_value, col_action = st.columns([40, 50, 10])
                                        
                                        with col_name:
                                            new_name = st.text_input(
                                                "Name", 
                                                value=locator_data['name'], 
                                                key=f"loc_name_R_{page_name}_{loc_id}",
                                                label_visibility="collapsed",
                                                placeholder="Name"
                                            )
                                        
                                        with col_value:
                                            new_value = st.text_input(
                                                "Value", 
                                                value=locator_data['value'], 
                                                key=f"loc_value_R_{page_name}_{loc_id}",
                                                label_visibility="collapsed",
                                                placeholder="XPath"
                                            )
                                        
                                        with col_action:
                                            if st.button("🗑️", key=f"loc_del_R_{page_name}_{loc_id}", help="Delete", use_container_width=True):
                                                # ลบโดยใช้ id เท่านั้น
                                                ws_state['locators'] = [
                                                    loc for loc in ws_state['locators'] 
                                                    if loc.get('id') != loc_id
                                                ]
                                                st.rerun()
                                        # อัปเดตค่าถ้ามีการเปลี่ยนแปลง
                                        if new_name != locator_data['name'] or new_value != locator_data['value']:
                                            for idx, loc in enumerate(ws_state['locators']):
                                                if loc.get('id') == loc_id:
                                                    ws_state['locators'][idx]['name'] = new_name
                                                    ws_state['locators'][idx]['value'] = new_value
                                                    break
                                else:
                                    st.caption("(Empty)")

            # 4. Export Options (เหมือนเดิม)
            # --- START: ส่วนที่แก้ไขใหม่ทั้งหมด ---
            st.markdown("---")
            st.subheader("💾 Export Options")
            st.caption("Exports only new locators generated from HTML.")
            
            # สร้าง State เพื่อจำตัวเลือกของผู้ใช้
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

            # --- Logic การดึงและจัดรูปแบบ Locator (ทำครั้งเดียว) ---
            html_locators = [
                loc for loc in ws_state['locators'] 
                if loc.get('page_name') in [p['name'] for p in ws_state.get('html_pages', [])]
            ]
            
            locators_string = ""
            if html_locators:
                max_len = max(len(f"${{{loc['name']}}}") for loc in html_locators) + 4
                locators_string = "\n".join([
                    f"{f'${{{loc['name']}}}'.ljust(max_len)}{loc['value']}"
                    for loc in sorted(html_locators, key=lambda x: x['name'])
                ])

            if save_option == "Append to Existing File":
                # --- UI สำหรับ APPEND ---
                all_robot_files = st.session_state.project_structure.get('robot_files', [])
                target_folder = "pageobjects"
                
                pageobject_files = [
                    f for f in all_robot_files 
                    if f.replace(os.sep, '/').startswith(target_folder + '/')
                ]
                
                if not pageobject_files:
                    st.warning("No files found in the `pageobjects` folder.")
                else:
                    file_options = [f.replace(os.sep, '/') for f in pageobject_files]
                    selected_file = st.selectbox(
                        "Select a pageobjects file to append to:",
                        options=sorted(file_options),
                        key="locator_append_target"
                    )
                    
                    if st.button("➕ Append Locators", key="append_locators_btn"):
                        if not html_locators:
                            st.warning("No new locators from HTML to save.")
                        else:
                            full_path = os.path.join(st.session_state.project_path, selected_file)
                            success, message = append_robot_content_intelligently(
                                full_path, 
                                variables_code=locators_string
                            )
                            if success:
                                st.success(message)
                            else:
                                st.error(message)

            elif save_option == "Create New File":
                # --- UI สำหรับ CREATE NEW ---
                st.caption("File will be saved in the `pageobjects` folder.")
                new_file_name = st.text_input(
                    "New file name:",
                    value="new_locators.robot",
                    key="locator_new_filename"
                )
                
                if st.button("📝 Create and Save File", key="create_locators_btn"):
                    if not html_locators:
                        st.warning("No new locators from HTML to save.")
                    elif not new_file_name.endswith(('.robot', '.resource')):
                        st.error("File name must end with .robot or .resource")
                    else:
                    # สร้างเนื้อหาพร้อม block marker
                        full_content = textwrap.dedent(f"""
*** Settings ***
Resource            ../resources/commonkeywords.resource

*** Variables ***

# --- START: Generated by Robot Framework Code Generator ---

{locators_string}

# ---  END: Generated by Robot Framework Code Generator  ---
""")
                        save_dir = os.path.join(st.session_state.project_path, "pageobjects")
                        os.makedirs(save_dir, exist_ok=True)
                        full_path = os.path.join(save_dir, new_file_name)
                        
                        success = create_new_robot_file(full_path, full_content)
                        if success:
                            # เก็บข้อความและ path ไว้ใน session_state
                            st.session_state['show_file_created_success'] = {
                                'path': os.path.relpath(full_path, st.session_state.project_path)
                            }
                            # สแกนโปรเจกต์ใหม่
                            st.session_state.project_structure = scan_robot_project(st.session_state.project_path)
                            st.rerun()
                        else:
                            st.error("Failed to create the file.")
           
    # แสดงข้อความ success หลัง rerun (วางไว้นอก if button)
        if 'show_file_created_success' in st.session_state and st.session_state.show_file_created_success:
            success_data = st.session_state.show_file_created_success
            st.success(f"✅ Successfully created file at `{success_data['path']}`")
            # เคลียร์ข้อความหลังแสดงแล้ว
            del st.session_state['show_file_created_success']        

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point"""
    init_session_state()
    render_sidebar()
    render_header()
    
    if not PARSER_AVAILABLE:
        st.error("HTML Parser module not available. Please check installation."); return

    # --- ลบ st.tabs ออก และเรียกใช้ render_studio_tab() โดยตรง ---
    render_studio_tab()

if __name__ == "__main__":
    main()

