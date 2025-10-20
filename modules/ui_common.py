# modules/ui_common.py
"""
Common UI Utility Functions
Contains shared UI components and helper functions used across different modules.
"""
import streamlit as st
import uuid
import json
from pathlib import Path
from .session_manager import get_clean_locator_name # Import needed helper

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

# --- Argument Input Rendering Functions (Moved from ui_test_flow.py) ---

# (Helper for CSV popover - Keep it here as it's used by render_argument_input)
def render_csv_variable_helper(arg_info, input_key, ws_state):
    """
    Renders a helper UI for inserting CSV variable syntax.
    Returns the inserted text or None.
    (Needs ws_state for extract_csv_datasource_keywords)
    """
    # Import locally to avoid potential circular dependency if extract_csv_datasource_keywords moves
    from .crud_generator.ui_crud import extract_csv_datasource_keywords

    # Extract available data sources
    csv_keywords = extract_csv_datasource_keywords(ws_state)

    if not csv_keywords:
        return None

    with st.popover("📊 Insert CSV Value", use_container_width=True):
        st.caption("Select a data source and column to insert:")

        selected_ds = st.selectbox(
            "Data Source",
            options=list(csv_keywords.keys()),
            key=f"{input_key}_csv_ds_select"
        )

        if selected_ds:
            ds_info = csv_keywords[selected_ds]
            headers = ds_info.get('headers', [])

            if headers:
                row_key = st.text_input(
                    "Row Key (e.g., 'robotapi')",
                    key=f"{input_key}_csv_row_key",
                    placeholder="Enter the key value"
                )

                selected_col = st.selectbox(
                    "Column",
                    options=headers[1:] if len(headers) > 1 else headers, # Adjust options based on headers length
                    key=f"{input_key}_csv_col_select"
                )

                if st.button("✅ Insert", key=f"{input_key}_csv_insert_btn"):
                    # Generate the variable syntax
                    ds_var = ds_info['ds_var']
                    col_var = ds_info['col_var']

                    if len(headers) > 1:
                        # Multi-column format - Using f-string interpolation correctly
                        variable_syntax = f"${{{ds_var}['{row_key}'][${{{col_var}.{selected_col}}}]}}"
                    else:
                         # Single column format needs key only
                        variable_syntax = f"${{{ds_var}['{row_key}']}}" # Corrected: Use row_key

                    return variable_syntax
            else:
                 st.caption("No columns found for selected data source.")

    return None


def render_preset_input(arg_name, config, default_value, step_id_or_key_prefix):
    """
    Render input based on preset configuration
    (Modified to accept a unique key prefix instead of just step_id)
    """
    input_type = config.get('type')
    label = config.get('label', f"📝 {arg_name}")
    key_base = f"{step_id_or_key_prefix}_{arg_name}" # Use prefix for unique keys

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
        options = config.get('options', [])
        allow_custom = config.get('allow_custom', True)

        if allow_custom:
            display_options = options + ["📝 Other (custom)"]
            select_key = f"{key_base}_select"
            custom_input_key = f"{key_base}_custom"

            # Determine default index and initial custom value
            default_index = 0
            initial_custom_value = ""
            if default_value:
                try:
                    default_index = options.index(default_value)
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
            else:
                # If user switches back from custom, clear the custom state
                if st.session_state.get(custom_input_key):
                     st.session_state[custom_input_key] = ""
                return selected
        else: # Select only (no custom) - simplified
             options = config.get('options', [])
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
                 key=key_base # Use base key directly
             )
    else: # Fallback to text input if type is unknown
         return st.text_input(label, value=str(default_value) if default_value is not None else "", key=key_base)


def render_pattern_input(arg_name, config, default_value, step_id_or_key_prefix):
    """
    Render input based on pattern matching (username, password, etc.)
    (Modified to accept a unique key prefix)
    """
    input_type = config.get('type', 'text')
    label = config.get('label', f"📝 {arg_name}")
    placeholder = config.get('placeholder', '')
    key = f"{step_id_or_key_prefix}_{arg_name}" # Use prefix for unique key

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


def render_argument_input(arg_info, ws_state, unique_key_prefix, current_value=None):
    """
    Smart argument input renderer with priority (Modified for unique keys and current_value).
    Now includes CSV helper popover.
    """
    arg_name = arg_info.get('name')
    # Use current_value if provided, otherwise fallback to arg_info default
    default_value = current_value if current_value is not None else arg_info.get('default', '')

    # Priority 1: Check if it's a Locator argument
    is_locator_arg = any(s in arg_name.lower() for s in ['locator', 'field', 'button', 'element', 'menu', 'header', 'body', 'theader', 'tbody']) # Expanded list

    if is_locator_arg:
        locator_options = [''] + sorted([loc['name'] for loc in ws_state.get('locators', [])]) # Sort options

        # Handle potential ${EMPTY} value coming from Robot files
        effective_default = '' if default_value == '${EMPTY}' else default_value

        default_index = 0
        try:
            if effective_default and effective_default in locator_options:
                default_index = locator_options.index(effective_default)
        except ValueError:
             default_index = 0 # Fallback if value not in options

        # Use columns for selectbox and potential CSV helper
        col1, col2 = st.columns([4, 1])
        with col1:
             selected_locator = st.selectbox(
                 f"🎯 {arg_name}",
                 locator_options,
                 index=default_index,
                 key=f"{unique_key_prefix}_locator_select", # Unique key
                 format_func=get_clean_locator_name # Use helper for display
             )
        # No CSV helper needed for locators
        return selected_locator


    # Priority 2: Check if argument name matches preset (exact match)
    if arg_name in ARGUMENT_PRESETS:
        # Use columns for preset input and potential CSV helper
        col1, col2 = st.columns([4, 1])
        with col1:
             preset_value = render_preset_input(arg_name, ARGUMENT_PRESETS[arg_name], default_value, unique_key_prefix)
        with col2:
             # Add vertical space to align button better
             st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
             csv_value = render_csv_variable_helper(arg_info, unique_key_prefix, ws_state)
             if csv_value:
                 # Update the state of the *actual* input element (might be complex for select_or_input)
                 # This part might need refinement depending on how render_preset_input sets state
                 st.session_state[f"{unique_key_prefix}_{arg_name}"] = csv_value # Assuming base key works
                 st.rerun()
        return preset_value # Return the value from the preset input

    # Priority 3: Check pattern matching (partial match)
    arg_lower = arg_name.lower()
    for pattern_key, pattern_config in ARGUMENT_PATTERNS.items():
        if pattern_key in arg_lower:
            # Use columns for pattern input and potential CSV helper
            col1, col2 = st.columns([4, 1])
            with col1:
                 pattern_value = render_pattern_input(arg_name, pattern_config, default_value, unique_key_prefix)
            with col2:
                 st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                 csv_value = render_csv_variable_helper(arg_info, unique_key_prefix, ws_state)
                 if csv_value:
                      st.session_state[f"{unique_key_prefix}_{arg_name}"] = csv_value
                      st.rerun()
            return pattern_value

    # Priority 4: Default - Text Input
    col1, col2 = st.columns([4, 1])
    with col1:
         text_value = st.text_input(
             f"📝 {arg_name}",
             value=str(default_value) if default_value is not None else "",
             key=f"{unique_key_prefix}_default_text", # Unique key
             placeholder="Enter value or ${VARIABLE}"
         )
    with col2:
         st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
         csv_value = render_csv_variable_helper(arg_info, unique_key_prefix, ws_state)
         if csv_value:
             st.session_state[f"{unique_key_prefix}_default_text"] = csv_value
             st.rerun()
    return text_value


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