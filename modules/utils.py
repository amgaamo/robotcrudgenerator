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
    Helper to format a single step object into a string with its keyword and named arguments.
    (Moved from test_flow_manager.py)
    """
    keyword = step.get('keyword', '')
    args = step.get('args', {})

    def format_value(arg_name, arg_value):
        if arg_value == "": return "${EMPTY}"
        if arg_value is None: return None
        is_locator = any(s in arg_name.lower() for s in ['locator', 'field', 'button', 'element', 'menu', 'theader', 'tbody'])
        if isinstance(arg_value, str) and arg_value.startswith('${') and arg_value.endswith('}'):
            return arg_value
        if is_locator:
            return f"${{{arg_value}}}"
        if isinstance(arg_value, bool):
            return str(arg_value).lower()
        return arg_value

    if keyword.strip() == 'Verify Result of data table':
        fixed_args = {}
        col_args = {}
        for k, v in args.items():
            if k.startswith('col.') or k.startswith('assert.') or k.startswith('expected.'):
                col_args[k] = v
            else:
                fixed_args[k] = v

        first_line_parts = [keyword]
        for name, value in fixed_args.items():
             robot_name = 'ignore_case' if name == 'ignorcase' else name
             formatted_val = format_value(name, value)
             if formatted_val is not None:
                  first_line_parts.append(f"{robot_name}={formatted_val}")

        column_lines = []
        column_ids = sorted(list(set([k.split('.')[1] for k in col_args if k.startswith('col.')])))

        for col_id in column_ids:
            line_parts = ["..."]
            col_name = f"col.{col_id}"
            assert_name = f"assert.{col_id}"
            expected_name = f"expected.{col_id}"

            val = format_value(col_name, col_args.get(col_name))
            if val is not None: line_parts.append(f"{col_name}={val}")
            val = format_value(assert_name, col_args.get(assert_name))
            if val is not None: line_parts.append(f"{assert_name}={val}")
            val = format_value(expected_name, col_args.get(expected_name))
            if val is not None: line_parts.append(f"{expected_name}={val}")

            column_lines.append("    ".join(line_parts))

        final_output = "    ".join(first_line_parts)
        if column_lines:
            final_output += "\n" + "\n".join([f"    {line}" for line in column_lines])
        return final_output

    line_parts = [keyword]
    for arg_name, arg_value in args.items():
        formatted_value = format_value(arg_name, arg_value)
        if formatted_value is not None:
             line_parts.append(f"{arg_name}={formatted_value}")

    return "    ".join(line_parts)


def format_args_as_string(args_dict):
    """
    Helper to format arguments as a simple string for st.caption
    (Moved from ui_common.py)
    """
    if not args_dict:
        return ""
    parts = []
    for k, v in args_dict.items():
        if k == 'assertion_columns': 
            continue

        if isinstance(v, dict) and 'name' in v:
            # Relies on get_clean_locator_name, which is now in this file
            val_str = get_clean_locator_name(v['name'])
        elif v or v is False:
            val_str = str(v)
        else:
            continue

        parts.append(f"{k}={val_str}")

    full_str = ", ".join(parts)
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
                    if len(var) > 3:
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