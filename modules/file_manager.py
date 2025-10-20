"""
File Management Module
Handles all file operations: scanning, reading, writing Robot Framework files
"""
import os
import re
import streamlit as st
import pandas as pd
from datetime import datetime 

def scan_robot_project(path):
    """Scan Robot Framework project structure"""
    if not path or not os.path.exists(path):
        return {}

    structure = {
        'root': path,
        'folders': {},
        'robot_files': [],
        'csv_files': []
    }

    # 1. แก้ไข: ลบ 'output' ออก และหาเฉพาะโฟลเดอร์หลักที่ต้องการ
    expected_folders = ['pageobjects', 'resources', 'testsuite']

    for folder in expected_folders:
        folder_path = os.path.join(path, folder)
        if os.path.exists(folder_path):
            structure['folders'][folder] = folder_path

    # 2. เพิ่ม: ค้นหาโฟลเดอร์ services และ datatest ที่ซ้อนอยู่ข้างใน
    resources_path = structure['folders'].get('resources')
    if resources_path:
        nested_folders_to_find = ['services', 'datatest']
        for nested_folder in nested_folders_to_find:
            nested_folder_path = os.path.join(resources_path, nested_folder)
            if os.path.exists(nested_folder_path):
                # ใช้ key ที่แสดงถึงการซ้อนกัน เช่น 'resources/services'
                key = os.path.join('resources', nested_folder).replace(os.sep, '/')
                structure['folders'][key] = nested_folder_path

    for root, dirs, files in os.walk(path):
        # 3. เพิ่ม: สั่งให้ข้ามโฟลเดอร์ output และ __pycache__ ระหว่างการค้นหาไฟล์
        if 'output' in dirs:
            dirs.remove('output')
        if '__pycache__' in dirs:
            dirs.remove('__pycache__')

        for file in files:
            rel_path = os.path.relpath(os.path.join(root, file), path)
            if file.endswith('.robot') or file.endswith('.resource'):
                structure['robot_files'].append(rel_path)

            elif file.endswith('.csv'):
                structure['csv_files'].append(rel_path)

    return structure

def create_new_robot_file(file_path, content):
    """Create new Robot Framework file with content"""
    try:
        file_path = os.path.abspath(file_path)

        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return True
        
    except PermissionError:
        st.error(f"Permission denied: Cannot write to {file_path}")
        return False
    except Exception as e:
        st.error(f"Error creating file: {str(e)}")
        return False

def read_robot_variables_from_content(content: str):
    """Reads variables from a string content instead of a file path."""
    try:
        variables_match = re.search(r'\*\*\* Variables \*\*\*(.*?)(?=\*\*\*|$)', content, re.DOTALL | re.IGNORECASE)
        if not variables_match:
            st.warning("Could not find a '*** Variables ***' section in the content.")
            return []

        variables_content = variables_match.group(1)
        locators = []
        variable_pattern = re.compile(r'^\s*\$\{([^}]+)\}\s+(.+?)\s*$', re.MULTILINE)

        for match in variable_pattern.finditer(variables_content):
            variable_name = match.group(1).strip()
            if variable_name.upper().startswith('LOCATOR_'):
                locators.append({
                    'name': variable_name,
                    'value': match.group(2).strip()
                })
        
        if not locators:
            st.warning("No variables starting with `LOCATOR_` found.")
        return locators
    except Exception as e:
        st.error(f"An error occurred while parsing content: {str(e)}")
        return []

def parse_robot_keywords(file_content: str):
    """
    [FINAL FIX] Parses keyword definitions with a highly robust logic for multi-line arguments,
    correctly handling blank lines and comments within the [Arguments] block.
    """
    keywords_list = []
    # Find the content from *** Keywords *** to the end of the file or next section
    keywords_section_match = re.search(r'\*\*\* Keywords \*\*\*(.*)', file_content, re.DOTALL | re.IGNORECASE)
    
    if not keywords_section_match:
        return []

    keywords_content = keywords_section_match.group(1)
    
    # Split content into individual keyword blocks. A new keyword starts at the beginning of a line.
    keyword_blocks = re.split(r'\n(?=\S)', keywords_content.strip())

    for block in keyword_blocks:
        if not block.strip():
            continue

        lines = block.strip().split('\n')
        keyword_name = lines[0].strip()
        
        # Skip comments, settings, or control structures mistaken for keywords
        if not keyword_name or keyword_name.startswith(('#', '[', '...', 'FOR', 'IF', 'ELSE')):
            continue

        keyword_body_lines = lines[1:]
        
        doc_list = [line.split(']', 1)[1].strip() for line in keyword_body_lines if line.strip().lower().startswith('[documentation]')]
        doc = " ".join(doc_list) if doc_list else "No documentation available."

        args = []
        # --- [🎯 FINAL FIX: More robust continuation logic] ---
        # 1. Find the starting line for [Arguments]
        arg_start_index = -1
        for i, line in enumerate(keyword_body_lines):
            if line.strip().lower().startswith('[arguments]'):
                arg_start_index = i
                break
        
        if arg_start_index != -1:
            # 2. Extract arguments from the first line
            full_args_str = keyword_body_lines[arg_start_index].split(']', 1)[1].strip()
            
            # 3. Scan subsequent lines for continuations, IGNORING blank lines/comments
            for line in keyword_body_lines[arg_start_index + 1:]:
                stripped_line = line.strip()
                
                # If it's a continuation line, add its content
                if stripped_line.startswith('...'):
                    full_args_str += "  " + stripped_line[3:].strip()
                # If it's a blank line or a comment, just skip it and continue looking
                elif not stripped_line or stripped_line.startswith('#'):
                    continue
                # If it's anything else, it's the start of the keyword body, so stop.
                else:
                    break
            
            # 4. Use the proven logic to parse the final, combined argument string
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
        # --- [END OF FINAL FIX] ---
            
        keywords_list.append({"name": keyword_name, "args": args, "doc": doc})

    return keywords_list

def save_df_to_csv(project_path, file_name, df):
    """Saves a pandas DataFrame to a CSV file inside the 'datatest' folder."""
    if not project_path or not st.session_state.project_structure.get('folders', {}).get('resources/datatest'):
        st.error("Project path is not set or 'datatest' folder not found inside 'resources'.")
        return False
    
    # Construct the full path
    datatest_path = st.session_state.project_structure['folders']['resources/datatest']
    full_path = os.path.join(datatest_path, file_name)

    try:
        df.to_csv(full_path, index=False, encoding='utf-8')
        return True
    except Exception as e:
        st.error(f"Failed to save CSV file: {e}")
        return False


def append_robot_content_intelligently(file_path, variables_code=None, keywords_code=None):
    """
    Intelligently appends variables and keywords to a .robot or .resource file.
    - Creates sections (*** Variables ***, *** Keywords ***) if they don't exist.
    - Checks for duplicate variables/keywords before appending.
    - Creates a generator block with markers ONCE.
    - Appends new content inside the existing generator block.
    (Version 2.0 - Simplified and Robust Logic)
    """
    if not os.path.exists(file_path):
        return False, f"File not found: {file_path}"
    if not variables_code and not keywords_code:
        return True, "Nothing to append."

    try:
        with open(file_path, 'r+', encoding='utf-8') as f:
            content = f.read()
            original_content = content

            # --- Block Markers ---
            start_marker = "# --- START: Generated by Robot Framework Code Generator ---"
            end_marker = "# ---  END: Generated by Robot Framework Code Generator  ---"
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # --- Helper Function to process a section ---
            def process_section(current_content, section_name, code_to_add, is_keyword):
                # 1. Ensure the section exists
                if section_name not in current_content:
                    current_content += f"\n\n{section_name}\n"

                # 2. Find the section's boundaries
                section_pattern = re.compile(rf'({re.escape(section_name)}.*?)(?=\n\*\*\*|$)', re.DOTALL | re.IGNORECASE)
                match = section_pattern.search(current_content)
                if not match:
                    # This should not happen if step 1 works, but as a fallback
                    return current_content, "Could not find or create section."

                section_text = match.group(1)

                # 3. Check for duplicates within the section
                lines_to_add = [line for line in code_to_add.strip().splitlines() if line.strip()]
                new_content_to_insert = []
                
                for line in lines_to_add:
                    check_str = line.strip()
                    if is_keyword:
                        # For keywords, only check the name (the first line)
                        check_str = lines_to_add[0].strip()
                    
                    # Check if the exact line or keyword name already exists
                    if re.search(fr'^\s*{re.escape(check_str)}\s*($|\s{{2,}})', section_text, re.MULTILINE):
                        continue # Skip if already exists
                    new_content_to_insert.append(line)

                if is_keyword and not new_content_to_insert:
                     return current_content, f"⚠️ Keyword '{lines_to_add[0].strip()}' already exists. No changes made."

                if not new_content_to_insert:
                    return current_content, "⚠️ All content already exists. No changes made."

                final_code_str = "\n".join(new_content_to_insert)
                if is_keyword:
                    final_code_str = "\n" + final_code_str # Add extra space before keyword

                # 4. Find the generator block's end marker within the section
                end_marker_pos = section_text.rfind(end_marker)

                if end_marker_pos != -1:
                    # Block exists: insert content before the end marker
                    insertion_point = match.start(1) + end_marker_pos
                    current_content = current_content[:insertion_point] + final_code_str + "\n" + current_content[insertion_point:]
                else:
                    # Block does not exist: create it and append to the section
                    new_block = f"\n{start_marker}\n# Created: {timestamp}\n{final_code_str.strip()}\n{end_marker}\n"
                    # Append new block at the end of the section
                    insertion_point = match.end(1)
                    current_content = current_content[:insertion_point] + new_block + current_content[insertion_point:]
                
                return current_content, f"✅ Successfully updated {os.path.basename(file_path)}"

            # --- Process Variables ---
            message = "No changes made."
            if variables_code:
                content, message = process_section(content, "*** Variables ***", variables_code, is_keyword=False)

            # --- Process Keywords ---
            if keywords_code:
                content, message = process_section(content, "*** Keywords ***", keywords_code, is_keyword=True)

            # --- Write back to file if changes were made ---
            if content != original_content:
                f.seek(0)
                f.write(content)
                f.truncate()
                return True, message
            else:
                return True, message

    except FileNotFoundError:
        return False, f"File not found: {file_path}"
    except Exception as e:
        return False, f"An error occurred: {str(e)}"


def append_to_api_base(file_path, variable_line, keyword_line):
    """
    [FINAL FIX] Prevents nested blocks and duplicate end markers.
    """
    try:
        with open(file_path, 'r+', encoding='utf-8') as f:
            content = f.read()
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            content_changed = False

            start_marker = "# --- START: Generated by Robot Framework Code Generator ---"
            end_marker = "# ---  END: Generated by Robot Framework Code Generator  ---"

            # --- 1. Handle *** Variables *** Section ---
            var_name_to_check = variable_line.strip().split('}')[0] + '}'
            vars_section_name = "*** Variables ***"
            vars_pattern = re.compile(rf'({re.escape(vars_section_name)}.*?)(?=\n\*\*\*|$)', re.DOTALL | re.IGNORECASE)
            vars_match = vars_pattern.search(content)

            if not vars_match:
                new_block = (f"\n\n{vars_section_name}\n{start_marker}\n# Created: {timestamp}\n"
                             f"{variable_line.strip()}\n{end_marker}\n")
                content += new_block
                content_changed = True
            else:
                section_text = vars_match.group(1)
                if var_name_to_check not in section_text:
                    end_marker_pos = section_text.rfind(end_marker)
                    if end_marker_pos != -1:
                        insertion_point = vars_match.start(1) + end_marker_pos
                        content = f"{content[:insertion_point]}{variable_line.strip()}\n{content[insertion_point:]}"
                    else:
                        new_block = (f"\n{start_marker}\n# Created: {timestamp}\n"
                                     f"{variable_line.strip()}\n{end_marker}\n")
                        new_section_text = section_text.rstrip() + new_block
                        content = content.replace(section_text, new_section_text, 1)
                    content_changed = True

            # --- 2. Handle 'Set Path Request URL' Keyword (SIMPLIFIED & FIXED) ---
            target_keyword_name = "Set Path Request URL"
            
            # Prepare the line with correct indentation (4 spaces)
            new_line = f"    {keyword_line.strip()}"

            # Find the keyword block
            kw_pattern = re.compile(rf'(^{re.escape(target_keyword_name)}.*?)(?=\n^\S|\Z)', re.DOTALL | re.MULTILINE)
            kw_match = kw_pattern.search(content)
            
            if not kw_match:
                return False, f"Keyword '{target_keyword_name}' not found."

            keyword_block = kw_match.group(1)
            keyword_start = kw_match.start(1)
            keyword_end = kw_match.end(1)
            
            # Check if the exact line already exists (ignore extra spaces)
            if keyword_line.strip() in keyword_block.replace('    ', ''):
                # Line already exists, skip
                pass
            else:
                # Find the generated block within this keyword
                indented_start = f"    {start_marker}"
                indented_end = f"    {end_marker}"
                
                start_pos = keyword_block.find(indented_start)
                end_pos = keyword_block.find(indented_end)
                
                if start_pos != -1 and end_pos != -1:
                    # Block exists - insert new line before the END marker
                    # Calculate absolute position in the content
                    abs_end_marker_pos = keyword_start + end_pos
                    
                    # Insert the new line
                    content = (
                        content[:abs_end_marker_pos] + 
                        new_line + '\n' + 
                        content[abs_end_marker_pos:]
                    )
                    content_changed = True
                else:
                    # No block exists - create a new one at the end of keyword
                    new_block = (
                        f"\n{indented_start}\n"
                        f"    # Created: {timestamp}\n"
                        f"{new_line}\n"
                        f"{indented_end}\n"
                    )
                    
                    # Insert the block at the end of the keyword
                    content = (
                        content[:keyword_end] + 
                        new_block + 
                        content[keyword_end:]
                    )
                    content_changed = True

            # --- 3. Write changes to file ---
            if content_changed:
                f.seek(0)
                f.write(content)
                f.truncate()
                return True, f"✅ Successfully updated {os.path.basename(file_path)}"
            else:
                return True, "⚠️ Content already exists. No changes made."

    except FileNotFoundError:
        return False, f"Error: {os.path.basename(file_path)} not found."
    except Exception as e:
        return False, f"An error occurred: {e}"

# ===================================================================
# ===== 🎯 START: NEW FUNCTION FOR DATASOURCE PARSING (V.2) =====
# ===================================================================

def parse_data_sources_from_resource(content: str):
    """
    Parses a datasources.resource file content to extract CSV paths.
    V.7: Fixed path cleaning and proper filename extraction.
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
                    col_name = col_var_match.group(1).replace('_col', '')

                    # --- ✅ FIXED: Proper path cleaning and filename extraction ---
                    csv_file_name = "NOT_FOUND"
                    if csv_path_var_name in variables:
                        full_path_value = variables[csv_path_var_name]
                        # Example: ${CURDIR}${/}datatest${/}login_data.csv
                        
                        # Step 1: Remove all Robot Framework variables
                        clean_path = full_path_value
                        clean_path = re.sub(r'\$\{CURDIR\}', '', clean_path)
                        clean_path = re.sub(r'\$\{/\}', '/', clean_path)
                        clean_path = re.sub(r'\$\{[^}]+\}', '', clean_path)  # Remove any other ${...}
                        
                        # Step 2: Clean up the path (remove leading/trailing slashes and spaces)
                        clean_path = clean_path.strip().strip('/')
                        # clean_path should now be: datatest/login_data.csv
                        
                        # Step 3: Extract only the filename (last part after /)
                        if '/' in clean_path:
                            csv_file_name = clean_path.split('/')[-1]
                        else:
                            csv_file_name = clean_path
                        
                        # Step 4: Extra safety - ensure .csv extension and clean any trailing chars
                        csv_file_name = csv_file_name.strip()
                        if not csv_file_name.endswith('.csv'):
                            # Try to find .csv in the string
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
        st.error(f"Error parsing datasources file: {e}")
        return []

# ===================================================================
# ===== 🎯 END: NEW FUNCTION =====
# ===================================================================