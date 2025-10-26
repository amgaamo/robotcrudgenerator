"""
Keyword Factory Manager
Handles the business logic for the Keyword Factory tab.
(Corrected version incorporating all discussed changes)
"""
import streamlit as st
import uuid
import re
# Make sure utils functions are imported correctly
from .utils import format_robot_step_line, convert_json_path_to_robot_accessor, generate_arg_name_from_locator

# --- Initialization and Basic Getters/Setters (No changes needed) ---
def initialize_workspace():
    if 'keyword_factory_workspace' not in st.session_state:
        st.session_state.keyword_factory_workspace = {
            'active_keyword_id': None,
            'keywords': []
        }

def _get_workspace():
    if 'keyword_factory_workspace' not in st.session_state:
        initialize_workspace()
    return st.session_state.keyword_factory_workspace

def get_all_keywords():
    return _get_workspace().get('keywords', [])

def get_keyword(keyword_id):
    for kw in get_all_keywords():
        if kw['id'] == keyword_id:
            return kw
    return None

def set_active_keyword(keyword_id):
    ws = _get_workspace()
    ws['active_keyword_id'] = keyword_id

def create_new_keyword():
    ws = _get_workspace()
    new_id = str(uuid.uuid4())
    new_kw = {
        'id': new_id,
        'name': 'New Keyword Name',
        'doc': 'Documentation for this new keyword.',
        'args': [], # Start with an empty list for dicts
        'steps': [],
        'tags': ['Generated']
    }
    ws['keywords'].append(new_kw)
    ws['active_keyword_id'] = new_id
    return new_id

def delete_keyword(keyword_id):
    ws = _get_workspace()
    ws['keywords'] = [kw for kw in ws['keywords'] if kw['id'] != keyword_id]
    if ws['active_keyword_id'] == keyword_id:
        ws['active_keyword_id'] = None

# --- *** CORRECTED: update_keyword_details *** ---
def update_keyword_details(keyword_id, name): # Removed args_str
    """Updates ONLY the name, documentation, and tags of a keyword."""
    kw = get_keyword(keyword_id)
    if kw:
        kw['name'] = name

# --- Step Management (No changes needed in add, delete, move) ---
def add_step(keyword_id, new_step):
    kw = get_keyword(keyword_id)
    if kw and 'steps' in kw: # Ensure 'steps' key exists
        kw['steps'].append(new_step)

def delete_step(keyword_id, step_id):
    kw = get_keyword(keyword_id)
    if kw and 'steps' in kw:
        kw['steps'] = [s for s in kw['steps'] if s.get('id') != step_id]

def move_step(keyword_id, step_id, direction):
    kw = get_keyword(keyword_id)
    if not kw or 'steps' not in kw:
        return

    steps = kw['steps']
    try:
        index = next(i for i, s in enumerate(steps) if s['id'] == step_id)
    except StopIteration:
        return

    if direction == 'up' and index > 0:
        steps.insert(index - 1, steps.pop(index))
    elif direction == 'down' and index < len(steps) - 1:
        steps.insert(index + 1, steps.pop(index))

# --- Step Update (Correct version provided by user) ---
def update_step(keyword_id, step_id, updated_data):
    kw = get_keyword(keyword_id)
    if not kw or 'steps' not in kw:
        return

    for i, step in enumerate(kw['steps']):
        if step['id'] == step_id:
            # Update specific keys to avoid overwriting unrelated data
            if 'keyword' in updated_data:
                kw['steps'][i]['keyword'] = updated_data['keyword']
            if 'args' in updated_data:
                kw['steps'][i]['args'] = updated_data['args']
            if 'output_variable' in updated_data:
                kw['steps'][i]['output_variable'] = updated_data['output_variable']
            # Add other keys if needed in the future
            break

# --- *** CORRECTED: Quick Steps Functions *** ---
def add_quick_fill_form_steps(keyword_id, locators_to_add):
    """
    [DEPRECATED - Use add_quick_fill_form_steps_with_custom_args]
    Adds 'Fill in data form' steps with default arguments.
    Calls the new function with default arguments.
    """
    locators_with_defaults = {
        loc_name: FILL_FORM_DEFAULTS.copy() for loc_name in locators_to_add
    }
    add_quick_fill_form_steps_with_custom_args(keyword_id, locators_with_defaults)

# --- *** ฟังก์ชันใหม่ *** ---
def add_quick_fill_form_steps_with_custom_args(keyword_id, locators_with_custom_args):
    """
    Adds 'Fill in data form' steps using provided locators and their specific
    custom argument overrides. Also adds necessary arguments to the keyword.
    """
    kw = get_keyword(keyword_id)
    if not kw:
        return

    if 'args' not in kw or not isinstance(kw['args'], list):
        kw['args'] = [] # Initialize if missing/incorrect type

    current_arg_names = {arg['name'] for arg in kw['args']} # Set for quick lookup

    for loc_name, custom_args in locators_with_custom_args.items():
        # Generate suggested variable name (without ${})
        arg_var = generate_arg_name_from_locator(loc_name)
        if not arg_var: # Handle cases where generation fails
             clean_loc = loc_name.replace('LOCATOR_', '').lower()
             arg_var = f"${{{clean_loc or 'value'}}}"

        # Start building the args for this step
        step_args = {
            "locator_field": loc_name, # Pass locator name string
            "value": arg_var           # Pass the generated variable string
        }

        # Merge the custom args provided
        step_args.update(custom_args) # This adds/overwrites defaults

        new_step = {
            "id": str(uuid.uuid4()),
            "keyword": "Fill in data form", # Make sure this matches commonkeywords
            "args": step_args # Use the merged arguments
        }

        if 'steps' not in kw: kw['steps'] = []
        kw['steps'].append(new_step)

        # Add the new argument dictionary if the name isn't already present
        if arg_var not in current_arg_names:
            kw['args'].append({'name': arg_var, 'default': ''}) # Add as dict
            current_arg_names.add(arg_var) # Update the set

    # Sort args list after adding potentially multiple new ones
    kw['args'] = sorted(kw['args'], key=lambda x: x['name'])


def add_quick_verify_steps(keyword_id, locators_to_add):
    """
    [DEPRECATED - Use add_quick_verify_steps_with_custom_args]
    Adds 'Verify data form' steps with default arguments.
    Calls the new function with default arguments.
    """
    locators_with_defaults = {}
    for loc_name in locators_to_add:
        locators_with_defaults[loc_name] = VERIFY_FORM_DEFAULTS.copy()
        # Auto-generate default expected value variable
        arg_var = generate_arg_name_from_locator(loc_name)
        if not arg_var:
             clean_loc = loc_name.replace('LOCATOR_', '').lower()
             arg_var = f"${{{clean_loc or 'expected'}}}"
        locators_with_defaults[loc_name]['exp_value'] = arg_var

    add_quick_verify_steps_with_custom_args(keyword_id, locators_with_defaults)


# --- *** ฟังก์ชันใหม่ *** ---
def add_quick_verify_steps_with_custom_args(keyword_id, locators_with_custom_args):
    """
    Adds 'Verify data form' steps using provided locators and their specific
    custom argument overrides. Also adds necessary arguments to the keyword.
    """
    kw = get_keyword(keyword_id)
    if not kw:
        return

    if 'args' not in kw or not isinstance(kw['args'], list):
        kw['args'] = []

    current_arg_names = {arg['name'] for arg in kw['args']}

    for loc_name, custom_args in locators_with_custom_args.items():
        # Start building the args for this step
        step_args = {
            "locator_field": loc_name
        }

        # Merge the custom args provided
        step_args.update(custom_args) # Adds/overwrites defaults

        # Get the exp_value (which might have been auto-generated or user-modified)
        arg_var = step_args.get('exp_value')

        new_step = {
            "id": str(uuid.uuid4()),
            "keyword": "Verify data form", # Match commonkeywords
            "args": step_args
        }

        if 'steps' not in kw: kw['steps'] = []
        kw['steps'].append(new_step)

        # Add the exp_value as an argument if it looks like a variable and isn't already added
        if arg_var and isinstance(arg_var, str) and arg_var.startswith("${") and arg_var.endswith("}"):
            if arg_var not in current_arg_names:
                kw['args'].append({'name': arg_var, 'default': ''})
                current_arg_names.add(arg_var)

    # Sort args list
    kw['args'] = sorted(kw['args'], key=lambda x: x['name'])

# --- *** Script Generation (Correct version from previous steps) *** ---
def generate_robot_script_for_keyword(keyword_id):
    kw = get_keyword(keyword_id)
    if not kw:
        return "# Keyword not found."

    script = []
    script.append(f"{kw.get('name', 'Untitled Keyword')}") # Use get with default

    # --- Arguments Section ---
    args_list_of_dicts = kw.get('args', []) # Read List of Dicts
    if args_list_of_dicts:
        args_parts = []
        for arg_dict in args_list_of_dicts:
            arg_name = arg_dict.get('name')
            arg_default = arg_dict.get('default', None)
            if arg_name:
                if arg_default is not None and arg_default != '':
                    args_parts.append(f"{arg_name}={arg_default}")
                else:
                    args_parts.append(arg_name)
        if args_parts:
            script.append(f"    [Arguments]    {'    '.join(args_parts)}")

    # # --- Documentation Section ---
    # doc = kw.get('doc')
    # if doc:
    #     doc_lines = doc.split('\n')
    #     script.append(f"    [Documentation]    {doc_lines[0]}")
    #     for line in doc_lines[1:]:
    #         script.append(f"    ...    {line}") # Consistent 4 spaces before ...

    # # --- Tags Section ---
    # tags = kw.get('tags')
    # if tags:
    #     script.append(f"    [Tags]    {', '.join(tags)}") # Use comma space

# --- Steps Section ---
    steps = kw.get('steps') # Corrected variable name
    if not steps:
        script.append("    Log    This keyword has no steps.") # 4 spaces indent
    else:
        indent_level = 0 # Base indent level within the keyword
        base_indent = "    " # 4 spaces

        for step in steps: # Use the correct variable 'steps'
            keyword_name = step.get('keyword', '')

            # --- คำนวณ Indent ปัจจุบัน *ก่อน* สร้างโค้ด ---
            current_indent_adjustment = 0
            if keyword_name in ['ELSE IF Condition', 'ELSE', 'END']:
                # ลด indent ชั่วคราว *สำหรับบรรทัดนี้เท่านั้น*
                current_indent_adjustment = -1

            # คำนวณ indent string ที่จะใช้จริง (ป้องกันค่าติดลบ)
            actual_indent_level = max(0, indent_level + current_indent_adjustment)
            current_indent_str = base_indent * (actual_indent_level + 1) # +1 เพราะอยู่ใน Keyword

            # --- จัดการ Logic พิเศษสำหรับ IF / ELSE IF / ELSE / END ---
            if keyword_name == 'IF Condition':
                condition = step.get('args', {}).get('condition', 'True')
                script.append(f"{current_indent_str}IF    {condition}")
                indent_level += 1 # เพิ่มระดับสำหรับ Step *ถัดไป*
                continue # ข้ามไป Step ถัดไป

            elif keyword_name == 'ELSE IF Condition': # <-- เพิ่ม ELSE IF
                condition = step.get('args', {}).get('condition', 'True')
                script.append(f"{current_indent_str}ELSE IF    {condition}")
                # ไม่เปลี่ยน indent_level สำหรับ Step ถัดไป
                continue # ข้ามไป Step ถัดไป

            elif keyword_name == 'ELSE': # <-- เพิ่ม ELSE
                script.append(f"{current_indent_str}ELSE")
                # ไม่เปลี่ยน indent_level สำหรับ Step ถัดไป
                continue # ข้ามไป Step ถัดไป

            elif keyword_name == 'END':
                script.append(f"{current_indent_str}END")
                indent_level = max(0, indent_level - 1) # ลดระดับสำหรับ Step *ถัดไป*
                continue # ข้ามไป Step ถัดไป

            # --- Logic เดิมสำหรับ Step ทั่วไป (ใช้ current_indent_str) ---
            formatted_lines_str = format_robot_step_line(step)
            lines = formatted_lines_str.split('\n')

            if lines:
                script.append(f"{current_indent_str}{lines[0]}") # บรรทัดแรก
                if len(lines) > 1:
                    for line in lines[1:]: # บรรทัดต่อเนื่อง
                        if line.strip().startswith("..."):
                            script.append(f"{current_indent_str}{line}") # Indent เท่าเดิม
                        else:
                            script.append(f"{current_indent_str}{base_indent}{line}") # Indent เพิ่ม

            # --- Logic เดิมสำหรับ Set Variable (ใช้ current_indent_str) ---
            output_config = step.get('output_variable', {})
            if output_config.get('enabled') and output_config.get('name', '').strip():
                var_name = output_config['name'].strip()
                scope = output_config.get('scope', 'Test').capitalize()
                # ... (logic กำหนด value_to_set เหมือนเดิม) ...
                selected_source = output_config.get('value_source', "Default Return Value (${OUTPUT})")
                source_detail = output_config.get('source_detail', '')
                value_to_set = "${OUTPUT}"
                if selected_source == "API Response Body (${GLOBAL_RESPONSE_JSON})": value_to_set = "${GLOBAL_RESPONSE_JSON}"
                elif selected_source == "API Response JSON Path" and source_detail:
                    robot_accessor = convert_json_path_to_robot_accessor(source_detail)
                    if robot_accessor: value_to_set = f"${{GLOBAL_RESPONSE_JSON}}{robot_accessor}"
                    else: print(f"Warning: Could not convert JSON Path '{source_detail}'.")
                elif selected_source == "Specific Argument Value" and source_detail: value_to_set = f"${{{source_detail}}}"
                elif selected_source == "Manual Value/Variable" and source_detail: value_to_set = source_detail

                if var_name:
                    set_var_line = f"{current_indent_str}Set {scope} Variable    ${{{var_name}}}    {value_to_set}"
                    script.append(set_var_line)
        # --- จบ Loop for ---

    # Add a newline at the end for spacing between keywords
    script.append("")
    return "\n".join(script)