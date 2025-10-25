# modules/utils.py
"""
Common Utility Functions
Contains shared, pure-logic helper functions used across different modules.
This module should NOT import streamlit.
"""
import re
import os
import csv
from pathlib import Path

# ===================================================================
# ===== 1. String & Naming Utilities (From session_manager.py)
# ===================================================================

FILL_FORM_DEFAULTS = {
    'is_switch_type': False,
    'is_checkbox_type': False,
    'select_attribute': 'label',
    'is_ant_design': False,
    'locator_switch_checked': '${EMPTY}'
}

VERIFY_FORM_DEFAULTS = {
    'select_attribute': 'label',
    'ignorcase': False,         # Correct key name is 'ignorcase'
    'antdesign': False,         # Correct key name is 'antdesign'
    'is_switchtype': False,     # Correct key name is 'is_switchtype'
    'locator_switch_checked': '${EMPTY}',
    'is_skipfield': False       # Correct key name is 'is_skipfield'
}

def get_clean_locator_name(raw_name):
    """Removes Robot Framework variable syntax ${...} for cleaner display."""
    if isinstance(raw_name, str) and raw_name.startswith('${') and raw_name.endswith('}'):
        return raw_name[2:-1]
    return raw_name

# ===================================================================
# ===== 2. File Icon Utility (From app.py)
# ===================================================================

def get_file_icon(file_name):
    """Return an emoji icon based on file extension."""
    if file_name.endswith('.robot'):
        return "📝"
    elif file_name.endswith('.resource'):
        return "📝"
    elif file_name.endswith('.py'):
        return "🐍"
    elif file_name.endswith('.txt'):
        return "📝"
    else:
        return "📄"

# ===================================================================
# ===== 3. Robot Framework File Parsers (From file_manager.py)
# ===================================================================
# (Refactored to remove all 'st.warning' and 'st.error' calls)

def parse_robot_keywords(file_content: str):
    """
    [FINAL FIX] Parses keyword definitions with a highly robust logic for multi-line arguments,
    correctly handling blank lines and comments within the [Arguments] block.
    (Moved from file_manager.py)
    """
    keywords_list = []
    keywords_section_match = re.search(r'\*\*\* Keywords \*\*\*(.*)', file_content, re.DOTALL | re.IGNORECASE)
    
    if not keywords_section_match:
        return []

    keywords_content = keywords_section_match.group(1)
    keyword_blocks = re.split(r'\n(?=\S)', keywords_content.strip())

    for block in keyword_blocks:
        if not block.strip():
            continue

        lines = block.strip().split('\n')
        keyword_name = lines[0].strip()
        
        if not keyword_name or keyword_name.startswith(('#', '[', '...', 'FOR', 'IF', 'ELSE')):
            continue

        keyword_body_lines = lines[1:]
        
        doc_list = [line.split(']', 1)[1].strip() for line in keyword_body_lines if line.strip().lower().startswith('[documentation]')]
        doc = " ".join(doc_list) if doc_list else "No documentation available."

        args = []
        arg_start_index = -1
        for i, line in enumerate(keyword_body_lines):
            if line.strip().lower().startswith('[arguments]'):
                arg_start_index = i
                break
        
        if arg_start_index != -1:
            full_args_str = keyword_body_lines[arg_start_index].split(']', 1)[1].strip()
            
            for line in keyword_body_lines[arg_start_index + 1:]:
                stripped_line = line.strip()
                if stripped_line.startswith('...'):
                    full_args_str += "  " + stripped_line[3:].strip()
                elif not stripped_line or stripped_line.startswith('#'):
                    continue
                else:
                    break
            
            if full_args_str:
                parsed_args = []
                arg_strings = re.split(r'\s{2,}(?=[$@&]\{)', full_args_str)
                for arg_str in arg_strings:
                    if not arg_str.strip(): continue
                    if '=' in arg_str:
                        name, default_value = arg_str.split('=', 1)
                        parsed_args.append({"name": name.strip(), "default": default_value.strip()})
                    else:
                        parsed_args.append({"name": arg_str.strip(), "default": None})
                args = parsed_args
            
        keywords_list.append({"name": keyword_name, "args": args, "doc": doc})

    return keywords_list

def parse_robot_variables(content: str):
    """
    [FIXED] Reads ALL variables from a string content,
    including scalar (${}), list (@{}), and dictionary (&{...}) types,
    and handles multi-line definitions.
    """
    try:
        variables_match = re.search(r'\*\*\* Variables \*\*\*(.*?)(?=\*\*\*|$)', content, re.DOTALL | re.IGNORECASE)
        if not variables_match:
            print("Warning: Could not find a '*** Variables ***' section in the content.")
            return []

        variables_content = variables_match.group(1)
        all_variables = []
        
        # Pattern to find the start of a variable
        # $&@{name}    value...
        var_start_pattern = re.compile(r'^\s*([$@&]\{[^{}]+\})\s*(.*)$')
        # ...    value...
        continuation_pattern = re.compile(r'^\s*\.\.\.\s*(.*)$')

        lines = variables_content.strip().split('\n')
        
        current_var_data = None

        for line in lines:
            line_strip = line.strip()
            if not line_strip or line_strip.startswith('#'):
                # Skip empty lines and comments
                continue
            
            var_match = var_start_pattern.match(line)
            cont_match = continuation_pattern.match(line)

            if var_match:
                # This is a new variable definition.
                # First, save the previous variable if one was being built.
                if current_var_data:
                    all_variables.append(current_var_data)
                
                full_name = var_match.group(1).strip() # e.g., ${homemenu}
                first_value_line = var_match.group(2).strip()
                
                var_type_char = full_name[0]
                var_name = full_name[2:-1] # e.g., homemenu
                
                var_type = 'scalar'
                if var_type_char == '@':
                    var_type = 'list'
                elif var_type_char == '&':
                    var_type = 'dict'
                    
                current_var_data = {
                    'name': var_name,
                    'type': var_type,
                    'value_lines': [first_value_line] # Store raw value lines
                }

            elif cont_match and current_var_data:
                # This is a continuation of the previous variable.
                continuation_value_line = cont_match.group(1).strip()
                # ตรวจสอบว่ามีค่าหรือไม่ (ป้องกันบรรทัด ... ว่างๆ)
                if continuation_value_line:
                    current_var_data['value_lines'].append(continuation_value_line)
            
            else:
                # This line is not a var start or continuation (e.g., junk line),
                # so save the current var and reset.
                if current_var_data:
                    all_variables.append(current_var_data)
                current_var_data = None
        
        # Save the very last variable being processed
        if current_var_data:
            all_variables.append(current_var_data)

        # --- Post-process the 'value_lines' into structured 'value' ---
        final_parsed_variables = []
        for var_data in all_variables:
            try:
                if var_data['type'] == 'scalar':
                    # Join all lines, though scalars are usually single-line
                    var_data['value'] = " ".join(var_data['value_lines'])
                
                elif var_data['type'] == 'list':
                    # Each line is an item
                    var_data['value'] = [line for line in var_data['value_lines'] if line]
                
                elif var_data['type'] == 'dict':
                    # Parse key=value pairs
                    dict_value = {}
                    combined_lines = " ".join(var_data['value_lines'])
                    
                    # ใช้ regex findall เพื่อจับ key=value ที่อาจมี space
                    # (?:^|\s+) = non-capturing group:
                    #   - ^ = or start of string
                    #   - \s+ = or one or more spaces
                    # ([^=\s]+) = Group 1: key (anything not = or space)
                    # =
                    # (.*?(?=\s+[^=\s]+=|\s*$)) = Group 2: value
                    #   - .*? = non-greedy match of the value
                    #   - (?=...) = positive lookahead (ends before...)
                    #   - \s+[^=\s]+= = ...next key= (e.g. " key2=")
                    #   - | = or
                    #   - \s*$ = ...end of the string
                    
                    # Regex ที่ง่ายกว่าและรองรับค่าที่มี space
                    # (แยกตาม '  ' (2+ spaces) หรือ '='
                    # แต่วิธีที่ปลอดภัยที่สุดคือการ parse ทีละบรรทัด
                    
                    for line in var_data['value_lines']:
                        # แยก key=value ที่อาจอยู่บรรทัดเดียวกัน
                        # ใช้ regex split ตาม space ที่มากกว่า 2 (เว้นแต่จะอยู่ใน quote)
                        # เพื่อความเรียบง่าย: สมมติว่า 1 key-value ต่อ 1 line (สำหรับ dict)
                        
                        if '=' in line:
                            # Split on the *first* equals sign
                            key, val = line.split('=', 1)
                            dict_value[key.strip()] = val.strip()
                        elif line:
                            # Handle flag-style entries (e.g., "readonly")
                            dict_value[line] = None 
                    var_data['value'] = dict_value
                
                del var_data['value_lines'] # Clean up temporary field
                final_parsed_variables.append(var_data)
            except Exception as e_inner:
                print(f"Error parsing variable '{var_data.get('name')}': {e_inner}")

        if not final_parsed_variables:
            print("Warning: No variables were found in the '*** Variables ***' section.")
        
        return final_parsed_variables

    except Exception as e:
        print(f"An error occurred while parsing content: {str(e)}")
        return []

def parse_data_sources(content: str):
    """
    Parses a datasources.resource file content to extract CSV paths.
    (Moved from file_manager.py and refactored to remove streamlit calls)
    """
    variables = {}
    data_sources = []

    try:
        # 1. Parse *** Variables *** section
        variables_match = re.search(r'\*\*\* Variables \*\*\*(.*?)(?=\*\*\*|$)', content, re.DOTALL | re.IGNORECASE)
        if variables_match:
            variables_content = variables_match.group(1)
            var_pattern = re.compile(r'^\s*\$\{([^}]+)\}\s+([^\s].*?)\s*(?:#.*)?$', re.MULTILINE)
            for match in var_pattern.finditer(variables_content):
                var_name = match.group(1).strip()
                var_value = match.group(2).strip()
                variables[var_name] = var_value

        # 2. Parse *** Keywords *** section
        keywords_match = re.search(r'\*\*\* Keywords \*\*\*(.*)', content, re.DOTALL | re.IGNORECASE)
        if keywords_match:
            keywords_content = keywords_match.group(1)
            keyword_blocks = re.split(r'\n(?=\S)', keywords_content.strip())

            for block in keyword_blocks:
                lines = block.strip().split('\n')
                keyword_name_line = lines[0].strip()
                
                if not keyword_name_line.lower().startswith('import datasource'):
                    continue 
                
                csv_var_match = re.search(r'Import datasource file\s+\$\{([^}]+)\}', block, re.IGNORECASE)
                ds_var_match = re.search(r'Set Global Variable\s+\$\{(DS_[^}]+)\}', block, re.IGNORECASE)
                col_var_match = re.search(r'Set Global Variable\s+\$\{([^}]+)\}\s+\$\{value_col\}', block, re.IGNORECASE)

                if csv_var_match and ds_var_match and col_var_match:
                    csv_path_var_name = csv_var_match.group(1)
                    ds_name = ds_var_match.group(1)
                    col_name = col_var_match.group(1)
                    csv_file_name = "NOT_FOUND"
                    
                    if csv_path_var_name in variables:
                        full_path_value = variables[csv_path_var_name]
                        clean_path = full_path_value
                        clean_path = re.sub(r'\$\{CURDIR\}', '', clean_path)
                        clean_path = re.sub(r'\$\{/\}', '/', clean_path)
                        clean_path = re.sub(r'\$\{[^}]+\}', '', clean_path)
                        clean_path = clean_path.strip().strip('/')
                        
                        if '/' in clean_path:
                            csv_file_name = clean_path.split('/')[-1]
                        else:
                            csv_file_name = clean_path
                        
                        csv_file_name = csv_file_name.strip()
                        if not csv_file_name.endswith('.csv'):
                            csv_match = re.search(r'([^/\\]+\.csv)', csv_file_name)
                            if csv_match:
                                csv_file_name = csv_match.group(1)
                    else:
                        print(f"Warning: Variable '${csv_path_var_name}' not found in *** Variables ***")

                    data_sources.append({
                        'file_name': csv_file_name,
                        'name': ds_name,
                        'col_name': col_name,
                        'is_imported': True
                    })
        return data_sources
    except Exception as e:
        print(f"Error parsing datasources file: {e}")
        return []

# ===================================================================
# ===== 4. Robot Framework Formatting (From test_flow_manager.py & ui_common.py)
# ===================================================================

def format_robot_step_line(step):
    """
    Helper to format a single step object into string with named arguments.
    🔧 FIXED V14: Refined boolean formatting and argument name omission logic
                  to ensure 'exp_value' and other arguments are always included correctly.
    """
    keyword = step.get('keyword', '')
    args = step.get('args', {})
    kw_padding = "    " # 4 spaces

    # --- Handle special table verification keyword ---
    # (Assuming this part is correct or less critical for now)
    if keyword.strip() == 'Verify Result of data table':
        # ... (Existing logic for Verify Result of data table - ensure it uses _format_value_for_robot) ...
        # Simplified example - Ensure this section also uses _format_value_for_robot
        fixed_args = {}
        col_args = {}
        for k, v in args.items():
            if k.startswith(('col.', 'assert.', 'expected.')):
                col_args[k] = v
            else:
                fixed_args[k] = v

        first_line_parts = [keyword]
        fixed_arg_order = sorted(fixed_args.keys())
        for name in fixed_arg_order:
             value = fixed_args[name]
             robot_name = 'ignore_case' if name == 'ignorcase' else name
             formatted_val = _format_value_for_robot(value)
             if formatted_val is not None:
                  final_formatted_value = formatted_val
                  # Apply specific boolean formatting
                  if isinstance(value, bool): final_formatted_value = '${True}' if value else '${False}'
                  elif formatted_val == 'True': final_formatted_value = '${True}'
                  elif formatted_val == 'False': final_formatted_value = '${False}'
                  # Append arg=value
                  first_line_parts.append(f"{robot_name}={final_formatted_value}")

        column_lines = []
        # ... (rest of Verify Result logic formatting col_args) ...
        final_output = kw_padding.join(first_line_parts)
        if column_lines:
            final_output += "\n" + "\n".join([f"{kw_padding}{line}" for line in column_lines])
        return final_output
    # --- End special handling ---

    # --- Check for Keywords with Defaults ---
    is_fill_form_kw = (keyword == "Fill in data form")
    is_verify_form_kw = (keyword == "Verify data form")

    # --- Standard keyword formatting ---
    parts = [keyword]
    valid_args_with_none = args.copy()

    # Define argument order priority
    arg_order = sorted(valid_args_with_none.keys(), key=lambda x: (
        0 if 'locator' in x.lower() else
        1 if x == 'main_menu' else
        2 if x == 'submenu' else
        3 if x in ['exp_value', 'value'] else
        4 # Other args
    ))

    # Iterate through arguments in defined order
    for arg_name in arg_order:
        value = valid_args_with_none[arg_name] # Get value, might be None
        arg_name_lower = arg_name.lower()

        skip_argument = False

        # --- Default Skipping Logic (Same as before) ---
        if is_fill_form_kw and arg_name in FILL_FORM_DEFAULTS:
             if arg_name not in ['locator_field', 'value']:
                default_value = FILL_FORM_DEFAULTS.get(arg_name)
                current_value_original = value
                if arg_name == 'locator_switch_checked' and default_value == '${EMPTY}':
                    if current_value_original in ['${EMPTY}', False, 'False', None, '']: skip_argument = True
                elif isinstance(default_value, bool) and isinstance(current_value_original, bool):
                    if current_value_original == default_value: skip_argument = True
                elif isinstance(default_value, str) and isinstance(current_value_original, str):
                    if current_value_original == default_value: skip_argument = True
                elif isinstance(default_value, bool) and isinstance(current_value_original, str):
                    default_as_robot_bool = '${True}' if default_value else '${False}'
                    if _format_value_for_robot(current_value_original) == default_as_robot_bool: skip_argument = True

        elif is_verify_form_kw and arg_name in VERIFY_FORM_DEFAULTS:
             if arg_name not in ['locator_field', 'exp_value', 'assertion']:
                default_value = VERIFY_FORM_DEFAULTS.get(arg_name)
                current_value_original = value
                if arg_name == 'locator_switch_checked' and default_value == '${EMPTY}':
                     if current_value_original in ['${EMPTY}', False, 'False', None, '']: skip_argument = True
                elif arg_name == 'select_attribute' and default_value == 'label':
                     if current_value_original == 'label': skip_argument = True
                elif isinstance(default_value, bool) and isinstance(current_value_original, bool):
                     if current_value_original == default_value: skip_argument = True
                elif isinstance(default_value, bool) and isinstance(current_value_original, str):
                     default_as_robot_bool = '${True}' if default_value else '${False}'
                     if _format_value_for_robot(current_value_original) == default_as_robot_bool: skip_argument = True
                elif isinstance(default_value, str) and isinstance(current_value_original, str):
                     if current_value_original == default_value: skip_argument = True

        if skip_argument:
            continue
        # --- End Default Skipping ---

        # --- Format Value for Robot ---
        if value is None: value_to_format = '${EMPTY}'
        elif value == '' and arg_name_lower in ['menu_locator', 'main_menu', 'submenu']: continue
        elif value == '': value_to_format = '${EMPTY}'
        else: value_to_format = value

        # Use helper to get base formatted string (handles vars, ${EMPTY}, 'True'/'False' strings)
        formatted_value_str = _format_value_for_robot(value_to_format)

        # --- Append parts [REVISED LOGIC V3 - Clearer Boolean Handling] ---
        if formatted_value_str is not None:
             final_output_value = formatted_value_str # Start with helper result
             original_value = valid_args_with_none[arg_name] # Get original for type check

             # 1. Convert actual Python Booleans to ${True}/${False}
             if isinstance(original_value, bool):
                  final_output_value = '${True}' if original_value else '${False}'
             # 2. Convert string 'True'/'False' (from helper) to ${True}/${False}
             elif formatted_value_str == 'True': final_output_value = '${True}'
             elif formatted_value_str == 'False': final_output_value = '${False}'
             # Now final_output_value holds the correct Robot representation

             # 3. Determine if argument name should be omitted (ONLY for specific boolean flags)
             # This list defines which arguments can omit their name if value is True/False
             boolean_flags_can_omit_name = [
                 'is_switch_type', 'is_checkbox_type', 'is_ant_design',
                 'ignorcase', 'is_skipfield'
             ]
             omit_arg_name = (arg_name_lower in boolean_flags_can_omit_name and
                              final_output_value in ['${True}', '${False}'])

             # 4. Append to parts list
             if omit_arg_name:
                   parts.append(f"{final_output_value}") # Append only value
             else:
                   # Append name=value for all other cases (including locator, exp_value, value, assertion, etc.)
                   parts.append(f"{arg_name}={final_output_value}")
             # --- End Revised Append Logic V3 ---

    # --- Line breaking logic (เหมือนเดิม) ---
    if len(parts) <= 1:
        return parts[0] if parts else ""

    first_line = parts[0]
    remaining_parts = parts[1:]
    lines = [first_line]
    current_line_len = len(first_line)
    LINE_LENGTH_THRESHOLD = 120
    arg_padding = "    "
    cont_padding = f"...{kw_padding}"

    for i, part in enumerate(remaining_parts):
        part_with_padding = f"{arg_padding}{part}"
        part_len = len(part_with_padding)
        if current_line_len > len(first_line) and (current_line_len + part_len > LINE_LENGTH_THRESHOLD):
            lines.append(f"{cont_padding}{part}")
            current_line_len = len(lines[-1])
        else:
            lines[-1] += part_with_padding
            current_line_len += part_len
    return "\n".join(lines)

# --- [HELPER] Function for formatting values ---
def _format_value_for_robot(value):
    """
    Applies the V10 smart formatting logic to a single value.
    Handles None by returning None. Handles empty string by returning '${EMPTY}'.
    Converts boolean True/False to string 'True'/'False'.
    """
    if value is None:
        return None # Caller function handles None -> '${EMPTY}' conversion
    if value == '':
         return '${EMPTY}' # Explicitly return ${EMPTY} for empty string

    formatted_value = None

    if isinstance(value, str):
        v_str = str(value).strip() # Should not be empty here

        # Pattern 1: Menu dictionary access (e.g., ${mainmenu}[key])
        menu_pattern = r'^(\$\{)?(mainmenu|submenu|menuname|homemenu)(\})?\[([^\]]+)\]$'
        menu_match = re.match(menu_pattern, v_str)
        if menu_match: formatted_value = f"${{{menu_match.group(2)}}}[{menu_match.group(4)}]"

        # Pattern 2: Already a Robot variable (e.g., ${VAR}, @{LIST}, &{DICT})
        elif re.match(r'^[$@&]\{.*\}$', v_str): formatted_value = v_str

        # Pattern 3: The literal string '${EMPTY}' or boolean strings 'true'/'false'
        elif v_str == '${EMPTY}' or v_str.lower() in ['true', 'false']:
            # Return the original case for '${EMPTY}', capitalize for boolean strings
            formatted_value = v_str.capitalize() if v_str.lower() in ['true', 'false'] else v_str

        # Pattern 4: UPPERCASE_WITH_UNDERSCORE (likely a constant variable)
        elif re.match(r'^[A-Z][A-Z0-9_]*$', v_str): formatted_value = f"${{{v_str}}}"

        # Pattern 5: Starts with LOCATOR_ (likely a locator variable)
        elif v_str.startswith('LOCATOR_'): formatted_value = f"${{{v_str}}}"

        # Pattern 6: Regular text values
        else: formatted_value = v_str

    # Handle Python boolean type -> convert to string 'True' or 'False'
    elif isinstance(value, bool):
        formatted_value = 'True' if value else 'False'

    # Handle other types (numbers, etc.) -> convert to string
    else:
        formatted_value = str(value)

    return formatted_value


def format_args_as_string(args_dict):
    """
    Helper to format arguments as a simple string for st.caption
    
    🔧 FIXED V10: Smart Variable Detection
    ✅ Menu dictionary: ${mainmenu}[configuration]
    ✅ UPPERCASE variables: HOST_IMAP_TEMPEMAIL → ${HOST_IMAP_TEMPEMAIL}
    ✅ LOCATOR_ prefix: LOCATOR_USERNAME → ${LOCATOR_USERNAME}
    ✅ Text values: label → label (ไม่ใส่ ${})
    """
    if not args_dict:
        return ""
    
    parts = []
    for k, v in args_dict.items():
        if k == 'assertion_columns': 
            continue

        val_str = None
        
        # ===== 🔧 FIXED: Smart Value Formatting =====
        if isinstance(v, str):
            v_str = str(v).strip()
            
            # Pattern 1: Menu dictionary - ${mainmenu}[configuration]
            menu_pattern = r'^(\$\{)?(mainmenu|submenu|menuname|homemenu)(\})?\[([^\]]+)\]$'
            menu_match = re.match(menu_pattern, v_str)
            
            if menu_match:
                dict_name = menu_match.group(2)
                dict_key = menu_match.group(4)
                val_str = f"${{{dict_name}}}[{dict_key}]"
            
            # Pattern 2: Already has ${...} or &{...} or @{...}
            elif re.match(r'^[$@&]\{.*\}$', v_str):
                val_str = v_str
            
            # Pattern 3: ${EMPTY} or boolean
            elif v_str == '${EMPTY}' or v_str.lower() in ['true', 'false']:
                val_str = v_str.capitalize() if v_str.lower() in ['true', 'false'] else v_str
            
            # Pattern 4: UPPERCASE_WITH_UNDERSCORE (likely a variable) ✅ NEW!
            elif re.match(r'^[A-Z][A-Z0-9_]*$', v_str):
                val_str = f"${{{v_str}}}"
            
            # Pattern 5: LOCATOR_ prefix
            elif v_str.startswith('LOCATOR_'):
                val_str = f"${{{v_str}}}"
            
            # Pattern 6: Text values (lowercase, mixed case, or numbers)
            else:
                val_str = v_str
        
        # Handle dict type (legacy)
        elif isinstance(v, dict) and 'name' in v:
            val_str = get_clean_locator_name(v['name'])
        
        # Handle boolean
        elif isinstance(v, bool):
            val_str = 'True' if v else 'False'
        
        elif v or v is False:
            val_str = str(v)
        else:
            continue
        
        if val_str is not None:
            parts.append(f"{k}={val_str}")
    
    # Use 4 spaces as separator (Robot Framework standard)
    full_str = "    ".join(parts)
    return full_str

# ===================================================================
# ===== 5. File System Utilities (Logic from crud_generator/manager.py)
# ===================================================================

def util_get_csv_headers(project_path, csv_filename):
    """
    Reads the headers (first row) from a CSV file in the datatest folder.
    (Logic moved from crud_generator/manager.py, made pure)
    
    Args:
        project_path (str): The absolute project path
        csv_filename (str): Name of the CSV file (e.g., 'login_data.csv')
    
    Returns:
        list: List of column headers, or empty list if file not found/error
    """
    if not project_path or not csv_filename:
        return []
    
    csv_path = os.path.join(
        project_path,
        'resources',
        'datatest',
        csv_filename
    )
    
    if not os.path.exists(csv_path):
        return []
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader, [])
            headers = [h.strip() for h in headers]
            return headers
    except Exception as e:
        print(f"Error reading CSV headers from {csv_filename}: {e}")
        return []

def scan_steps_for_variables(steps):
    """
    Scans a list of step dictionaries and extracts potential Robot Framework
    variables (e.g., ${var}, @{list}, &{dict}) used in their arguments.

    Args:
        steps (list): A list of step dictionaries, where each step has an 'args' key
                      containing a dictionary of argument names and values.

    Returns:
        list: A sorted list of unique potential variable names found (e.g., ['${username}', '${password}']).
    """
    potential_vars = set()
    variable_pattern = re.compile(r'([$@&]\{[^{}]+\})') # Pattern to find ${...}, @{...}, &{...}

    if not isinstance(steps, list):
        return []

    for step in steps:
        args_dict = step.get('args', {})
        if not isinstance(args_dict, dict):
            continue

        for arg_value in args_dict.values():
            if isinstance(arg_value, str):
                found_vars = variable_pattern.findall(arg_value)
                for var in found_vars:
                    # Basic validation: ensure it has content between {}
                    if len(var) > 3 and var != '${EMPTY}':
                         potential_vars.add(var)

    return sorted(list(potential_vars))

def generate_arg_name_from_locator(locator_name):
    """
    Generates a suggested Robot Framework argument variable name
    from a locator name.
    Example: LOCATOR_USER_NAME_INPUT -> ${user_name}
             BTN_SUBMIT -> ${submit}

    Args:
        locator_name (str): The name of the locator (e.g., "LOCATOR_USER_NAME_INPUT").

    Returns:
        str: The suggested variable name (e.g., "${user_name}"), or None if input is invalid.
    """
    if not locator_name or not isinstance(locator_name, str):
        return None

    # 1. Remove common prefixes/suffixes and variable syntax ${}
    clean_name = get_clean_locator_name(locator_name) # Use existing helper
    clean_name = clean_name.upper() # Ensure consistent casing for removal
    prefixes_suffixes = ['LOCATOR_', '_INPUT', '_TEXTAREA', '_SELECT', '_BUTTON', '_BTN', '_LINK', '_FIELD', '_DROPDOWN', '_RADIO', '_CHECKBOX', 'RADIO_', 'CHECKBOX_', 'BTN_']
    for item in prefixes_suffixes:
        if clean_name.startswith(item):
            clean_name = clean_name[len(item):]
        if clean_name.endswith(item):
             clean_name = clean_name[:-len(item)]

    # 2. Convert to lowercase and replace underscore with space temporarily
    clean_name = clean_name.lower().replace('_', ' ')

    # 3. Handle common abbreviations or specific words (optional refinement)
    #    e.g., 'pwd' -> 'password', 'usr' -> 'user'
    replacements = {'pwd': 'password', 'usr': 'user', 'num': 'number'}
    words = clean_name.split()
    cleaned_words = [replacements.get(word, word) for word in words]

    # 4. Join back with underscore and create variable format
    final_name = '_'.join(cleaned_words).strip('_')

    # Return None if the process results in an empty name
    if not final_name:
        return None

    return f"${{{final_name}}}"

def convert_json_path_to_robot_accessor(json_path):
    """
    Converts a JSON path string (dot or bracket notation) into
    Robot Framework dictionary/list access syntax.

    Examples:
        'data.items[0].id' -> '[data][items][0][id]'
        'data.name'         -> '[data][name]'
        '[0].value'         -> '[0][value]'
        'key'               -> '[key]'

    Args:
        json_path (str): The JSON path string.

    Returns:
        str: The Robot Framework accessor string, or an empty string if conversion fails.
    """
    if not isinstance(json_path, str) or not json_path.strip():
        return ''

    accessor = ''
    # Use regex to find keys (words) or array indices ([number])
    # Allows for paths starting with [index] or key.
    pattern = re.compile(r'\.?(\w+)|(\[\s*\d+\s*\])')
    matches = pattern.finditer(json_path)

    start_index = 0
    for match in matches:
        # Check if there was a gap before this match (could indicate invalid format)
        if match.start() != start_index and start_index != 0 :
             # Allow starting with '[' without a preceding dot
             if not (json_path[start_index] == '[' and start_index == 0):
                  print(f"Warning: Potentially invalid JSON path segment near index {start_index} in '{json_path}'")
                  # Depending on strictness, could return '' here

        key_match = match.group(1)
        index_match = match.group(2)

        if key_match:
            accessor += f"[{key_match}]"
        elif index_match:
            # Remove spaces within brackets for consistency
            accessor += f"[{index_match.strip().strip('[]')}]"

        start_index = match.end()

    # Check if the entire string was consumed
    if start_index != len(json_path):
         # Handle simple case: path is just a single key without dots/brackets
         if accessor == '' and re.match(r'^\w+$', json_path):
              return f"[{json_path}]"
         # Handle case where path starts with '[' but wasn't fully matched
         elif json_path.startswith('[') and accessor.startswith('['):
             pass # Looks okay, regex handled it
         else:
              print(f"Warning: JSON path '{json_path}' might not be fully converted. Result: '{accessor}'")
              # Fallback or error handling needed? For now, return what we have.

    # Handle case where input is just 'key'
    if not accessor and re.fullmatch(r'\w+', json_path):
         return f'[{json_path}]'

    return accessor

# ===================================================================
# ===== 7. Additional Keyword Factory Utilities (New Section)
# ===================================================================

def check_argument_usage(steps, arg_name):
    """
    Checks if a specific Robot Framework variable is used within the arguments of any step.

    Args:
        steps (list): A list of step dictionaries.
        arg_name (str): The variable name to check (e.g., "${username}").

    Returns:
        bool: True if the variable is found in any step's argument values, False otherwise.
    """
    if not isinstance(steps, list) or not arg_name:
        return False

    # Create a regex pattern to find the exact variable, potentially surrounded by other text
    # Need to escape special characters in the variable name itself for the regex
    escaped_arg_name = re.escape(arg_name)
    # Pattern looks for the variable as a whole word or at start/end, or within quotes/brackets
    # This is a basic check; more complex usage might need refinement
    usage_pattern = re.compile(r'(?<![\w$\{\[])' + escaped_arg_name + r'(?![\w}\]])')


    for step in steps:
        args_dict = step.get('args', {})
        if not isinstance(args_dict, dict):
            continue
        for arg_value in args_dict.values():
            if isinstance(arg_value, str):
                if usage_pattern.search(arg_value):
                    return True # Found usage in at least one step
    return False # Not found in any step

# --- Function to help with Rename Refactoring ---
def rename_argument_in_steps(steps, old_arg_name, new_arg_name):
    """
    Creates a *new* list of steps with occurrences of an old argument name
    replaced with a new argument name within step argument values.
    This performs a simple string replacement.

    Args:
        steps (list): The original list of step dictionaries.
        old_arg_name (str): The old variable name (e.g., "${old_user}").
        new_arg_name (str): The new variable name (e.g., "${username}").

    Returns:
        list: A new list of step dictionaries with replacements made.
              Returns the original list reference if no changes were needed or inputs invalid.
    """
    if not isinstance(steps, list) or not old_arg_name or not new_arg_name or old_arg_name == new_arg_name:
        return steps # Return original list if inputs invalid or no change

    import copy # Use deepcopy to avoid modifying original step dictionaries indirectly
    new_steps = copy.deepcopy(steps) # Work on a copy
    changed = False

    for step in new_steps:
        args_dict = step.get('args') # No need for default, deepcopy handled it
        if not isinstance(args_dict, dict):
            continue

        for arg_key, arg_value in args_dict.items():
            if isinstance(arg_value, str) and old_arg_name in arg_value:
                # Simple string replacement
                args_dict[arg_key] = arg_value.replace(old_arg_name, new_arg_name)
                changed = True

    # Return the new list only if changes were actually made
    return new_steps if changed else steps


# --- Function to help with Documentation Generation ---
def generate_basic_docstring(keyword_name, args_list, steps):
    """
    Generates a basic documentation string template based on arguments and output variables found in steps.

    Args:
        keyword_name (str): The name of the keyword.
        args_list (list): List of argument dictionaries [{'name': '...', 'default': '...'}].
        steps (list): List of step dictionaries to scan for output variables.

    Returns:
        str: A basic multi-line docstring template.
    """
    doc_lines = [f"{keyword_name}"] # Start with the keyword name itself
    doc_lines.append("")

    if args_list:
        doc_lines.append("Arguments:")
        for arg in args_list:
            default_str = f" (default=`{arg.get('default','')}`)" if arg.get('default') else ""
            doc_lines.append(f"    - `{arg.get('name', 'N/A')}`:{default_str}")
        doc_lines.append("")

    # Scan steps for output variables
    output_vars = []
    for step in steps:
        output_config = step.get('output_variable', {})
        if output_config.get('enabled') and output_config.get('name'):
            output_vars.append({
                'name': output_config['name'],
                'scope': output_config.get('scope', 'Test')
            })

    if output_vars:
        doc_lines.append("Outputs (Set Variable):")
        for out_var in output_vars:
            doc_lines.append(f"    - `${{{out_var.get('name', 'N/A')}}}` (Scope: {out_var.get('scope', 'N/A')})")
        doc_lines.append("")

    if len(doc_lines) <= 2: # Only name and blank line
        return f"{keyword_name}\n\n    [Documentation]    Documentation for this keyword." # Basic default

    # Add [Documentation] marker for the first line
    doc_lines.insert(1, "    [Documentation]    ")
    # Add continuation marker for subsequent lines
    for i in range(2, len(doc_lines)):
         # Add continuation only if line is not empty
         if doc_lines[i].strip():
              doc_lines[i] = f"    ...    {doc_lines[i]}"
         else:
              # Keep empty lines for spacing, but still add continuation marker
              doc_lines[i] = "    ..."


    # Reconstruct the docstring structure
    # This function just returns the string content, the calling function
    # needs to handle splitting and formatting for the RF file.
    # We return a single string with newlines for easy use in st.text_area
    return "\n".join(doc_lines[1:]) # Return starting from [Documentation] line

# --- Function to check if keyword exists in content ---
def keyword_exists_in_content(file_content, keyword_name):
    """
    Checks if a keyword with the exact given name exists in the provided Robot Framework file content.
    Uses the parse_robot_keywords utility.

    Args:
        file_content (str): The content of the .robot or .resource file.
        keyword_name (str): The exact name of the keyword to check for.

    Returns:
        bool: True if the keyword name is found, False otherwise.
    """
    if not file_content or not keyword_name:
        return False

    try:
        existing_keywords = parse_robot_keywords(file_content) # Use the parser from utils
        for kw in existing_keywords:
            if kw.get('name') == keyword_name:
                return True
        return False
    except Exception as e:
        print(f"Error checking for keyword '{keyword_name}': {e}")
        return False # Assume not found if parsing fails

# ===================================================================
# ===== End New Section =====
# ===================================================================

def format_args_as_multiline_string(args_dict):
    """
    ✅ CUSTOM: locator แยกแถว, args อื่นคั่นด้วย |
    """
    if not args_dict:
        return ""

    locator_args = []
    other_args = []
    
    # Define argument order
    arg_order = sorted(args_dict.keys(), key=lambda x: (
        0 if 'locator' in x.lower() else
        1 if x == 'main_menu' else
        2 if x == 'submenu' else
        3 if x in ['exp_value', 'value'] else
        4
    ))

    # Parse arguments
    for k in arg_order:
        v_original = args_dict[k]
        value_to_format = v_original
        
        if v_original is None or v_original == '':
            value_to_format = '${EMPTY}'
            if k.lower() in ['menu_locator', 'main_menu', 'submenu'] and v_original == '':
                continue

        formatted_value_str = _format_value_for_robot(value_to_format)
        final_output_value = formatted_value_str
        
        if isinstance(v_original, bool):
            final_output_value = '${True}' if v_original else '${False}'
        elif formatted_value_str == 'True': 
            final_output_value = '${True}'
        elif formatted_value_str == 'False': 
            final_output_value = '${False}'

        if final_output_value is not None:
            boolean_flags_can_omit_name = [
                'is_switch_type', 'is_checkbox_type', 'is_ant_design',
                'ignorcase', 'is_skipfield'
            ]
            omit_arg_name = (k.lower() in boolean_flags_can_omit_name and
                           final_output_value in ['${True}', '${False}'])

            is_locator = (k.lower() == 'locator_field')
            
            if omit_arg_name:
                arg_str = final_output_value
            else:
                arg_str = f"{k}={final_output_value}"
            
            if is_locator:
                locator_args.append(arg_str)
            else:
                other_args.append(arg_str)

    if not locator_args and not other_args:
        return ""

    # Build HTML
    html = '<div style="margin: 6px 0; line-height: 1.8;">\n'
    
    # Locator field - แถวบน
    if locator_args:
        for locator in locator_args:
            html += f'  <div style="font-family: \'SF Mono\', Monaco, monospace; font-size: 0.82rem; color: #79C0FF; font-weight: 700; margin-bottom: 4px;">{locator}</div>\n'
    
    # Other args - คั่นด้วย |
    if other_args:
        args_line = ' | '.join(other_args)
        html += f'  <div style="font-family: \'SF Mono\', Monaco, monospace; font-size: 0.82rem; color: #56d364; font-weight: 400;">{args_line}</div>\n'
    
    html += '</div>'
    
    return html