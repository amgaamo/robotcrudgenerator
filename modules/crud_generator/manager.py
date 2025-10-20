# file: modules/crud_generator/manager.py
# (REVISED to support 'Verify Result of data table' script generation)

import streamlit as st
import uuid
from ..session_manager import get_clean_locator_name
import os
import csv
import pandas as pd

# ===================================================================
# ===== 1. LOGIC สำหรับจัดการ WORKSPACE STATE =====
# ===================================================================

def _create_default_steps_structure():
    return {
        'suite_setup': [], 'test_setup': [], 'action_list': [], 'action_detail': [],
        'verify_list': [], 'verify_detail': [], 'test_teardown': [], 'suite_teardown': []
    }

def initialize_workspace():
    ws = st.session_state.get('crud_generator_workspace', {})
    if 'steps' not in ws or not isinstance(ws['steps'], dict):
        ws['steps'] = _create_default_steps_structure()
    for key in _create_default_steps_structure().keys():
        if key not in ws['steps']:
            ws['steps'][key] = []
    st.session_state.crud_generator_workspace = ws

def _get_workspace():
    # ตรวจสอบเผื่อยังไม่ได้ init
    if 'crud_generator_workspace' not in st.session_state:
        initialize_workspace()
    return st.session_state.crud_generator_workspace

def _save_workspace():
    st.session_state.crud_generator_workspace = st.session_state.crud_generator_workspace

def _get_assets():
    # ตรวจสอบเผื่อ studio_workspace ไม่มี
    if 'studio_workspace' not in st.session_state:
        st.session_state.studio_workspace = {}
    return st.session_state.studio_workspace.get('keywords', []), st.session_state.studio_workspace.get('locators', [])


def get_csv_headers(csv_filename):
    """
    Reads the headers (first row) from a CSV file in the datatest folder.
    
    Args:
        csv_filename (str): Name of the CSV file (e.g., 'login_data.csv')
    
    Returns:
        list: List of column headers, or empty list if file not found/error
    """
    import os
    import csv
    
    # Get project path from session state
    if 'project_path' not in st.session_state or not st.session_state.project_path:
        return []
    
    project_path = st.session_state.project_path
    
    # Construct full path to CSV file
    csv_path = os.path.join(
        project_path,
        'resources',
        'datatest',
        csv_filename
    )
    
    # Check if file exists
    if not os.path.exists(csv_path):
        return []
    
    try:
        # Read first row (headers)
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader, [])  # Get first row
            # Strip whitespace from headers
            headers = [h.strip() for h in headers]
            return headers
    except Exception as e:
        # Log error if needed
        print(f"Error reading CSV headers from {csv_filename}: {e}")
        return []

def _find_step_index(steps_list, step_id):
    return next((i for i, step in enumerate(steps_list) if step.get('id') == step_id), -1)

# ===================================================================
# ===== 2. ฟังก์ชันจัดการ STEPS (CRUD) =====
# ===================================================================

def add_step(section_key, new_step_data):
    if 'id' not in new_step_data: new_step_data['id'] = str(uuid.uuid4())
    _get_workspace()['steps'][section_key].append(new_step_data)
    _save_workspace()

def add_fill_form_step(section_key):
    ws = _get_workspace()
    new_step = {
        "id": str(uuid.uuid4()), "keyword": "Fill in data form",
        "args": {
            "locator_field": "", "value": "", "select_attribute": "label",
            "is_checkbox_type": False, "is_ant_design": False,
            "is_switch_type": False, "locator_switch_checked": ""
        }
    }
    ws['steps'][section_key].insert(0, new_step)
    _save_workspace()

def delete_step(section_key, step_id):
    steps_list = _get_workspace()['steps'][section_key]
    index = _find_step_index(steps_list, step_id)
    if index != -1:
        steps_list.pop(index)
        _save_workspace()

def move_step(section_key, step_id, direction):
    steps_list = _get_workspace()['steps'][section_key]
    index = _find_step_index(steps_list, step_id)
    if index != -1:
        if direction == 'up' and index > 0:
            steps_list.insert(index - 1, steps_list.pop(index))
        elif direction == 'down' and index < len(steps_list) - 1:
            steps_list.insert(index + 1, steps_list.pop(index))
        _save_workspace()

def duplicate_step(section_key, step_id):
    steps_list = _get_workspace()['steps'][section_key]
    index = _find_step_index(steps_list, step_id)
    if index != -1:
        # ใช้ deepcopy เพื่อป้องกันปัญหากับ nested dicts
        import copy
        new_step = copy.deepcopy(steps_list[index])
        new_step['id'] = str(uuid.uuid4())
        steps_list.insert(index + 1, new_step)
        _save_workspace()

def update_step_args(section_key, step_id, new_args):
    steps_list = _get_workspace()['steps'][section_key]
    index = _find_step_index(steps_list, step_id)
    if index != -1:
        steps_list[index]['args'] = new_args
        _save_workspace()

def batch_update_step_args(section_key, updates_dict):
    ws = _get_workspace()
    steps_map = {s['id']: s for s in ws['steps'][section_key]}
    for step_id, new_args in updates_dict.items():
        if step_id in steps_map:
            steps_map[step_id]['args'].update(new_args)
    _save_workspace()

# ===================================================================
# ===== 3. ฟังก์ชันสร้าง Template =====
# ===================================================================

def generate_create_template():
    """
    Generate Create template using the new template module
    """
    from .template_create import generate_create_template as gen_create
    
    ws = _get_workspace()
    all_keywords, all_locators = _get_assets()
    
    # Clear existing steps
    for section in ws['steps']:
        ws['steps'][section] = []
    
    # Generate new steps using template module
    generated_steps = gen_create(ws, all_keywords, all_locators)
    
    # Assign generated steps to workspace
    for section_key, steps_list in generated_steps.items():
        ws['steps'][section_key] = steps_list
    
    _save_workspace()
    
    import streamlit as st
    st.toast("🤖 'Create' template generated successfully!", icon="✨")

def generate_update_template():
    """
    Generate Update template using the new template module
    """
    from .template_update import generate_update_template as gen_update
    
    ws = _get_workspace()
    all_keywords, all_locators = _get_assets()
    
    # Clear existing steps
    for section in ws['steps']:
        ws['steps'][section] = []
    
    # Generate new steps using template module
    generated_steps = gen_update(ws, all_keywords, all_locators)
    
    # Assign generated steps to workspace
    for section_key, steps_list in generated_steps.items():
        ws['steps'][section_key] = steps_list
    
    _save_workspace()
    
    import streamlit as st
    st.toast("🔄 'Update' template generated successfully!", icon="✨")

def generate_delete_template():
    """
    Generate Delete template using the new template module
    """
    from .template_delete import generate_delete_template as gen_delete
    
    ws = _get_workspace()
    all_keywords, all_locators = _get_assets()
    
    # Clear existing steps
    for section in ws['steps']:
        ws['steps'][section] = []
    
    # Generate new steps using template module
    generated_steps = gen_delete(ws, all_keywords, all_locators)
    
    # Assign generated steps to workspace
    for section_key, steps_list in generated_steps.items():
        ws['steps'][section_key] = steps_list
    
    _save_workspace()
    
    import streamlit as st
    st.toast("🗑️ 'Delete' template generated successfully!", icon="✨")
# ===== END: สิ้นสุดฟังก์ชันใหม่ =====

def auto_detect_and_generate_form_steps(add_to_section):
    all_keywords, all_locators = _get_assets(); ws = _get_workspace()
    fill_keyword = next((kw for kw in all_keywords if kw['name'] == 'Fill in data form'), None)
    if not fill_keyword: return 0
    input_suffixes = ['_INPUT', '_SELECT', '_TEXTAREA', '_DATE', '_FILE']
    if not all_locators: return 0 # Guard clause
    form_locators = [loc for loc in all_locators if any(loc['name'].upper().endswith(suffix) for suffix in input_suffixes) and 'SEARCH' not in loc['name'].upper()]
    steps_added = 0
    existing_loc_names = {s['args'].get('locator_field', {}).get('name') for s in ws['steps'][add_to_section]}
    for locator_obj in form_locators:
        if locator_obj['name'] not in existing_loc_names:
            new_step = {"keyword": fill_keyword['name'], "args": {"locator_field": locator_obj, "value": "", "select_attribute": "label", "is_checkbox_type": False, "is_ant_design": False, "is_switch_type": False, "locator_switch_checked": ""}}
            insert_pos = max(0, len(ws['steps'][add_to_section]) - 2)
            ws['steps'][add_to_section].insert(insert_pos, {**new_step, 'id': str(uuid.uuid4())})
            steps_added += 1
    if steps_added > 0: _save_workspace()
    return steps_added

# ===================================================================
# ===== 4. LOGIC สำหรับสร้าง SCRIPT (REFACTORED) =====
# ===================================================================

def _format_arguments_for_script(keyword, args):
    """
    ฟังก์ชัน Helper ใหม่: แปลง dict ของ arguments เป็น list ของ string ที่พร้อมใช้งาน
    (REVISED: Added logic for 'Verify Result of data table')
    """
    args_list = []
    
    # --- Logic พิเศษสำหรับ 'Fill in data form' ---
    if keyword == 'Fill in data form':
        locator_obj = args.get('locator_field')
        if isinstance(locator_obj, dict) and locator_obj.get('name'):
            args_list.append(f"locator_field=${{{get_clean_locator_name(locator_obj['name'])}}}")
        if not args.get('is_switch_type'):
            value = args.get('value', '')
            args_list.append(f"value={value or '${EMPTY}'}")
        args_list.append(f"select_attribute={args.get('select_attribute', 'label')}")
        if args.get('is_checkbox_type'): args_list.append("is_checkbox_type=${True}")
        if args.get('is_ant_design'): args_list.append("is_ant_design=${True}")
        if args.get('is_switch_type'):
            args_list.append("is_switch_type=${True}")
            switch_loc_obj = args.get('locator_switch_checked')
            if isinstance(switch_loc_obj, dict) and switch_loc_obj.get('name'):
                args_list.append(f"locator_switch_checked=${{{get_clean_locator_name(switch_loc_obj['name'])}}}")
        return args_list

    # --- ✅✅✅ START: NEW LOGIC for 'Verify Result of data table' ---
    if keyword == 'Verify Result of data table':
        # 1. Handle fixed args
        if args.get('theader'): args_list.append(f"theader=${{{args['theader']}}}")
        if args.get('tbody'): args_list.append(f"tbody=${{{args['tbody']}}}")
        if args.get('rowdata'): args_list.append(f"rowdata={args['rowdata']}")
        if args.get('ignore_case'): args_list.append(f"ignore_case={args['ignore_case']}")
        
        # 2. Handle dynamic 'assertion_columns'
        #    แปลงจาก: [{'header_name': 'H1', 'expected_value': 'V1'}, ...]
        #    ไปเป็น:  [ 'col.H1=H1', 'assert.H1=equal', 'expected.H1=V1', ... ]
        assertion_columns = args.get('assertion_columns', [])
        for assertion in assertion_columns:
            header = assertion.get('header_name')
            expected = assertion.get('expected_value')
            if header:
                # เราจะ hardcode 'equal' Tensei
                args_list.append(f"col.{header}={header}")
                args_list.append(f"assert.{header}=equal")
                args_list.append(f"expected.{header}={expected or '${EMPTY}'}")
        return args_list
    # --- ✅✅✅ END: NEW LOGIC ---

    # --- ✅✅✅ START: NEW LOGIC for 'Verify data form' ---
    if keyword == 'Verify data form':
        locator_obj = args.get('locator_field')
        if isinstance(locator_obj, dict) and locator_obj.get('name'):
            args_list.append(f"locator_field=${{{get_clean_locator_name(locator_obj['name'])}}}")
        
        expected_val = args.get('expected_value', '')
        args_list.append(f"expected_value={expected_val or '${EMPTY}'}")
        
        if args.get('select_attribute'):
            args_list.append(f"select_attribute={args.get('select_attribute')}")
        return args_list
    # --- ✅✅✅ END: NEW LOGIC ---

    # --- Logic ทั่วไปสำหรับ Keywords อื่นๆ ---
    for name, value in args.items():
        if value or value is False or value == "": # (ปรับให้รองรับค่าว่าง)
            
            # 1. จัดการ Locator ที่เป็น Object (จาก auto_detect)
            if isinstance(value, dict) and value.get('name'):
                formatted_value = f"${{{get_clean_locator_name(value['name'])}}}"
            
            # 2. จัดการค่าว่าง
            elif str(value).strip() == "":
                formatted_value = "${EMPTY}"
            
            # 3. จัดการค่าตัวแปร
            elif str(value).startswith('${'):
                formatted_value = value
                
            # 4. จัดการค่าปกติ (Plain text)
            else:
                # ตรวจสอบว่า arg name คล้าย locator หรือไม่
                is_loc_arg = any(s in name.lower() for s in ['locator', 'menu', 'name', 'header', 'body'])
                formatted_value = f"${{{value}}}" if is_loc_arg else value
            
            args_list.append(f"{name}={formatted_value}")
    return args_list

def _format_step_for_script(step, indent=4):
    """ฟังก์ชันหลักในการแปลง 1 step เป็น 1 บรรทัดโค้ด"""
    keyword = step.get('keyword', 'N/A')
    args = step.get('args', {})
    
    formatted_args = _format_arguments_for_script(keyword, args)
    
    separator = "    " # 4 spaces
    
    # --- ✅✅✅ REVISED: Logic สำหรับ Keyword ที่อาจยาวหลายบรรทัด ---
    # (เช่น Verify Result of data table)
    
    if keyword == 'Verify Result of data table' and 'assertion_columns' in args and args['assertion_columns']:
        # แยก args ปกติ ออกจาก args ของ column
        fixed_args = [a for a in formatted_args if not a.startswith(('col.', 'assert.', 'expected.'))]
        col_args = [a for a in formatted_args if a.startswith(('col.', 'assert.', 'expected.'))]

        lines = []
        # บรรทัดแรก: Keyword + Fixed args
        lines.append(f"{' ' * indent}{keyword}{separator if fixed_args else ''}{separator.join(fixed_args)}")
        
        # บรรทัดต่อมา: Column args (จัดกลุ่มทีละ 3)
        if col_args:
            # จัดกลุ่ม col_args ทีละ 3 (col, assert, expected)
            grouped_col_args = [col_args[i:i + 3] for i in range(0, len(col_args), 3)]
            for group in grouped_col_args:
                lines.append(f"{' ' * indent}...{separator}{separator.join(group)}")
        
        return "\n".join(lines)
    
    # --- Logic เดิมสำหรับ Keyword บรรทัดเดียว ---
    return f"{' ' * indent}{keyword}{separator if formatted_args else ''}{separator.join(formatted_args)}"

def generate_robot_script():
    """สร้าง Robot Framework script ทั้งหมดจากข้อมูลใน workspace"""
    ws = _get_workspace()
    
    def _format_run_keywords(keyword, steps):
        if not steps: return ""
        if len(steps) == 1:
            # ใช้ _format_step_for_script เพื่อรองรับ multi-line
            step_lines = _format_step_for_script(steps[0], indent=0).split('\n')
            first_line = step_lines[0]
            other_lines = [f"    ...    {line}" for line in step_lines[1:]]
            return f"{keyword}    {first_line}\n" + "\n".join(other_lines)
        
        lines = [f"{keyword}    Run Keywords"]
        for i, step in enumerate(steps):
            prefix = "    ..." if i == 0 else "    ...    AND"
            # ใช้ _format_step_for_script เพื่อรองรับ multi-line
            step_lines = _format_step_for_script(step, indent=0).split('\n')
            lines.append(f"{prefix}    {step_lines[0]}")
            if len(step_lines) > 1:
                for line in step_lines[1:]:
                    lines.append(f"{prefix}    ...    {line}")
        return "\n".join(lines)

    settings_lines = [
        "*** Settings ***",
        "Resource    ../../resources/commonkeywords.resource",
        _format_run_keywords("Suite Setup", ws['steps']['suite_setup']),
        _format_run_keywords("Test Setup", ws['steps']['test_setup']),
        _format_run_keywords("Test Teardown", ws['steps']['test_teardown']),
        _format_run_keywords("Suite Teardown", ws['steps']['suite_teardown'])
    ]
    
    all_test_steps = (
        ws['steps']['action_list'] + 
        ws['steps']['action_detail'] + 
        ws['steps']['verify_list'] + 
        ws['steps']['verify_detail']
    )
    
    test_case_lines = [f"{ws.get('test_case_name', 'TC_Placeholder')}"]
    if ws.get('tags'):
        test_case_lines.append(f"    [Tags]    {'    '.join(ws.get('tags'))}")
    
    for step in all_test_steps:
        test_case_lines.append(_format_step_for_script(step, indent=4))

    script_parts = [
        "\n".join(filter(None, settings_lines)),
        "\n*** Test Cases ***",
        "\n".join(test_case_lines)
    ]
    
    return "\n\n".join(filter(None, script_parts))

# (Add this function definition inside manager.py)

def update_step(section_key, step_id, updated_data):
    """Updates both keyword and arguments of an existing step."""
    ws = _get_workspace()
    # Ensure the section exists in the steps dictionary
    if section_key not in ws['steps']:
        print(f"Error updating step: Section '{section_key}' not found.")
        # Optionally create the section if it should exist
        # ws['steps'][section_key] = []
        return # Or handle the error appropriately

    steps_list = ws['steps'][section_key]
    
    index = _find_step_index(steps_list, step_id)
    if index != -1:
        # Update specific fields, keeping the ID
        steps_list[index]['keyword'] = updated_data.get('keyword', steps_list[index]['keyword'])
        steps_list[index]['args'] = updated_data.get('args', steps_list[index]['args'])
        _save_workspace()
        # You might want to remove print statements in production
        # print(f"Step {step_id} in {section_key} updated.")
    else:
        print(f"Error updating step: Step ID '{step_id}' not found in section '{section_key}'.")