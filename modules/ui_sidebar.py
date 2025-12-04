import streamlit as st
import streamlit.components.v1 as components
import os
from .file_manager import scan_robot_project
from .utils import get_file_icon
from .ui_components import copy_button_component

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
                # ใช้ components.html เพื่อ render ปุ่ม copy (ความสูง 40px เพื่อความพอดี)
                components.html(
                    copy_button_component(st.session_state.project_path, "copy_root_btn"),
                    height=40,
                    scrolling=False
                )

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
            
            # CSS เฉพาะสำหรับปุ่ม Folder ใน Sidebar (เพื่อความสวยงาม)
            st.markdown("""
            <style>
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
                    height: auto !important;
                    min-height: auto !important;
                    justify-content: flex-start !important;
                }
                [data-testid="stSidebar"] button[kind="secondary"][key*="folder_btn_"]:hover {
                    border-color: rgba(129, 140, 248, 0.5) !important;
                    box-shadow: 0 4px 16px rgba(99, 102, 241, 0.25) !important;
                    transform: translateX(2px) !important;
                    background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(51, 65, 85, 0.4) 100%) !important;
                    filter: none !important;
                }
            </style>
            """, unsafe_allow_html=True)
        
        with col_copy:
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
                    components.html(
                        copy_button_component(full_file_path, f"copy_file_{safe_key}_btn"), 
                        height=40,
                        scrolling=False
                    )
        
        if indent_level == 0:
            st.markdown("<div style='margin-bottom: 12px;'></div>", unsafe_allow_html=True)