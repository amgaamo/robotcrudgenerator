"""
Session State Management Module
Handles all session state initialization and helper functions
"""

import streamlit as st
import os
from .file_manager import scan_robot_project, read_robot_variables_from_content
from pathlib import Path
from .utils import parse_robot_keywords

def _load_default_keywords():
    """Loads and parses the default commonkeywords.resource file."""
    
    # Define menu locators to exclude from the main list
    MENU_LOCATOR_NAMES = ['homemenu', 'mainmenu', 'submenu', 'menuname']
    
    # Define block markers
    START_MARKER = "### All Menu Locator ###"
    END_MARKER = "### All Menu Locator (END) ###"

    try:
        default_file_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'commonkeywords')
        
        with open(default_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        keywords = parse_robot_keywords(content)
        all_variables = read_robot_variables_from_content(content)
        
        # แยก menu locators และ common variables
        menu_locators = {}
        common_variables = []
        
        for v in all_variables:
            var_name = v.get('name')
            if var_name in MENU_LOCATOR_NAMES:
                menu_locators[var_name] = v
            else:
                common_variables.append(v)
                
        return keywords, common_variables, menu_locators, "Default Keywords"

    except FileNotFoundError:
        st.warning("Default keywords file not found. Please upload one manually.")
        return [], [], {}, None
    except Exception as e:
        st.error(f"Error loading default keywords: {e}")
        return [], [], {}, None

def init_session_state():
    """Initialize all session state variables"""
    
# --- 🎯 START: Logic หา Default Path และ Auto-Scan (Revised) ---
    default_project_dir_path = ""
    try:
        # 1. หา Path ไปยังโฟลเดอร์ assets
        assets_dir = Path(__file__).parent.parent / "assets"

        # 2. ตรวจสอบว่า assets มีอยู่จริง
        if assets_dir.is_dir():
            # 3. ค้นหา Subdirectories
            subdirectories = [item for item in assets_dir.iterdir() if item.is_dir()]

            # 4. ตรวจสอบว่ามี Subdirectory เพียงอันเดียวหรือไม่
            if len(subdirectories) == 1:
                single_subdir = subdirectories[0]
                default_project_dir_path = str(single_subdir.resolve())
                print(f"✅ Found single default project directory: {default_project_dir_path}")
            # ... (Optional: add print statements for 0 or multiple subdirs if needed) ...

    except Exception as e:
        print(f"Error finding default project directory: {e}")

    # --- Initialize project_path and project_structure ---
    # Initialize project_structure first if it doesn't exist
    if 'project_structure' not in st.session_state:
        st.session_state.project_structure = {}

    # Set project_path only if it doesn't exist yet
    if 'project_path' not in st.session_state:
        st.session_state.project_path = default_project_dir_path

        # --- ✨ Auto-scan ONLY if default path is valid AND structure is currently empty ---
        if default_project_dir_path and not st.session_state.project_structure:
            print(f"🚀 Auto-scanning default project path: {default_project_dir_path}")
            try:
                # scan_robot_project is now imported
                st.session_state.project_structure = scan_robot_project(default_project_dir_path)
                print("✅ Auto-scan complete.")
            except Exception as scan_error:
                print(f"❌ Error during auto-scan: {scan_error}")
                st.session_state.project_structure = {} # Reset on error
    # --- 🎯 END: สิ้นสุด Logic หา Default Path และ Auto-Scan ---
    
    if 'expanded_folders' not in st.session_state:
        st.session_state.expanded_folders = {}

    # ===== START: เพิ่มส่วนนี้สำหรับ CRUD Generator =====
    if 'crud_generator_workspace' not in st.session_state:
        st.session_state.crud_generator_workspace = {
            'active_action': 'Create', # Action ที่กำลังทำงาน (Create, Update, Delete)
            'test_case_name': 'TC_Create_New_Item',
            'tags': ['Create', 'Smoke'],
            'steps': {
                'setup': [],
                'action': [],
                'verification': [],
                'teardown': []
            },
            'keyword_factory_keywords': []
        }
    # ===== END: สิ้นสุดส่วนที่เพิ่ม =====

    # Code Generator Tab State
    if 'studio_workspace' not in st.session_state:
        st.session_state.studio_workspace = {
            'view': 'Resources',  # หน้าจอเริ่มต้นที่จะแสดง 'Resources' หรือ 'Timeline'
            'keywords': [],      # สำหรับเก็บ Keywords ที่ import เข้ามา
            'common_variables': [],
            'menu_locators': {},  # เพิ่มบรรทัดนี้
            'common_keyword_path': None,
            'locators': [],      # สำหรับเก็บ Locators ทั้งหมด
            'html_pages': [{'name': 'Page 1', 'html': ''}],
            'timeline': [],      # สำหรับเก็บ Steps ทั้งหมดใน Timeline
            'data_sources': [],
            'show_csv_creator': False,         # ตัวแปรสำหรับเปิด/ปิด Pop-up
            'csv_creator_mode': 'New File',  # ตัวแปรสำหรับเก็บโหมด (สร้างใหม่/อัปโหลด)      
            'csv_new_filename': '',
            'csv_new_columns': '',
            'csv_new_data': None,      # ใช้เก็บ DataFrame สำหรับทั้งสองโหมด
            'csv_uploaded_file': None, # สำหรับเก็บ object ของไฟล์ที่อัปโหลด
            'csv_save_as_name': '',   # สำหรับเก็บชื่อไฟล์ที่จะบันทึก (โหมดอัปโหลด)
            'api_services': [],
            'api_keywords': [],

            # Test Flow Tab
            # Each step is a dict: {'id': '...', 'keyword': '...', 'args': {...}}
            'suite_setup': [],
            'timeline': [],
            'suite_teardown': [],

            # UI Control Flags
            'show_csv_creator': False,
            'editing_html_index': None,
            'editing_api_service_id': None,

            'common_keyword_path': None,    # เพิ่ม state นี้เพื่อเก็บชื่อไฟล์
        }

        # 🎯 3. เรียกใช้ฟังก์ชันโหลดไฟล์ดีฟอลต์
        # ทำให้เมื่อเปิดแอปครั้งแรก จะมี keywords พร้อมใช้งานทันที
        keywords, common_vars, menu_locators, path_name = _load_default_keywords()
        st.session_state.studio_workspace['keywords'] = keywords
        st.session_state.studio_workspace['common_variables'] = common_vars
        st.session_state.studio_workspace['menu_locators'] = menu_locators
        st.session_state.studio_workspace['common_keyword_path'] = path_name

        # ===== START: ADDED FOR KEYWORD FACTORY =====
        if 'keyword_factory_workspace' not in st.session_state:
            st.session_state.keyword_factory_workspace = {
                'active_keyword_id': None,
                'keywords': [] 
            }
        # ===== END: ADDED FOR KEYWORD FACTORY =====

# 🎯 START: เพิ่มฟังก์ชันใหม่นี้เข้าไปทั้งหมด
def get_clean_locator_name(raw_name):
    """Removes Robot Framework variable syntax ${...} for cleaner display."""
    if isinstance(raw_name, str) and raw_name.startswith('${') and raw_name.endswith('}'):
        return raw_name[2:-1]
    return raw_name
# 🎯 END: สิ้นสุดโค้ดของฟังก์ชันใหม่