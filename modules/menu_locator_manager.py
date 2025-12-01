"""
Menu Locator Manager Module
จัดการ Menu Locators: homemenu, mainmenu, submenu, menuname
"""

import streamlit as st
import uuid
from typing import Dict, Any


def render_menu_locator_manager():
    """แสดง UI สำหรับจัดการ Menu Locators"""
    
    # ดึงข้อมูลจาก session state
    menu_locators = st.session_state.studio_workspace.get('menu_locators', {})
    
    # ถ้ายังไม่มีข้อมูล แสดงว่ายังไม่ได้โหลด
    if not menu_locators:
        st.info("No menu locators loaded. Please load a commonkeywords file first.")
        return
    
    # แสดงข้อมูลไฟล์ที่โหลด
    current_file = st.session_state.studio_workspace.get('common_keyword_path', 'Unknown')
    st.caption(f"📁 Source: **{current_file}**")
    
    # แสดงแต่ละประเภทเมนูในรูปแบบ sub-expander
    menu_types = [
        ('homemenu', '🏠 Home Menu', 'scalar'),
        ('mainmenu', '📋 Main Menu', 'dict'),
        ('submenu', '📂 Sub Menu', 'dict'),
        ('menuname', '🏷️ Menu Names', 'dict')
    ]
    
    for menu_key, menu_label, menu_type in menu_types:
        render_menu_section(menu_key, menu_label, menu_type, menu_locators)
    
    # ปุ่ม Save Changes
    st.divider()
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("💾 Save to File", type="primary", use_container_width=True, key="save_menu_locators_btn"):
            save_menu_locators_to_file()

def render_menu_section(menu_key: str, menu_label: str, menu_type: str, menu_locators: Dict):
    """แสดง section ของแต่ละประเภทเมนู"""
    
    menu_data = menu_locators.get(menu_key, {})
    
    # นับจำนวน items
    item_count = 0
    if menu_type == 'scalar':
        item_count = 1 if menu_data.get('value') else 0
    else:
        item_count = len(menu_data.get('value', {})) if menu_data else 0
    
    with st.expander(f"{menu_label} ({item_count} items)", expanded=False):
        if menu_type == 'scalar':
            render_scalar_menu(menu_key, menu_data)
        else:
            render_dict_menu(menu_key, menu_data)


def render_scalar_menu(menu_key: str, menu_data: Dict):
    """แสดง UI สำหรับ scalar menu (homemenu)"""
    
    current_value = menu_data.get('value', '') if menu_data else ''
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        new_value = st.text_input(
            "Locator Value",
            value=current_value,
            key=f"edit_{menu_key}_value",
            placeholder="e.g., //*[@id='home']"
        )
    
    with col2:
        st.write("")  # spacing
        st.write("")  # spacing
        if st.button("Update", key=f"btn_update_{menu_key}", use_container_width=True):
            if new_value.strip():
                st.session_state.studio_workspace['menu_locators'][menu_key] = {
                    'name': menu_key,
                    'value': new_value.strip(),
                    'type': 'scalar'
                }
                st.success(f"Updated {menu_key}")
                st.rerun()


def render_dict_menu(menu_key: str, menu_data: Dict):
    """แสดง UI สำหรับ dict menu (mainmenu, submenu, menuname)"""
    
    items = menu_data.get('value', {}) if menu_data else {}
    
    # แสดงรายการปัจจุบันเป็นการ์ด
    if items:
        # จำกัดความสูงด้วย container
        with st.container(height=300):
            for key, value in items.items():
                render_menu_item_card(menu_key, key, value)
    else:
        st.info(f"No items in {menu_key}. Add your first item below.")
    
    st.divider()
    
    # ฟอร์มเพิ่มรายการใหม่
    with st.form(key=f"form_add_{menu_key}"):
        st.write("**Add New Item**")
        col1, col2, col3 = st.columns([2, 3, 1])
        
        with col1:
            new_key = st.text_input("Key", key=f"new_key_{menu_key}", placeholder="e.g., userMgt")
        
        with col2:
            new_value = st.text_input("Value", key=f"new_value_{menu_key}", 
                                     placeholder="e.g., //a[@title='User Management']")
        
        with col3:
            st.write("")
            st.write("")
            submitted = st.form_submit_button("➕ Add", use_container_width=True)
        
        if submitted:
            if new_key.strip() and new_value.strip():
                add_menu_item(menu_key, new_key.strip(), new_value.strip())
                st.success(f"Added {new_key} to {menu_key}")
                st.rerun()
            else:
                st.error("Both key and value are required")


def render_menu_item_card(menu_key: str, item_key: str, item_value: str):
    """แสดงการ์ดของแต่ละรายการพร้อมปุ่ม Edit/Delete"""
    
    # ตรวจสอบว่ากำลัง edit อยู่หรือไม่
    edit_state_key = f"editing_{menu_key}_{item_key}"
    is_editing = st.session_state.get(edit_state_key, False)
    
    if is_editing:
        # โหมดแก้ไข
        col1, col2, col3, col4 = st.columns([2, 3, 1, 1])
        
        with col1:
            new_key = st.text_input("Key", value=item_key, key=f"edit_key_{menu_key}_{item_key}", label_visibility="collapsed")
        
        with col2:
            new_value = st.text_input("Value", value=item_value, key=f"edit_value_{menu_key}_{item_key}", label_visibility="collapsed")
        
        with col3:
            if st.button("✅", key=f"save_{menu_key}_{item_key}", help="Save", use_container_width=True):
                update_menu_item(menu_key, item_key, new_key.strip(), new_value.strip())
                st.session_state[edit_state_key] = False
                st.rerun()
        
        with col4:
            if st.button("❌", key=f"cancel_{menu_key}_{item_key}", help="Cancel", use_container_width=True):
                st.session_state[edit_state_key] = False
                st.rerun()
    
    else:
        # โหมดแสดงผล
        col1, col2, col3, col4 = st.columns([2, 3, 1, 1])
        
        with col1:
            st.markdown(f"**`{item_key}`**")
        
        with col2:
            # จำกัดความยาวการแสดงผล
            display_value = item_value if len(item_value) <= 50 else item_value[:47] + "..."
            st.text(display_value)
        
        with col3:
            if st.button("✏️", key=f"edit_{menu_key}_{item_key}", help="Edit", use_container_width=True):
                st.session_state[edit_state_key] = True
                st.rerun()
        
        with col4:
            if st.button("🗑️", key=f"delete_{menu_key}_{item_key}", help="Delete", use_container_width=True):
                delete_menu_item(menu_key, item_key)
                st.rerun()


def add_menu_item(menu_key: str, item_key: str, item_value: str):
    """เพิ่มรายการใหม่ใน menu dict"""
    
    if menu_key not in st.session_state.studio_workspace['menu_locators']:
        st.session_state.studio_workspace['menu_locators'][menu_key] = {
            'name': menu_key,
            'value': {},
            'type': 'dict'
        }
    
    menu_data = st.session_state.studio_workspace['menu_locators'][menu_key]
    
    if 'value' not in menu_data or not isinstance(menu_data['value'], dict):
        menu_data['value'] = {}
    
    menu_data['value'][item_key] = item_value


def update_menu_item(menu_key: str, old_key: str, new_key: str, new_value: str):
    """อัปเดตรายการใน menu dict"""
    
    menu_data = st.session_state.studio_workspace['menu_locators'][menu_key]
    items = menu_data.get('value', {})
    
    # ลบ key เดิม
    if old_key in items:
        del items[old_key]
    
    # เพิ่ม key ใหม่
    items[new_key] = new_value
    
    menu_data['value'] = items


def delete_menu_item(menu_key: str, item_key: str):
    """ลบรายการจาก menu dict"""
    
    menu_data = st.session_state.studio_workspace['menu_locators'][menu_key]
    items = menu_data.get('value', {})
    
    if item_key in items:
        del items[item_key]
        menu_data['value'] = items
        st.toast(f"Deleted {item_key} from {menu_key}", icon="🗑️")


def save_menu_locators_to_file():
    """
    บันทึก menu locators กลับไปยังไฟล์
    (FIXED: บันทึกทั้งไฟล์ default และไฟล์ใน project path)
    """
    
    from modules.file_manager import update_menu_locators_in_file
    import os
    
    # 1. ดึงข้อมูล locators จาก session state
    menu_locators = st.session_state.studio_workspace.get('menu_locators', {})
    if not menu_locators:
        st.error("No menu locators data to save.")
        return

    # --- Flag ติดตามความสำเร็จ ---
    saved_all_files = True
    
    try:
        # --- 2. บันทึกไปยังไฟล์ Default (Master) ---
        default_file_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'commonkeywords')
        
        if not os.path.exists(default_file_path):
            st.warning(f"Default file not found at: {default_file_path}. Skipping.")
            saved_all_files = False
        else:
            success_default = update_menu_locators_in_file(default_file_path, menu_locators)
            if success_default:
                st.toast("✅ Saved to Default: assets/commonkeywords", icon="💾")
            else:
                st.error(f"❌ Failed to save to Default: {default_file_path}")
                saved_all_files = False

        # --- 3. บันทึกไปยังไฟล์ Project (ที่กำลัง Active) ---
        
        # ดึง project_path จาก st.session_state (ซึ่งถูกตั้งค่าใน session_manager.py)
        project_path = st.session_state.get('project_path') 
        
        if not project_path:
            st.info("No active project path found. Skipping save to project file.")
            # ไม่ถือว่าเป็น Error ถ้าไม่มีโปรเจกต์
        else:
            # สร้าง path ไปยัง commonkeywords.resource ภายในโปรเจกต์
            project_common_keyword_path = os.path.join(project_path, 'resources', 'commonkeywords.resource')
            
            if not os.path.exists(project_common_keyword_path):
                st.warning(f"Project file not found at: {project_common_keyword_path}. Skipping.")
                # หากไฟล์ในโปรเจกต์ไม่มีจริง ก็ไม่ควรถือว่า Error
            else:
                success_project = update_menu_locators_in_file(project_common_keyword_path, menu_locators)
                
                if success_project:
                    project_name = os.path.basename(project_path)
                    st.toast(f"✅ Saved to Project: {project_name}/resources/commonkeywords.resource", icon="📁")
                else:
                    st.error(f"❌ Failed to save to Project: {project_common_keyword_path}")
                    saved_all_files = False

        # --- 4. สรุปผล ---
        if saved_all_files:
            st.success("✅ Menu locators saved successfully to all targets!")
        else:
            st.error("❌ Failed to save to one or more targets. Check messages above.")
            
    except Exception as e:
        st.error(f"An error occurred during save: {e}")