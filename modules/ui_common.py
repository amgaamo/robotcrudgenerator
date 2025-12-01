# modules/ui_common.py
"""
Common UI Utility Functions
Contains shared UI components and helper functions used across different modules.
"""
import streamlit as st
import uuid
import json
import numpy as n
import re
from pathlib import Path
from .utils import util_get_csv_headers, get_clean_locator_name, format_args_as_string, util_get_csv_first_column_values
from .keyword_categorizer import categorize_keywords

# --- Argument Preset Loading (Moved from ui_test_flow.py) ---
def load_argument_presets():
    """Load argument presets from JSON file"""
    try:
        # Adjusted path to find assets folder relative to this file's parent
        preset_path = Path(__file__).parent.parent / "assets" / "argument_presets.json"
        with open(preset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('presets', {}), data.get('patterns', {})
    except FileNotFoundError:
        st.warning("⚠️ argument_presets.json not found. Using default text inputs.")
        return {}, {}
    except json.JSONDecodeError:
        st.error("❌ Error parsing argument_presets.json. Check JSON syntax.")
        return {}, {}

# Load presets at module level
ARGUMENT_PRESETS, ARGUMENT_PATTERNS = load_argument_presets()

ARGUMENT_PRESETS['button_name'] = {
    "type": "select_or_input",
    "options": ["OK", "Yes", "No", "Cancel", "Save", "Confirm", "Close", "Submit", "Back", "Next"],
    "label": "🔘 Button Name (Text)",
    "placeholder": "Enter button text (e.g., OK)"
}

# --- Argument Input Rendering Functions (Moved from ui_test_flow.py) ---

def render_preset_input(arg_name, config, default_value, step_id_or_key_prefix, ws_state=None):
    """
    Render input based on preset configuration
    (Modified to accept ws_state parameter to fix TypeError)
    """
    input_type = config.get('type')
    label = config.get('label', f"📝 {arg_name}")
    key_base = step_id_or_key_prefix    # Use prefix for unique keys

    if input_type == "boolean":
        default_bool = default_value.lower() == 'true' if isinstance(default_value, str) else bool(default_value)
        # Use config default if default_value is None or empty string
        if default_value is None or default_value == '':
             default_bool = config.get('default', 'false').lower() == 'true'

        result = st.checkbox(
            label,
            value=default_bool,
            key=key_base
        )
        # Always return string 'true' or 'false'
        return 'true' if result else 'false'

    elif input_type == "select":
        options = config.get('options', [])
        default_index = 0
        try:
            if default_value and default_value in options:
                default_index = options.index(default_value)
        except ValueError:
             default_index = 0 # Fallback if value not in options

        return st.selectbox(
            label,
            options,
            index=default_index,
            key=key_base
        )

    elif input_type == "select_or_input":
        options = config.get('options', [])[:] # Make a copy
        allow_custom = config.get('allow_custom', True)

        # (ส่วน inject locator ถูกลบออกแล้ว)

        if allow_custom:
            display_options = options + ["📝 Other (custom)"]
            select_key = f"{key_base}_select"
            custom_input_key = f"{key_base}_custom"

            # Determine default index and initial custom value
            default_index = 0
            initial_custom_value = ""
            if default_value:
                try:
                    # === FIX: ต้องค้นหาใน display_options ===
                    default_index = display_options.index(default_value)
                except ValueError:
                    default_index = len(options) # Select "Other"
                    initial_custom_value = default_value

            # Set initial state for custom input if not set
            if custom_input_key not in st.session_state:
                st.session_state[custom_input_key] = initial_custom_value

            selected = st.selectbox(
                label,
                display_options,
                index=default_index,
                key=select_key
            )

            if selected == "📝 Other (custom)":
                st.text_input(
                    f"✏️ Custom {arg_name}",
                    key=custom_input_key,
                    placeholder=config.get('placeholder', 'Enter custom value')
                )
                return st.session_state.get(custom_input_key, "")
            elif selected == "--- Locators ---": # Should not happen now
                 return st.session_state.get(select_key, "")
            else:
                if st.session_state.get(custom_input_key):
                     st.session_state[custom_input_key] = ""
                return selected
        else: # Select only (no custom)
             options = config.get('options', []) # ดึง options มาใหม่
             default_index = 0
             try:
                 if default_value and default_value in options:
                     default_index = options.index(default_value)
             except ValueError:
                 default_index = 0
             return st.selectbox(
                 label,
                 options,
                 index=default_index,
                 key=key_base
             )
    else: # Fallback to text input
         return st.text_input(label, value=str(default_value) if default_value is not None else "", key=key_base)


def render_pattern_input(arg_name, config, default_value, step_id_or_key_prefix):
    """
    Render input based on pattern matching (username, password, etc.)
    (Modified to accept a unique key prefix)
    """
    input_type = config.get('type', 'text')
    label = config.get('label', f"📝 {arg_name}")
    placeholder = config.get('placeholder', '')
    key = step_id_or_key_prefix   # Use prefix for unique key

    if input_type == "password":
        return st.text_input(
            label,
            value=default_value,
            type="password",
            key=key,
            placeholder=placeholder
        )
    else: # Default is text
        suggestions = config.get('suggestions', [])
        help_text = config.get('help', '')

        if suggestions:
            help_text += f" 💡 Suggestions: {', '.join(suggestions)}"
            effective_placeholder = placeholder or f"e.g., {suggestions[0]}"
        else:
             effective_placeholder = placeholder

        return st.text_input(
            label,
            value=default_value,
            key=key,
            placeholder=effective_placeholder,
            help=help_text.strip() or None # Only show help if there's content
        )


def render_argument_input(arg_info, ws_state, unique_key_prefix, current_value=None, selected_kw_name=None):
    """
    Smart argument input renderer with priority.
    (MODIFIED V7 handles menu_locator, main_menu, submenu based on selected_kw_name)
    """
    arg_name = arg_info.get('name')
    default_value = current_value if current_value is not None else arg_info.get('default', '')
    arg_name_lower = arg_name.lower() # ชื่อ Argument ที่ถูก Clean แล้ว
    kw_name_lower = str(selected_kw_name).lower() # ชื่อ Keyword ที่เลือก

    # === START: NEW LOGIC (V7) ===

    menu_locs = ws_state.get('menu_locators', {})
    main_menu_dict = menu_locs.get('mainmenu', {}).get('value', {})
    sub_menu_dict = menu_locs.get('submenu', {}).get('value', {})
    main_menu_options = [''] + sorted(list(main_menu_dict.keys()))
    sub_menu_options = [''] + sorted(list(sub_menu_dict.keys()))

    # --- Case 1: Keyword "Go to MENU name" and Argument "menu_locator" ---
    if 'go to menu name' in kw_name_lower and arg_name_lower == 'menu_locator':
        st.markdown(f"**🎯 {arg_name} (Select Main Menu)**") # Custom label

        # Parse current value (e.g., "${mainmenu}[config]")
        current_main_key = ''
        if default_value:
            main_match = re.search(r"\${mainmenu}\[(.*?)\]", default_value)
            if main_match: current_main_key = main_match.group(1)

        try: main_index = main_menu_options.index(current_main_key)
        except ValueError: main_index = 0

        selected_main = st.selectbox(
            "Main Menu", main_menu_options, index=main_index,
            key=f"{unique_key_prefix}_main_menu_select", # Key สำหรับ main menu
            format_func=get_clean_locator_name
        )
        # Return value in correct format
        return f"${{mainmenu}}[{selected_main}]" if selected_main else ""

    # --- Case 2: Keyword "Go to SUBMENU name" and Argument "main_menu" ---
    elif 'go to submenu name' in kw_name_lower and arg_name_lower == 'main_menu':
        st.markdown(f"**🎯 {arg_name}**") # Standard label

        # default_value is the key (e.g., "configuration")
        try: main_index = main_menu_options.index(default_value)
        except ValueError: main_index = 0

        selected_main_key = st.selectbox(
            "Main Menu", main_menu_options, index=main_index,
            key=f"{unique_key_prefix}_main_menu_select", # Key สำหรับ main menu
            format_func=get_clean_locator_name
        )
        return selected_main_key # Return the key

    # --- Case 3: Keyword "Go to SUBMENU name" and Argument "submenu" ---
    elif 'go to submenu name' in kw_name_lower and arg_name_lower == 'submenu':
        st.markdown(f"**🎯 {arg_name}**") # Standard label

        # default_value is the key (e.g., "companyMgt")
        try: sub_index = sub_menu_options.index(default_value)
        except ValueError: sub_index = 0

        selected_sub_key = st.selectbox(
            "Sub Menu", sub_menu_options, index=sub_index,
            key=f"{unique_key_prefix}_sub_menu_select", # Key สำหรับ sub menu
            format_func=get_clean_locator_name
        )
        return selected_sub_key # Return the key

    # --- Case 4: Other Locator Arguments (Buttons, Fields, etc.) ---
    is_locator_arg_other = any(s in arg_name_lower for s in ['locator', 'theader', 'tbody'])

    if is_locator_arg_other:
        st.markdown(f"**🎯 {arg_name}**")
        
        # 1. เตรียมข้อมูล Locators และจัดกลุ่มตาม Page
        all_locators = ws_state.get('locators', [])
        common_vars = ws_state.get('common_variables', [])
        menu_block_names = ['homemenu', 'mainmenu', 'submenu', 'menuname']
        
        pages_dict = {}
        
        for loc in all_locators:
            loc_name = loc.get('name', '')
            page_name = loc.get('page_name', 'Other') # ถ้าไม่มี page_name ให้เป็น Other
            
            if loc_name.lower() in menu_block_names: continue # ข้าม Menu Variables
            
            if page_name not in pages_dict:
                pages_dict[page_name] = []
            pages_dict[page_name].append(loc_name)
        
        if common_vars:
             pages_dict['Global Variables'] = [var.get('name', '') for var in common_vars if var.get('name')]
        
        # 2. จัดการค่า Default (ถ้ามีค่าเดิมอยู่ ต้องหาว่าอยู่ Page ไหน)
        effective_default = '' if default_value == '${EMPTY}' else default_value
        # ลบ ${} ออกถ้ามี เพื่อใช้ค้นหาใน list
        clean_default = get_clean_locator_name(effective_default)
        
        default_page = ''
        if clean_default:
            for page, locs in pages_dict.items():
                if clean_default in locs:
                    default_page = page
                    break
        
        # 3. สร้าง Dropdown เลือก Page
        page_options = [''] + sorted(pages_dict.keys())
        try:
            default_page_index = page_options.index(default_page) if default_page else 0
        except ValueError:
            default_page_index = 0
            
        selected_page = st.selectbox(
            "📄 Step 1: Select Page",
            options=page_options,
            index=default_page_index,
            key=f"{unique_key_prefix}_page_select",
            help="Filter locators by page"
        )
        
        # 4. สร้าง Dropdown เลือก Locator (กรองตาม Page ที่เลือก)
        locator_options = ['']
        if selected_page:
            page_locators = pages_dict.get(selected_page, [])
            # เรียงลำดับตามชื่อ
            locator_options = [''] + sorted(page_locators)
            st.caption(f"ℹ️ Found {len(locator_options)-1} locators in **{selected_page}**")
        else:
            st.caption("ℹ️ Please select a page first")
            
        # หา Index ของ Locator เดิม
        try:
            loc_index = locator_options.index(clean_default) if clean_default in locator_options else 0
        except ValueError:
            loc_index = 0

        selected_locator = st.selectbox(
            "🔍 Step 2: Select Locator",
            options=locator_options,
            index=loc_index,
            key=f"{unique_key_prefix}_locator_select",
            format_func=get_clean_locator_name,
            disabled=(not selected_page)
        )
        
        return selected_locator

    # === END: NEW LOGIC (V7) ===

    # Priority 2: Check Presets
    if arg_name in ARGUMENT_PRESETS:
        return render_preset_input(
            arg_name, ARGUMENT_PRESETS[arg_name], default_value,
            unique_key_prefix, ws_state=ws_state # Pass ws_state
        )

    # Priority 3: Check Patterns
    arg_lower_pattern = arg_name.lower() # Use separate var if needed
    for pattern_key, pattern_config in ARGUMENT_PATTERNS.items():
        if pattern_key in arg_lower_pattern:
            return render_pattern_input(arg_name, pattern_config, default_value, unique_key_prefix)


    # Priority 4: Default Text Input
    return st.text_input(
        f"📝 {arg_name}",
        value=str(default_value) if default_value is not None else "",
        key=f"{unique_key_prefix}_default_text",
        placeholder="Enter value or ${VARIABLE}"
    )


# --- Verify Table UI Functions (Moved from ui_test_flow.py) ---
def _parse_args_for_verify_ui(args):
    """Helper to parse existing flat args into structured data for the UI."""
    assertions = []
    # Find all unique column identifiers from 'col.*' keys
    col_keys = sorted([k for k in args if k.startswith('col.')])
    for col_key in col_keys:
        column_id = col_key[4:] # Get the part after 'col.'
        if not column_id: continue
        assertions.append({
            'id': column_id, # Use column name as ID
            'col_value': args.get(col_key, column_id), # Header name
            'assert_value': args.get(f'assert.{column_id}', 'equal'), # Assertion type
            'expected_value': args.get(f'expected.{column_id}', '') # Expected value
        })
    return assertions

def render_verify_table_arguments_for_edit_mode(ws_state, unique_context_id, current_args={}):
    """
    Renders a special UI for the 'Verify Result of data table' keyword in EDIT mode.
    Manages dynamic column assertions and returns a dictionary of all arguments.
    """
    state_key = f"verify_table_assertions_{unique_context_id}"

    # Initialize state from current arguments if not already set
    if state_key not in st.session_state:
        st.session_state[state_key] = _parse_args_for_verify_ui(current_args)

    assertions = st.session_state[state_key]
    final_args = {} # Dictionary to build the flat args

    # --- 1. Render Fixed Arguments ---
    st.markdown("**Table Locators & Options**")
    fixed_arg_defs = [
        {'name': 'theader', 'default': ''},
        {'name': 'tbody', 'default': ''},
        {'name': 'rowdata', 'default': 'all'}, # Default 'all' might need adjustment
        {'name': 'ignorcase', 'default': 'true'} # Note: Robot uses ignore_case
    ]
    with st.container(border=True):
        grid = st.columns(2)
        i = 0
        for arg_info in fixed_arg_defs:
            with grid[i % 2]:
                arg_name = arg_info['name']
                # Correct arg name if needed (e.g., ignorcase -> ignore_case)
                robot_arg_name = 'ignore_case' if arg_name == 'ignorcase' else arg_name
                # Use current_args.get() with the CORRECT robot name
                current_val = current_args.get(robot_arg_name, arg_info.get('default', ''))
                # Render using the original name for display consistency
                final_args[robot_arg_name] = render_argument_input(
                    {'name': arg_name, 'default': arg_info['default']}, # Pass original name to renderer
                    ws_state,
                    f"{unique_context_id}_{arg_name}",
                    current_value=current_val # Pass the potentially corrected current value
                )
            i += 1

    st.markdown("---")
    st.markdown("**Column Assertions**")
    st.caption("Define the validation rules for each column you want to check.")

    # --- 2. Render Dynamic Assertion Rows ---
    indices_to_delete = [] # Keep track of indices to delete
    for i, assertion in enumerate(assertions):
        with st.container(border=True):
            cols = st.columns([0.35, 0.3, 0.35, 0.08])

            with cols[0]:
                assertion['col_value'] = st.text_input(
                    "**Table Header Name**",
                    value=assertion.get('col_value', ''),
                    key=f"{unique_context_id}_col_{i}",
                    help="The exact text of the column header in the table."
                )
                assertion['id'] = assertion['col_value'].strip() # Update ID based on input

            with cols[1]:
                assertion_preset = ARGUMENT_PRESETS.get('assertion', {})
                options = assertion_preset.get('options', ['equal', 'contains', 'should be', 'should not be'])
                default_index = options.index(assertion['assert_value']) if assertion['assert_value'] in options else 0
                assertion['assert_value'] = st.selectbox(
                    "**Assertion**",
                    options,
                    index=default_index,
                    key=f"{unique_context_id}_assert_{i}"
                )

            with cols[2]:
                assertion['expected_value'] = st.text_input(
                    "**Expected Value**",
                    value=assertion['expected_value'],
                    key=f"{unique_context_id}_expected_{i}"
                )

            with cols[3]:
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                if st.button("🗑️", key=f"{unique_context_id}_del_{i}", help="Delete this assertion"):
                     indices_to_delete.append(i) # Mark for deletion

    # --- Process Deletions ---
    if indices_to_delete:
         # Delete in reverse order to avoid index shifting issues
         for index in sorted(indices_to_delete, reverse=True):
              del st.session_state[state_key][index]
         st.rerun() # Rerun immediately after deletion

    if st.button("✚ Add Column Assertion", use_container_width=True, key=f"{unique_context_id}_add_assertion"):
        st.session_state[state_key].append({'id': '', 'col_value': '', 'assert_value': 'equal', 'expected_value': ''})
        st.rerun()

    # --- 3. Build final flat dictionary from the current assertion state ---
    for assertion in st.session_state[state_key]: # Use the potentially updated state
        column_id = assertion['id'].strip()
        if column_id:
            final_args[f"col.{column_id}"] = assertion['col_value'].strip()
            final_args[f"assert.{column_id}"] = assertion['assert_value']
            final_args[f"expected.{column_id}"] = assertion['expected_value']

    return final_args


# This function remains here as it's specifically for the dialog context
def render_verify_table_arguments_for_dialog(ws_state, context, section_name, selected_kw):
    """
    A self-contained UI for the 'Verify Result...' keyword specifically for the Add Dialog.
    It manages its own state and submission button, completely outside of an st.form.
    Calls the edit mode renderer internally.
    """
    # Determine the unique context ID based on where it's called from
    if isinstance(context, dict): # CRUD context
         dialog_context_id = f"add_dialog_crud_{context.get('key', 'unknown')}_verify_table"
    else: # Test Flow context (context is the timeline_key string)
         dialog_context_id = f"add_dialog_tf_{context}_verify_table"


    # --- Call the edit mode renderer to display the inputs ---
    args_data = render_verify_table_arguments_for_edit_mode(
        ws_state=ws_state,
        unique_context_id=dialog_context_id,
        current_args={} # Always empty for a new step
    )

    st.markdown("---") # Add a separator

    # --- Add its own submission button ---
    # Need to know which callback and dialog state key to use based on context
    if isinstance(context, dict): # CRUD context
         dialog_state_key = 'show_crud_add_dialog'
         add_callback_target = context.get("add_callback") # Expect callback in context
    else: # Test Flow context
         dialog_state_key = 'show_add_dialog'
         add_callback_target = context.get("add_callback") # Expect callback in context

    if add_callback_target and st.button(f"✅ Add Step to {section_name}", type="primary", use_container_width=True, key=f"{dialog_context_id}_submit"):
        new_step = {"id": str(uuid.uuid4()), "keyword": selected_kw['name'], "args": args_data}
        add_callback_target(context, new_step) # Use the correct callback

        # Cleanup - Use correct keys based on context
        st.session_state[dialog_state_key] = False
        if isinstance(context, dict):
             selected_kw_key = 'selected_kw_crud'
             context_key = 'crud_add_dialog_context'
        else:
             selected_kw_key = 'selected_kw'
             context_key = 'add_dialog_timeline' # Or appropriate key

        if selected_kw_key in st.session_state: del st.session_state[selected_kw_key]
        if context_key in st.session_state: del st.session_state[context_key] # Make sure context is cleared if needed

        state_key_verify = f"verify_table_assertions_{dialog_context_id}"
        if state_key_verify in st.session_state: del st.session_state[state_key_verify]

        st.rerun()

# ======= CSV VALUE HELPER (SHARED) =======

def get_available_csv_datasources(ws_state):
    """
    Extract CSV data sources from workspace (works for all modules).
    
    Returns:
        dict: {ds_name: {ds_var, col_var, csv_filename, headers}}
    """
   
    result = {}
    data_sources = ws_state.get('data_sources', [])
    project_path = st.session_state.get('project_path', '')

    for ds in data_sources:
        ds_name = ds.get('name', '').upper()
        csv_filename = ds.get('file_name', '')
        col_var = ds.get('col_name', '')
        
        if not ds_name or not csv_filename:
            continue
        
        # Get CSV headers
        headers = util_get_csv_headers(project_path, csv_filename)
        
        result[ds_name] = {
            'ds_var': f"DS_{ds_name.replace(' ', '_')}",
            'col_var': col_var if col_var else f"{ds_name.lower().replace(' ', '_')}",
            'csv_filename': csv_filename,
            'headers': headers if headers else []
        }
    
    return result


def render_csv_insert_button(input_key, ws_state, button_label="📊"):
    """
    Shared CSV value insertion popover button.
    Use this next to ANY text_input in the app.
    
    Args:
        input_key: The key of the text_input to insert value into
        ws_state: Session state workspace
        button_label: Button text/icon
        
    Returns:
        str or None: Variable syntax if user clicked insert, else None
        
    Usage:
        col1, col2 = st.columns([4, 1])
        with col1:
            value = st.text_input("Value", key="my_value")
        with col2:
            st.markdown("<div style='margin-top: 1.8rem;'></div>", unsafe_allow_html=True)
            inserted = render_csv_insert_button("my_value", ws_state)
            if inserted:
                st.session_state["my_value"] = inserted
                # Note: In forms, this won't rerun until form submits
    """
    datasources = get_available_csv_datasources(ws_state)
    
    if not datasources:
        st.caption("_No CSV_")
        return None
    
    with st.popover(button_label, use_container_width=True):
        st.markdown("**Insert from CSV**")
        st.caption("Select data source and column")
        
        # Step 1: Select Data Source
        selected_ds = st.selectbox(
            "Data Source",
            options=list(datasources.keys()),
            key=f"{input_key}_csvpop_ds",
            help="Choose which CSV to use"
        )
        
        if not selected_ds:
            return None
            
        ds_info = datasources[selected_ds]
        headers = ds_info.get('headers', [])
        
        if not headers:
            st.error("⚠️ No columns found in CSV")
            return None
        
        # Step 2: Enter Row Key
        row_key = st.text_input(
            "Row Key",
            key=f"{input_key}_csvpop_rowkey",
            placeholder="e.g., robotapi",
            help="Value from first column to identify the row"
        )
        
        # Step 3: Select Column (if multi-column CSV)
        selected_column = None
        if len(headers) > 1:
            selected_column = st.selectbox(
                "Column",
                options=headers[1:],  # Skip first column (key column)
                key=f"{input_key}_csvpop_col",
                help="Which column value to use"
            )
        
        # Step 4: Generate Syntax and Preview
        if row_key:
            ds_var = ds_info['ds_var']
            col_var = ds_info['col_var']
            
            # Generate syntax based on CSV structure
            if len(headers) > 1 and selected_column:
                # Multi-column: ${DS_LOGIN['robotapi'][${login_col.username}]}
                variable_syntax = f"${{{ds_var}['{row_key}'][${{{col_var}.{selected_col}}}]}}"
            else:
                # Single column: ${DS_DATA['key']}
                variable_syntax = f"${{{ds_var}['{row_key}']}}"
            
            # Show preview
            st.markdown("**Preview:**")
            st.code(variable_syntax, language="robotframework")
            
            # Insert button
            if st.button(
                "✅ Insert", 
                key=f"{input_key}_csvpop_insert", 
                type="primary", 
                use_container_width=True
            ):
                return variable_syntax
        else:
            st.info("💡 Enter row key to continue")
    
    return None

# ======= REVISED STEP CARD (V3.6) =======
def render_step_card_compact(step, index, section_key, ws, manager_module, card_prefix="crud"):
    """
    REVISED (V3.11) - Enhanced CSV/API config display
    Displays CSV configuration in caption.
    Inline Editing similar to ui_test_flow.
    """
    real_section_key = section_key
    ws_state = st.session_state.studio_workspace

    global ARGUMENT_PRESETS, ARGUMENT_PATTERNS

    # --- Logic to handle 'virtual' section keys ---
    if section_key == 'action_detail_others':
        real_section_key = 'action_detail'
        steps_list_for_display = [s for s in ws['steps']['action_detail'] if s['keyword'] != 'Fill in data form']
    elif section_key == 'verify_detail_others':
        real_section_key = 'verify_detail'
        steps_list_for_display = [s for s in ws['steps']['verify_detail'] if s['keyword'] != 'Verify data form']
    else:
        if real_section_key not in ws['steps']:
            ws['steps'][real_section_key] = []
        steps_list_for_display = ws['steps'][real_section_key]

    try:
        display_index = next(i for i, s in enumerate(steps_list_for_display) if s['id'] == step['id'])
    except StopIteration:
        display_index = index

    try:
        original_list = ws['steps'][real_section_key]
        real_index = next(i for i, s in enumerate(original_list) if s['id'] == step['id'])
        total_steps_in_original = len(original_list)
    except StopIteration:
        real_index = index
        total_steps_in_original = len(original_list) if original_list else 0

    # --- Edit Mode State ---
    edit_mode_key = f'crud_edit_mode_{step["id"]}'
    edit_mode = st.session_state.get(edit_mode_key, False)

    st.markdown("<div class='step-card'>", unsafe_allow_html=True)

    # === CARD HEADER ===
    with st.container():
        kw_col, btn_col = st.columns([0.6, 0.4], vertical_alignment="center")

        with kw_col:
            st.markdown(f"""
            <div class='step-header-content'>
                <span class='step-number-inline'>{display_index + 1}</span>
                <div class='step-keyword'>
                    <div class='step-keyword-label'>KEYWORD</div>
                    <div class='step-keyword-name'>{step.get('keyword', 'N/A')}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

        with btn_col:
            # --- Toolbar Code ---
            st.markdown("<div class='step-card-toolbar-wrapper'>", unsafe_allow_html=True)
            action_cols = st.columns([1, 1, 1, 1, 1], gap="small")

            with action_cols[0]:
                is_first = (real_index == 0)
                if st.button("⬆️", key=f"up_{real_section_key}_{step['id']}", help="Move Up", use_container_width=True, disabled=is_first):
                    manager_module.move_step(real_section_key, step['id'], 'up')
                    st.rerun()

            with action_cols[1]:
                is_last = (real_index == total_steps_in_original - 1)
                if st.button("⬇️", key=f"down_{real_section_key}_{step['id']}", help="Move Down", use_container_width=True, disabled=is_last):
                    manager_module.move_step(real_section_key, step['id'], 'down')
                    st.rerun()

            with action_cols[2]:
                edit_icon = "💾" if edit_mode else "✏️"
                edit_help = "Save Changes" if edit_mode else "Edit Step"
                if st.button(edit_icon, key=f"edit_{real_section_key}_{step['id']}", help=edit_help, use_container_width=True):
                    # Toggle edit mode
                    st.session_state[edit_mode_key] = not edit_mode

                    if st.session_state[edit_mode_key]:
                        edit_kw_state_key = f"edit_kw_select_{step['id']}"
                        temp_args_key = f"edit_temp_args_{step['id']}"

                       # --- START FIX ---
                        prev_kw_key = f"prev_kw_{step['id']}" # 1. กำหนดคีย์
                        current_kw = step.get('keyword', '')  # 2. ดึง KW ปัจจุบัน

                        # ✅ เก็บ keyword ปัจจุบัน
                        st.session_state[edit_kw_state_key] = current_kw

                          # 3. (FIX) ตั้งค่า prev_kw ด้วย KW ปัจจุบันทันที
                        st.session_state[prev_kw_key] = current_kw
                          # --- END FIX ---

                         # ✅ Preload arguments เดิมของ step ลงใน temp state ก่อน rerun
                        current_args = step.get('args', {})
                        st.session_state[temp_args_key] = current_args.copy() if current_args else {}

                        # ✅ ไม่ต้องลบ prev_kw หรือ temp_args ออก — ให้คงไว้จนกว่าจะ save หรือ cancel

                        st.rerun()

            with action_cols[3]:
                if st.button("📋", key=f"copy_{real_section_key}_{step['id']}", help="Duplicate", use_container_width=True):
                    manager_module.duplicate_step(real_section_key, step['id'])
                    st.rerun()

            with action_cols[4]:
                if st.button("🗑️", key=f"del_{real_section_key}_{step['id']}", help="Delete", use_container_width=True):
                    manager_module.delete_step(real_section_key, step['id'])
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    # === CARD BODY (Conditional Rendering) ===
    if not edit_mode:
        # --- Display Mode: Show simple caption ---
        
        # ✅ FIX: Clean and Deduplicate Arguments for Display
        # (ป้องกันการแสดงผลซ้ำ เช่น ${arg} กับ arg ให้ถือเป็นตัวเดียวกัน)
        raw_args = step.get('args', {})
        valid_args = {}
        
        if raw_args:
            for k, v in raw_args.items():
                if v or v is False: # Check validity
                    # ลบ ${} ออกจากชื่อตัวแปรเพื่อให้เป็นมาตรฐานเดียวกัน
                    clean_k = k.strip('${}') 
                    # บันทึกลง dict ใหม่ (ถ้ามีคีย์ซ้ำ ค่าจะถูกอัปเดตทับด้วยค่าล่าสุด)
                    valid_args[clean_k] = v

        if valid_args:
            # ส่ง valid_args ที่คลีนแล้วไปแสดงผล
            args_str = format_args_as_string(valid_args)
            if args_str:
                st.markdown(
                f"<div style='padding: 0.1rem 1rem 0.6rem 1rem; color: #56d364; "
                f"font-size: 0.8rem; font-family: \"SF Mono\", Monaco, monospace; "
                f"line-height: 1.4; margin-top: -0.2rem; word-wrap: break-word; "
                f"white-space: normal; overflow-wrap: break-word;'>{args_str}</div>",
                unsafe_allow_html=True
            )

        # --- Display CSV/API Config ---
        if step.get('type') == 'csv_import' and step.get('config'):
            cfg = step['config']
            st.caption(
                f"🗃️ **Data Source:** {cfg.get('ds_name', '?')} "
                f"→ Variable: `{cfg.get('ds_var', '?')}` "
                f"→ Column: `{cfg.get('col_var', '?')}`"
            )

            if cfg.get('headers'):
                headers_display = ', '.join(cfg['headers'][:5])
                if len(cfg['headers']) > 5:
                    headers_display += "..."
                st.caption(f"📊 **Columns:** {headers_display}")

        elif step.get('type') == 'api_call':
            st.caption(f"🌐 **API Service Call**")

    else:
        # --- Edit Mode: Show inputs ---
        st.markdown("<div class='crud-edit-section'>", unsafe_allow_html=True)

        if 'categorized_keywords' not in ws_state:
            all_keywords_list = ws_state.get('keywords', [])
            if all_keywords_list:
                from .keyword_categorizer import categorize_keywords
                ws_state['categorized_keywords'] = categorize_keywords(all_keywords_list)

        categorized_keywords = ws_state.get('categorized_keywords', {})
        
        # ✅ Smart Filter: ตรวจสอบประเภทของ step ที่กำลัง edit
        step_type = step.get('type', 'common')  # default เป็น common
        
        if step_type == 'keyword_factory' and card_prefix.startswith("crud"):
            # ถ้า step เป็น Keyword Factory → แสดงเฉพาะ Keyword Factory keywords
            crud_ws = st.session_state.get('crud_generator_workspace', {})
            all_kws = crud_ws.get('keyword_factory_keywords', [])
            keyword_source = "Keyword Factory"
        else:
            # ถ้า step เป็น Common Keyword → แสดงเฉพาะ Common keywords
            all_kws = [kw for kws in categorized_keywords.values() for kw in kws]
            keyword_source = "Common Keywords"
        
        all_kw_names = [kw['name'] for kw in all_kws]

        st.markdown("##### 🔧 Edit Step")
        
        # แสดง badge บอกประเภทของ keywords ที่แสดง
        if step_type == 'keyword_factory':
            st.caption("🏭 Editing Keyword Factory Keyword")
        else:
            st.caption("📝 Editing Common Keyword")

        # --- Keyword Selector ---
        current_kw_name = step.get('keyword', '')
        edit_kw_state_key = f"edit_kw_select_{step['id']}"
        if edit_kw_state_key not in st.session_state:
            st.session_state[edit_kw_state_key] = current_kw_name

        # ตรวจสอบว่า keyword ปัจจุบันอยู่ใน list หรือไม่
        try:
            current_index = all_kw_names.index(st.session_state[edit_kw_state_key])
        except ValueError:
            current_index = 0
            # ถ้าหาไม่เจอ ให้ reset เป็น keyword แรก
            if all_kw_names:
                st.session_state[edit_kw_state_key] = all_kw_names[0]

        selected_kw_name = st.selectbox(
            f"Select Keyword ({keyword_source})",
            all_kw_names,
            index=current_index,
            key=edit_kw_state_key
        )
        selected_kw = next((kw for kw in all_kws if kw['name'] == selected_kw_name), None)

        # === ✅ CSV Quick Insert ===
        if selected_kw and selected_kw.get('args'):
            with st.expander("📊 Quick Insert from CSV Data", expanded=False):
                st.caption("Select value and target argument to insert")

                csv_keywords = extract_csv_datasource_keywords(ws_state)

                if csv_keywords:
                    col_ds, col_test = st.columns([1, 1])

                    with col_ds:
                        quick_ds = st.selectbox(
                            "Data Source",
                            options=list(csv_keywords.keys()),
                            key=f"quick_csv_ds_edit_{step['id']}"
                        )

                    quick_row_val = ""
                    with col_test:
                        first_col_options = []
                        if quick_ds:
                            ds_info = csv_keywords.get(quick_ds, {})
                            csv_filename = ds_info.get('csv_filename', '')
                            project_path = st.session_state.get('project_path', '')
                            first_col_options = util_get_csv_first_column_values(project_path, csv_filename)
                        
                        if first_col_options:
                            quick_row_val = st.selectbox(
                                "Row Data Key",
                                options=first_col_options,
                                key=f"quick_csv_row_edit_{step['id']}"
                            )
                        else:
                            quick_row_val = st.text_input(
                                "Row Data Key",
                                key=f"quick_csv_row_edit_{step['id']}",
                                placeholder="e.g., robotapi"
                            )
                    
                    quick_col = None
                    col_column, col_target = st.columns([1, 1])
                    headers = []
                    if quick_ds:
                        ds_info = csv_keywords.get(quick_ds, {})
                        headers = ds_info.get('headers', [])

                        if headers:
                            with col_column:
                                if len(headers) > 1:
                                    quick_col = st.selectbox(
                                        "Column",
                                        options=headers[1:],
                                        key=f"quick_csv_col_edit_{step['id']}"
                                    )

                    target_arg = None
                    with col_target:
                        text_args = []
                        for arg_item in selected_kw.get('args', []):
                            arg_name = arg_item.get('name', '').strip('${}')
                            is_locator = any(s in arg_name.lower() for s in ['locator', 'field', 'button', 'element', 'menu'])
                            is_preset = arg_name in ARGUMENT_PRESETS
                            if not is_locator and not is_preset:
                                text_args.append(arg_name)

                        if text_args:
                            target_arg = st.selectbox(
                                "Insert to →",
                                options=text_args,
                                key=f"quick_csv_target_edit_{step['id']}"
                            )
                        else:
                            st.caption("_No text args_")

                    # ✅ แสดงปุ่ม Insert
                    if quick_ds and target_arg:
                        ds_info = csv_keywords.get(quick_ds, {})
                        ds_var = ds_info.get('ds_var', 'DATA')
                        col_var = ds_info.get('col_var', 'COL')

                        insert_syntax = ""
                        if quick_row_val:
                            if len(headers) > 1 and quick_col:
                                insert_syntax = f"${{{ds_var}['{quick_row_val}'][${{{col_var}.{quick_col}}}]}}"
                            else:
                                insert_syntax = f"${{{ds_var}['{quick_row_val}']}}"

                        if st.button("✅ Insert", type="primary", use_container_width=True,
                                    key=f"quick_csv_insert_btn_edit_{step['id']}"):
                            if not target_arg:
                                st.warning("Please select a target argument 'Insert to →'")
                            elif not quick_row_val:
                                st.warning("Please enter a 'Row Key'")
                            elif insert_syntax:
                                temp_args_key_insert = f"edit_temp_args_{step['id']}" # Use different var name
                                if temp_args_key_insert not in st.session_state:
                                    st.session_state[temp_args_key_insert] = {}

                                # ✅ อัปเดต temp_args_key
                                st.session_state[temp_args_key_insert][target_arg] = insert_syntax

                                # ✅ อัปเดต widget keys ทั้งหมดที่เป็นไปได้
                                base_key = f"crud_edit_{step['id']}_{target_arg}"
                                # Ensure keys exist before setting
                                if base_key in st.session_state:
                                    st.session_state[base_key] = insert_syntax
                                if f"{base_key}_default_text" in st.session_state:
                                    st.session_state[f"{base_key}_default_text"] = insert_syntax

                                st.toast(f"✅ Inserted '{insert_syntax}' into '{target_arg}'", icon="✅")
                                st.rerun()
                else:
                    st.info("No CSV data sources found. Add them in Test Data tab.")

            st.markdown("---")

        # --- Argument Inputs (FIXED LOGIC) ---
        temp_args_key = f"edit_temp_args_{step['id']}"

        # 1. Initialize temp args ONCE (เมื่อเริ่มกด Edit)
        if temp_args_key not in st.session_state or not st.session_state.get(temp_args_key):
            st.session_state[temp_args_key] = {}
            current_step_args_init = step.get('args', {})
            
            # ✅ FIX: ตอนโหลดค่าเดิม ให้ Clean Key ก่อน (ลบ ${} ออก) เพื่อให้ตรงกับ input field
            if current_step_args_init:
                 for k, v in current_step_args_init.items():
                     clean_k = k.strip('${}')
                     st.session_state[temp_args_key][clean_k] = v
            
            # ถ้าไม่มีค่าเดิม ให้ลองโหลด Default จาก Keyword Definition
            elif selected_kw and selected_kw.get('args'):
                for arg_item in selected_kw.get('args', []):
                    clean_arg_name_init = arg_item.get('name', '').replace('${', '').replace('}', '')
                    arg_info_init = arg_item.get('info', {}) 
                    initial_value_init = arg_info_init.get('default', '')
                    st.session_state[temp_args_key][clean_arg_name_init] = initial_value_init

        # 2. Check if keyword changed (Reset ถ้าเปลี่ยน Keyword)
        if st.session_state.get(edit_kw_state_key) != st.session_state.get(f"prev_kw_{step['id']}", ""):
            st.session_state[temp_args_key] = {}
            if selected_kw and selected_kw.get('args'):
                for arg_item in selected_kw.get('args', []):
                    arg_info_change = arg_item.copy() if isinstance(arg_item, dict) else {'name': str(arg_item), 'default': ''}
                    clean_arg_name_change = arg_info_change.get('name', '').strip('${}')
                    if not clean_arg_name_change:
                        continue
                    st.session_state[temp_args_key][clean_arg_name_change] = arg_info_change.get('default', '')
            st.session_state[f"prev_kw_{step['id']}"] = selected_kw_name

        # 3. Render argument inputs
        if selected_kw and selected_kw.get('args'):
            st.markdown("**Arguments:**")

            for arg_item in selected_kw.get('args', []):
                arg_info = arg_item.copy() if isinstance(arg_item, dict) else {'name': str(arg_item), 'default': ''}
                
                raw_arg_name = arg_info.get('name', '') # ชื่อดิบที่มี ${}
                clean_arg_name = raw_arg_name.strip('${}') # ชื่อคลีนสำหรับ UI
                
                if not clean_arg_name:
                    continue
                arg_info['name'] = clean_arg_name

                # ✅ FIX: อ่านค่าโดยเช็คทั้ง Key แบบ Clean และ Raw
                # (ป้องกันกรณีข้อมูลเก่าเก็บ key ไว้ต่างรูปแบบกัน)
                val_from_temp_clean = st.session_state[temp_args_key].get(clean_arg_name)
                val_from_temp_raw = st.session_state[temp_args_key].get(raw_arg_name)
                
                if val_from_temp_clean is not None:
                    current_value = val_from_temp_clean
                elif val_from_temp_raw is not None:
                    current_value = val_from_temp_raw
                else:
                    current_value = arg_info.get('default', '')

                # สร้าง unique key สำหรับ Input Widget
                input_key = f"crud_edit_{step['id']}_{clean_arg_name}"

                # Render Input
                rendered_value = render_argument_input(
                    arg_info,
                    ws_state,
                    input_key,
                    current_value=current_value,
                    selected_kw_name=selected_kw_name
                )

                # ✅ FIX: ใช้ค่าที่ Render ออกมาอัปเดตกลับเข้า temp state ทันที
                # เพื่อให้ค่าไม่หายเมื่อมีการ Rerun (เช่น กดปุ่ม Insert CSV)
                if rendered_value is not None:
                    st.session_state[temp_args_key][clean_arg_name] = rendered_value

                # Determine the actual key used by render_argument_input & GET value
                is_locator_arg = any(s in clean_arg_name.lower() for s in ['locator', 'field', 'button', 'element', 'menu', 'header', 'body', 'theader', 'tbody'])

                final_value = None

                # === START: (SAVE V2 FIX) LOGIC TO GET VALUE ===
                if is_locator_arg:
                    if 'menu' in clean_arg_name.lower():
                        # Read directly from session_state keys set by render_argument_input
                        selected_main = st.session_state.get(f"{input_key}_main_menu_select", '')
                        selected_sub = st.session_state.get(f"{input_key}_sub_menu_select", '')

                        parts = []
                        if selected_main:
                            parts.append(f"${{mainmenu}}[{selected_main}]")
                        # Add Submenu only if Keyword is "Go to SUBMENU name"
                        kw_name_lower = str(selected_kw_name).lower() # Use selected_kw_name
                        if selected_sub and 'go to submenu name' in kw_name_lower:
                            parts.append(f"${{submenu}}[{selected_sub}]")

                        final_value = "    ".join(parts) # Join with 4 spaces
                    else:
                        # Logic for other locators
                        final_value = st.session_state.get(f"{input_key}_locator_select", current_value)

                elif clean_arg_name in ARGUMENT_PRESETS:
                    config = ARGUMENT_PRESETS[clean_arg_name]
                    input_type = config.get('type')
                    if input_type == "select_or_input":
                        selected = st.session_state.get(f"{input_key}_select")
                        if selected == "📝 Other (custom)":
                            final_value = st.session_state.get(f"{input_key}_custom", current_value)
                        else:
                            final_value = selected if selected is not None else current_value
                    elif input_type == "boolean":
                         final_value = 'true' if st.session_state.get(input_key, False) else 'false'
                    else:
                        final_value = st.session_state.get(input_key, current_value)
                else:
                    # Check patterns
                    matched_pattern = False
                    arg_lower = clean_arg_name.lower()
                    for pattern_key in ARGUMENT_PATTERNS.keys():
                        if pattern_key in arg_lower:
                            final_value = st.session_state.get(input_key, current_value) # Key is base for pattern
                            matched_pattern = True
                            break

                    # Default Text Input
                    if not matched_pattern:
                        final_value = st.session_state.get(f"{input_key}_default_text", current_value)

                # Update temp_args_key (ensure value is not None)
                st.session_state[temp_args_key][clean_arg_name] = final_value if final_value is not None else current_value
                # === END: (SAVE V2 FIX) LOGIC TO GET VALUE ===


        elif not selected_kw:
            st.warning("Selected keyword definition not found.")

        # --- Save/Cancel Buttons (FIXED LOGIC) ---
        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Save Changes", key=f"save_edit_{step['id']}", use_container_width=True, type="primary"):
                if selected_kw.get('args'):
                    for arg_item in selected_kw.get('args', []):
                        # เตรียมชื่อตัวแปร
                        arg_info = arg_item.copy() if isinstance(arg_item, dict) else {'name': str(arg_item), 'default': ''}
                        clean_arg_name = arg_info.get('name', '').strip('${}')
                        if not clean_arg_name: continue
                        
                        # Key พื้นฐานของ Widget
                        input_key = f"crud_edit_{step['id']}_{clean_arg_name}"
                        
                        # ตัวแปรสำหรับเช็คเงื่อนไข
                        kw_name_lower = str(selected_kw_name).lower()
                        arg_lower = clean_arg_name.lower()
                        final_value = None

                        # --- 1. Menu Locators ---
                        if 'go to menu name' in kw_name_lower and clean_arg_name == 'menu_locator':
                            val = st.session_state.get(f"{input_key}_main_menu_select", '')
                            final_value = f"${{mainmenu}}[{val}]" if val else ""
                        elif 'go to submenu name' in kw_name_lower and clean_arg_name == 'main_menu':
                            final_value = st.session_state.get(f"{input_key}_main_menu_select", '')
                        elif 'go to submenu name' in kw_name_lower and clean_arg_name == 'submenu':
                            final_value = st.session_state.get(f"{input_key}_sub_menu_select", '')

                        # --- 2. PRESETS (สำคัญ: เช็คก่อน Locator เพื่อดัก button_name) ---
                        elif clean_arg_name in ARGUMENT_PRESETS:
                            config = ARGUMENT_PRESETS[clean_arg_name]
                            input_type = config.get('type')
                            if input_type == "select_or_input":
                                sel = st.session_state.get(f"{input_key}_select")
                                if sel == "📝 Other (custom)":
                                    final_value = st.session_state.get(f"{input_key}_custom")
                                else:
                                    final_value = sel
                            elif input_type == "boolean":
                                final_value = 'true' if st.session_state.get(input_key, False) else 'false'
                            else:
                                final_value = st.session_state.get(input_key)

                        # --- 3. LOCATOR ---
                        elif any(s in arg_lower for s in ['locator', 'field', 'button', 'element', 'header', 'body', 'theader', 'tbody']):
                            final_value = st.session_state.get(f"{input_key}_locator_select")

                        # --- 4. PATTERNS & DEFAULT ---
                        else:
                            matched = False
                            for p_key in ARGUMENT_PATTERNS.keys():
                                if p_key in arg_lower:
                                    final_value = st.session_state.get(input_key)
                                    matched = True
                                    break
                            if not matched:
                                final_value = st.session_state.get(f"{input_key}_default_text")

                        # Fallback & Update
                        if final_value is None: 
                            # ถ้าหาไม่เจอ ให้ลองดึงค่าเดิมที่มีอยู่
                            final_value = st.session_state.get(temp_args_key, {}).get(clean_arg_name, '')
                        
                        st.session_state[temp_args_key][clean_arg_name] = final_value    
                      
                # ✅ ใช้ค่าจาก temp_args_key โดยตรง
                updated_data = {
                    "keyword": selected_kw_name,
                    "args": st.session_state.get(temp_args_key, {}).copy()
                }

                if 'type' in step:
                    updated_data['type'] = step['type']
                if 'config' in step:
                    updated_data['config'] = step['config']

                manager_module.update_step(real_section_key, step['id'], updated_data) # Use manager_module

                # Cleanup states
                st.session_state[edit_mode_key] = False
                if edit_kw_state_key in st.session_state:
                    del st.session_state[edit_kw_state_key]
                if temp_args_key in st.session_state:
                    del st.session_state[temp_args_key]
                if f"prev_kw_{step['id']}" in st.session_state:
                    del st.session_state[f"prev_kw_{step['id']}"]

                 # ✅ Cleanup CSV Quick Insert keys
                csv_keys = [
                    f"quick_csv_ds_edit_{step['id']}",
                    f"quick_csv_row_edit_{step['id']}",
                    f"quick_csv_col_edit_{step['id']}",
                    f"quick_csv_target_edit_{step['id']}",
                ]
                for key in csv_keys:
                    if key in st.session_state:
                        del st.session_state[key]

                # ✅ Cleanup Widget Keys
                if selected_kw and selected_kw.get('args'):
                    for arg_item in selected_kw.get('args', []):
                        clean_arg_name_cleanup = arg_item.get('name', '').strip('${}')
                        if clean_arg_name_cleanup:
                            # Add all possible suffixes used by render_argument_input
                            suffixes = ["", "_select", "_custom", "_locator_select", "_default_text", "_main_menu_select", "_sub_menu_select"]
                            for suffix in suffixes:
                                widget_key_cleanup = f"crud_edit_{step['id']}_{clean_arg_name_cleanup}{suffix}"
                                if widget_key_cleanup in st.session_state:
                                    try:
                                        del st.session_state[widget_key_cleanup]
                                    except KeyError: pass # Ignore if already deleted

                st.rerun()

        with col2:
            if st.button("❌ Cancel", key=f"cancel_edit_{step['id']}", use_container_width=True):
                st.session_state[edit_mode_key] = False
                # Cleanup state keys like in Save
                if edit_kw_state_key in st.session_state: del st.session_state[edit_kw_state_key]
                if temp_args_key in st.session_state: del st.session_state[temp_args_key]
                if f"prev_kw_{step['id']}" in st.session_state: del st.session_state[f"prev_kw_{step['id']}"]
                # Cleanup CSV Quick Insert keys
                csv_keys_cancel = [ f"quick_csv_ds_edit_{step['id']}", f"quick_csv_row_edit_{step['id']}", f"quick_csv_col_edit_{step['id']}", f"quick_csv_target_edit_{step['id']}",]
                for key in csv_keys_cancel:
                    if key in st.session_state: del st.session_state[key]
                # Cleanup Widget Keys (same logic as Save)
                if selected_kw and selected_kw.get('args'):
                    for arg_item in selected_kw.get('args', []):
                        clean_arg_name_cleanup_cancel = arg_item.get('name', '').strip('${}')
                        if clean_arg_name_cleanup_cancel:
                            suffixes_cancel = ["", "_select", "_custom", "_locator_select", "_default_text", "_main_menu_select", "_sub_menu_select"]
                            for suffix in suffixes_cancel:
                                widget_key_cleanup_cancel = f"crud_edit_{step['id']}_{clean_arg_name_cleanup_cancel}{suffix}"
                                if widget_key_cleanup_cancel in st.session_state:
                                    try: del st.session_state[widget_key_cleanup_cancel]
                                    except KeyError: pass
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

def extract_csv_datasource_keywords(ws_state):
    """
    Extracts CSV Data Source information from workspace state.
    Returns dict: {ds_name: {col_var, ds_var, csv_path, headers}}
    """
    result = {}
    
    # Get data sources from workspace
    data_sources = ws_state.get('data_sources', [])
    project_path = st.session_state.get('project_path', '')

    for ds in data_sources:
        ds_name_raw = ds.get('name', '')
        csv_filename = ds.get('file_name', '')
        col_var = ds.get('col_name', '')
        
        if not ds_name_raw or not csv_filename:
            continue
        
        # Generate variable names
        # e.g., "LOGIN" -> "DS_LOGIN"
        ds_var_name = f"{ds_name_raw.upper().replace(' ', '_')}"
        
        # Get CSV headers
        headers = util_get_csv_headers(project_path, csv_filename)
        
        # Use ds_name_raw for both key and col_var generation
        result[ds_name_raw.upper()] = {  # ← แก้ตรงนี้
            'col_var': col_var if col_var else f"{ds_name_raw.lower().replace(' ', '_')}",  # ← แก้ตรงนี้ด้วย
            'ds_var': ds_var_name,
            'csv_filename': csv_filename,
            'headers': headers if headers else []
        }
    
    return result