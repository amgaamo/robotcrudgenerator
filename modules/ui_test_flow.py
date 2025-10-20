"""
UI Module for the Test Flow Tab
(Version 25.0 - Enhanced Modern Design)
"""
import streamlit as st
import uuid
from .test_flow_manager import categorize_keywords, generate_robot_script_from_timeline
import json
import os
from pathlib import Path

# ===== เพิ่มส่วนนี้ =====
def load_argument_presets():
    """Load argument presets from JSON file"""
    try:
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
# ===== จบส่วนที่เพิ่ม =====

def render_preset_input(arg_name, config, default_value, step_id):
    """
    Render input based on preset configuration
    """
    input_type = config.get('type')
    label = config.get('label', f"📝 {arg_name}")
    
    if input_type == "boolean":
        # Boolean → Checkbox
        default_bool = default_value.lower() == 'true' if default_value else config.get('default', 'false').lower() == 'true'
        result = st.checkbox(
            label,
            value=default_bool,
            key=f"dialog_arg_{arg_name}_{step_id}"
        )
        return str(result).lower()  # Convert to 'true'/'false' string
    
    elif input_type == "select":
        # Select only (no custom input)
        options = config.get('options', [])
        default_index = 0
        if default_value and default_value in options:
            default_index = options.index(default_value)
        
        return st.selectbox(
            label,
            options,
            index=default_index,
            key=f"dialog_arg_{arg_name}_{step_id}"
        )
    
    elif input_type == "select_or_input":
        # Select with custom input option
        options = config.get('options', [])
        allow_custom = config.get('allow_custom', True)
        
        if allow_custom:
            display_options = options + ["📝 Other (custom)"]
            
            if default_value and default_value in options:
                default_index = options.index(default_value)
            elif default_value:
                default_index = len(options)
            else:
                default_index = 0
            
            # --- ✅ FIX: REMOVED the on_change callback ---
            select_key = f"dialog_arg_{arg_name}_select_{step_id}"
            selected = st.selectbox(
                label,
                display_options,
                index=default_index,
                key=select_key
            )
            # --- END OF FIX ---
            
            # ตรวจสอบค่าที่ถูก "เลือก" ใน state ของ selectbox
            # เพื่อให้รู้ว่าควรจะแสดงช่อง Custom Input หรือไม่
            if st.session_state[select_key].endswith("Other (custom)"):
                custom_input_key = f"dialog_arg_{arg_name}_custom_{step_id}"

                # กำหนดค่าเริ่มต้นให้ช่อง custom input เพียงครั้งเดียว
                if custom_input_key not in st.session_state:
                    if default_value and default_value not in options:
                        st.session_state[custom_input_key] = default_value
                    else:
                        st.session_state[custom_input_key] = ""
                
                # วาด Text Input
                st.text_input(
                    f"✏️ Custom {arg_name}",
                    key=custom_input_key,
                    placeholder=config.get('placeholder', 'Enter custom value')
                )
                # คืนค่าล่าสุดที่อยู่ใน state ของ "ช่อง custom" ออกไป
                return st.session_state.get(custom_input_key, "")
            else:
                # ถ้าไม่ได้เลือก "Other" ก็คืนค่าที่เลือกจาก dropdown ไปตามปกติ
                return selected
        else:
            # (ส่วนนี้คือโค้ดเดิมที่ไม่ต้องแก้ไข)
            default_index = 0
            if default_value and default_value in options:
                default_index = options.index(default_value)
            
            return st.selectbox(
                label,
                options,
                index=default_index,
                key=f"dialog_arg_{arg_name}_{step_id}"
            )


def render_pattern_input(arg_name, config, default_value, step_id):
    """
    Render input based on pattern matching (username, password, etc.)
    """
    input_type = config.get('type', 'text')
    label = config.get('label', f"📝 {arg_name}")
    placeholder = config.get('placeholder', '')
    
    if input_type == "password":
        return st.text_input(
            label,
            value=default_value,
            type="password",
            key=f"dialog_arg_{arg_name}_{step_id}",
            placeholder=placeholder
        )
    else:
        # Show suggestions in help text or placeholder
        suggestions = config.get('suggestions', [])
        
        if suggestions:
            # แสดง suggestions ใน help text แทน
            help_text = f"💡 Suggestions: {', '.join(suggestions)}"
            enhanced_placeholder = placeholder or f"e.g., {suggestions[0]}"
            
            return st.text_input(
                label,
                value=default_value,
                key=f"dialog_arg_{arg_name}_{step_id}",
                placeholder=enhanced_placeholder,
                help=help_text
            )
        else:
            return st.text_input(
                label,
                value=default_value,
                key=f"dialog_arg_{arg_name}_{step_id}",
                placeholder=placeholder
            )


def render_argument_input(arg_info, ws_state, step_id):
    """
    Smart argument input renderer with priority:
    1. Check if it's a Locator argument
    2. Check if argument name matches preset
    3. Check if argument name matches pattern
    4. Default to text input
    """
    arg_name = arg_info.get('name')
    default_value = arg_info.get('default', '')
    
    # Priority 1: Check if it's a Locator argument
    is_locator_arg = any(s in arg_name.lower() for s in ['locator', 'field', 'button', 'element', 'menu'])
    
    if is_locator_arg:
        locator_options = [''] + [loc['name'] for loc in ws_state.get('locators', [])]

        if default_value == '${EMPTY}':
            default_value = ''    

        default_index = 0
        if default_value and default_value in locator_options:
            default_index = locator_options.index(default_value)
        
        return st.selectbox(
            f"🎯 {arg_name}",
            locator_options,
            index=default_index,
            key=f"dialog_arg_{arg_name}_{step_id}"
        )
    
    # Priority 2: Check if argument name matches preset (exact match)
    if arg_name in ARGUMENT_PRESETS:
        return render_preset_input(arg_name, ARGUMENT_PRESETS[arg_name], default_value, step_id)
    
    # Priority 3: Check pattern matching (partial match)
    arg_lower = arg_name.lower()
    for pattern_key, pattern_config in ARGUMENT_PATTERNS.items():
        if pattern_key in arg_lower:
            return render_pattern_input(arg_name, pattern_config, default_value, step_id)
    
    # Priority 4: Default - Text Input
    return st.text_input(
        f"📝 {arg_name}",
        value=default_value,
        key=f"dialog_arg_{arg_name}_{step_id}",
        placeholder="Enter value or ${VARIABLE}"
    )
    if arg_type == 'text':
        col1, col2 = st.columns([4, 1])
        with col1:
            value = st.text_input(
                arg_info['name'],
                value=current_value or arg_info.get('default', ''),
                key=input_key,
                placeholder=placeholder
            )
        with col2:
            csv_value = render_csv_variable_helper(arg_info, input_key)
            if csv_value:
                st.session_state[input_key] = csv_value
                st.rerun()
        
        return value


# =================================================================================
# ===== 🎯 START: NEW SPECIALIZED UI FOR 'Verify Result of data table' KEYWORD =====
# =================================================================================

def render_verify_table_arguments_for_dialog(ws_state, timeline_key, section_name, selected_kw):
    """
    A self-contained UI for the 'Verify Result...' keyword specifically for the Add Dialog.
    It manages its own state and submission button, completely outside of an st.form.
    """
    dialog_context_id = f"add_dialog_{timeline_key}_verify_table"
    
    # --- Call the original renderer to display the inputs ---
    args_data = render_verify_table_arguments_for_edit_mode(
        ws_state=ws_state,
        unique_context_id=dialog_context_id,
        current_args={} # Always empty for a new step
    )
    
    st.markdown("---") # Add a separator

    # --- Add its own submission button ---
    if st.button(f"✅ Add Step to {section_name}", type="primary", use_container_width=True, key=f"{dialog_context_id}_submit"):
        new_step = {"id": str(uuid.uuid4()), "keyword": selected_kw['name'], "args": args_data}
        ws_state.setdefault(timeline_key, []).append(new_step)
        
        # Cleanup
        st.session_state['show_add_dialog'] = False
        if 'selected_kw' in st.session_state: del st.session_state['selected_kw']
        state_key = f"verify_table_assertions_{dialog_context_id}"
        if state_key in st.session_state: del st.session_state[state_key]
        
        st.rerun()

def render_verify_table_arguments_for_edit_mode(ws_state, unique_context_id, current_args={}):
    """
    Renders a special UI for the 'Verify Result of data table' keyword.
    Manages dynamic column assertions and returns a dictionary of all arguments.
    """
    # --- State Management for dynamic assertion rows ---
    state_key = f"verify_table_assertions_{unique_context_id}"

    def parse_args_for_ui(args):
        """Helper to parse existing flat args into structured data for the UI."""
        assertions = []
        # Find all unique column identifiers from 'col.*' keys
        col_keys = sorted([k for k in args if k.startswith('col.')])
        for col_key in col_keys:
            column_id = col_key[4:]
            if not column_id: continue
            assertions.append({
                'id': column_id,
                'col_value': args.get(col_key, column_id),
                'assert_value': args.get(f'assert.{column_id}', 'equal'),
                'expected_value': args.get(f'expected.{column_id}', '')
            })
        return assertions

    # Initialize state from current arguments if not already set
    if state_key not in st.session_state:
        st.session_state[state_key] = parse_args_for_ui(current_args)
    
    assertions = st.session_state[state_key]
    final_args = {}

    # --- 1. Render Fixed Arguments ---
    st.markdown("**Table Locators & Options**")
    fixed_arg_defs = [
        {'name': 'locator_thead', 'default': ''},
        {'name': 'locator_tbody', 'default': ''},
        {'name': 'rowdata', 'default': 'all'},
        {'name': 'ignorcase', 'default': 'true'}
    ]
    with st.container(border=True):
        grid = st.columns(2)
        i = 0
        for arg_info in fixed_arg_defs:
            with grid[i % 2]:
                arg_name = arg_info['name']
                arg_info['default'] = current_args.get(arg_name, arg_info.get('default', ''))
                final_args[arg_name] = render_argument_input(
                    arg_info, ws_state, f"{unique_context_id}_{arg_name}"
                )
            i += 1

    st.markdown("---")
    st.markdown("**Column Assertions**")
    st.caption("Define the validation rules for each column you want to check.")

    # --- 2. Render Dynamic Assertion Rows ---
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
                assertion['id'] = assertion['col_value']

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
                    assertions.pop(i)
                    st.rerun()
    
    if st.button("✚ Add Column Assertion", use_container_width=True, key=f"{unique_context_id}_add_assertion"):
        assertions.append({'id': '', 'col_value': '', 'assert_value': 'equal', 'expected_value': ''})
        st.rerun()

    # --- 3. Build final flat dictionary from the assertion list ---
    for assertion in assertions:
        column_id = assertion['id'].strip()
        if column_id:
            final_args[f"col.{column_id}"] = assertion['col_value'].strip()
            final_args[f"assert.{column_id}"] = assertion['assert_value']
            final_args[f"expected.{column_id}"] = assertion['expected_value']
            
    return final_args

# ===============================================================================
# ===== 🎯 END: NEW SPECIALIZED UI FOR 'Verify Result of data table' KEYWORD =====
# ===============================================================================

def inject_test_flow_css():
    """Enhanced CSS with modern, professional design"""
    st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <style>
        /* Section Expander Styling */
        .stExpander {
            background: rgba(30, 41, 59, 0.5);
            border: 1px solid #374151;
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 1.5rem;
        }
        
        div[data-testid="stExpander"] > div:last-child {
            background-color: rgba(15, 23, 42, 0.4);
            padding: 1.5rem 1rem;
        }

        /* Card Wrapper - Centers cards */
        .card-wrapper {
            display: flex;
            justify-content: center;
            width: 100%;
            flex-direction: column;
            align-items: center;
        }
        
        /* Modern Step Card - Softer colors */
        .step-card {
            width: 96%;
            max-width: 1200px;
            margin-bottom: 1rem;
            position: relative;
            background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%);
            border: 1px solid rgba(71, 85, 105, 0.3);
            border-radius: 12px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            overflow: hidden;
        }
        
        .step-card:hover {
            border-color: rgba(100, 116, 139, 0.5);
            transform: translateY(-2px);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
        }
        
        /* Accent Border - Left Side - More subtle */
        .step-card::before {
            content: '';
            position: absolute;
            left: 0;
            top: 0;
            bottom: 0;
            width: 4px;
            background: linear-gradient(180deg, #64748b 0%, #475569 100%);
            opacity: 0.6;
        }
        
        /* Top Accent Line - Removed for cleaner look */
        .step-card::after {
            display: none;
        }
        
        /* Header Container - Enhanced depth */
        .step-header-container {
            padding: 0.3rem 1rem;
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.8) 100%);
            border-bottom: 1px solid rgba(71, 85, 105, 0.4);
            position: relative;
            display: flex;
            align-items: center;
            min-height: 52px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4),
                        0 2px 4px rgba(0, 0, 0, 0.3) inset;
        }

        /* Header Bottom Accent Line - Subtle 3D effect */
        .step-header-container::after {
            content: '';
            position: absolute;
            left: 0;
            bottom: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, 
                transparent 0%,
                rgba(148, 163, 184, 0.3) 50%,
                transparent 100%);
        }

        /* Step Number Badge - Enhanced 3D depth */
        .step-number {
            display: flex;
            align-items: center;
            justify-content: center;
            width: 48px;
            height: 48px;
            background: linear-gradient(135deg, #52627a 0%, #3d4c5f 50%, #2d3748 100%);
            border-radius: 10px;
            font-size: 1.3rem;
            font-weight: 700;
            color: #e2e8f0;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4),
                        0 1px 2px rgba(0, 0, 0, 0.3),
                        0 0 0 1px rgba(148, 163, 184, 0.15),
                        inset 0 1px 1px rgba(255, 255, 255, 0.1),
                        inset 0 -2px 4px rgba(0, 0, 0, 0.3);
            position: relative;
            border: 1px solid rgba(71, 85, 105, 0.4);
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
        }

        .step-number::after {
            content: '';
            position: absolute;
            inset: 0;
            border-radius: 10px;
            background: linear-gradient(135deg, 
                rgba(255, 255, 255, 0.15) 0%, 
                transparent 50%, 
                rgba(0, 0, 0, 0.2) 100%);
            pointer-events: none;
        }

        /* Keyword Display */
        .step-keyword {
            display: flex;
            flex-direction: column;
            justify-content: center;
            gap: 0.3rem;
            padding: 0.5rem 0;
        }

        .step-keyword-label {
            font-size: 0.85rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #94a3b8;
        }

        .step-keyword-name {
            font-size: 1.5rem;
            font-weight: 700;
            color: #f1f5f9;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            line-height: 1.3;
        }

        .step-keyword-name::before {
            content: '⚡';
            font-size: 1rem;
        }
        
        /* Action Buttons - Enhanced 3D depth */
        .stButton > button {
            border-radius: 8px;
            border: 1px solid rgba(71, 85, 105, 0.6);
            background: linear-gradient(135deg, #3d4c5f 0%, #2d3748 50%, #1e293b 100%);
            color: #cbd5e1;
            font-weight: 600;
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            height: 36px;
            font-size: 1rem;
            padding: 0.4rem 0.5rem;
            box-shadow: 0 3px 6px rgba(0, 0, 0, 0.4),
                        0 1px 2px rgba(0, 0, 0, 0.3),
                        inset 0 1px 1px rgba(255, 255, 255, 0.1),
                        inset 0 -2px 4px rgba(0, 0, 0, 0.2);
            position: relative;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
        }
        
        .stButton > button::before {
            content: '';
            position: absolute;
            inset: 0;
            border-radius: 8px;
            background: linear-gradient(135deg, 
                rgba(255, 255, 255, 0.1) 0%, 
                transparent 50%, 
                rgba(0, 0, 0, 0.15) 100%);
            pointer-events: none;
        }
        
        .stButton > button:hover {
            background: linear-gradient(135deg, #4a5a70 0%, #3d4c5f 50%, #334155 100%);
            border-color: #64748b;
            color: #ffffff;
            transform: translateY(-2px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.5),
                        0 2px 4px rgba(0, 0, 0, 0.3),
                        inset 0 1px 2px rgba(255, 255, 255, 0.15),
                        inset 0 -2px 4px rgba(0, 0, 0, 0.2);
        }
        
        .stButton > button:active {
            transform: translateY(0px);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.4),
                        inset 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .stButton > button:disabled {
            opacity: 0.35;
            cursor: not-allowed;
            background: #1e293b;
            border-color: #334155;
            color: #64748b;
            transform: none;
        }
        .step-card-toolbar .stButton > button {
            height: 42px;
            width: 42px;
            padding: 0;
            justify-content: center;
            font-size: 1.2rem;
        }

        .step-card-toolbar .stButton > button:hover {
            /* สไตล์ตอน hover ยังคงเหมือนเดิม */
        }

        /* Card Body */
        .step-body {
            padding: 0.1rem 1.75rem 0.1rem 1.75rem;
            background: rgba(15, 23, 42, 0.4);
            border-top: 1px solid rgba(71, 85, 105, 0.2);
        }

        /* Arguments Section - Remove top spacing */
        .args-section-title {
            font-size: 0.85rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            color: #94a3b8;
            margin-bottom: 1rem;
            margin-top: 0;
            display: flex;
            align-items: center;
            gap: 0.6rem;
            padding-bottom: 0.6rem;
            padding-top: 0;
            border-bottom: 2px solid rgba(71, 85, 105, 0.3);
        }

        .args-section-title i {
            color: #64748b;
            font-size: 1.1rem;
        }
        
        /* Arguments Grid */
        .args-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 1rem;
        }
        
        @media (max-width: 768px) {
            .args-grid {
                grid-template-columns: 1fr;
            }
        }
        
        /* Argument Card - Plain style */
        .arg-card {
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.6) 0%, rgba(15, 23, 42, 0.6) 100%);
            border: 1px solid rgba(71, 85, 105, 0.3);
            border-radius: 10px;
            padding: 1rem;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }

        .arg-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: linear-gradient(90deg, #64748b 0%, #475569 100%);
            opacity: 0;
            transition: opacity 0.3s ease;
        }

        .arg-card:hover {
            border-color: rgba(100, 116, 139, 0.5);
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }

        .arg-card:hover::before {
            opacity: 0.5;
        }
        
        .arg-label {
            color: #94a3b8;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.6rem;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }

        .arg-label::before {
            content: '●';
            color: #64748b;
            font-size: 0.5rem;
        }
        
        .arg-value {
            color: #e2e8f0;
            font-size: 0.95rem;
            font-family: 'SF Mono', 'Monaco', 'Cascadia Code', 'Courier New', monospace;
            background: rgba(30, 41, 59, 0.5);
            padding: 0.75rem 0.85rem;
            border-radius: 8px;
            border: 1px solid rgba(71, 85, 105, 0.2);
            word-break: break-word;
            line-height: 1.5;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.2) inset;
        }
        
        /* No Arguments State */
        .no-args {
            text-align: center;
            padding: 2.5rem 1.5rem;
            color: #64748b;
            font-style: italic;
            font-size: 0.95rem;
            grid-column: 1 / -1;
            background: rgba(30, 41, 59, 0.3);
            border-radius: 10px;
            border: 2px dashed rgba(71, 85, 105, 0.3);
        }
        
        .no-args i {
            display: block;
            font-size: 2.5rem;
            margin-bottom: 0.75rem;
            opacity: 0.25;
            color: #475569;
        }
        
        /* Edit Section - Softer background */
        .edit-section {
            padding: 1.5rem 2rem;
            background: rgba(30, 41, 59, 0.3);
            border-top: 1px solid rgba(71, 85, 105, 0.3);
        }
        
        /* Keyword Info Box - Softer accent */
        .keyword-info {
            background: rgba(30, 41, 59, 0.4);
            border-left: 3px solid #64748b;
            padding: 1.25rem;
            border-radius: 10px;
            margin-bottom: 1.25rem;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        }
        
        .keyword-info-title {
            font-weight: 700;
            color: #cbd5e1;
            font-size: 1.05rem;
            margin-bottom: 0.5rem;
        }

        /* Responsive adjustments */
        @media (max-width: 1024px) {
            .step-card {
                width: 98%;
            }
            
            .step-header-container {
                padding: 1rem 1.25rem;
            }
            
            .step-body {
                padding: 0.5rem 0.5rem;
            }
        }
    </style>
    """, unsafe_allow_html=True)

def render_step_card(step, index, timeline_key, total_steps):
    """Render enhanced step card with modern design and collapsible arguments"""
    edit_mode = st.session_state.get(f'edit_mode_{step["id"]}', False)
    expanded_key = f'expanded_{step["id"]}'
    if expanded_key not in st.session_state:
        valid_args = {k: v for k, v in step.get('args', {}).items() if v}
        st.session_state[expanded_key] = bool(valid_args)

    st.markdown("<div class='step-card'>", unsafe_allow_html=True)

    # === CARD HEADER ===
    num_col, kw_col, btn_col = st.columns([0.1, 0.55, 0.35], vertical_alignment="center")

    with num_col:
        # ทำให้ markdown เรียบง่ายขึ้น ไม่ต้องมี div จัดตำแหน่งซ้อนกัน
        st.markdown(f"<div class='step-number'>{index + 1}</div>", unsafe_allow_html=True)

    with kw_col:
        st.markdown(f"""
        <div class='step-keyword'>
            <div class='step-keyword-label'>KEYWORD</div>
            <div class='step-keyword-name' style="color: #58a6ff;">{step.get('keyword', 'N/A')}</div>
        </div>
        """, unsafe_allow_html=True)

    with btn_col:
        toolbar = st.container()
        with toolbar:
            st.markdown("<div class='step-card-toolbar'>", unsafe_allow_html=True)
            btn_cols = st.columns([1, 1, 1, 1, 1, 1], gap="small")

            # สมมติว่ามีตัวแปรพวกนี้อยู่แล้ว
            expand_icon = "🔽" if st.session_state.get("expanded_key", False) else "▶️"

            with btn_cols[0]:
                if st.button(label=" ", icon=expand_icon, key=f"expand_{step['id']}", help="Toggle details", use_container_width=True):
                    st.session_state[expanded_key] = not st.session_state[expanded_key]
                    st.rerun()

            with btn_cols[1]:
                is_first = (index == 0)
                if st.button(label=" ", icon="⬆️", key=f"up_{step['id']}", help="Move up", use_container_width=True, disabled=is_first):
                    st.session_state.studio_workspace[timeline_key].insert(index - 1, st.session_state.studio_workspace[timeline_key].pop(index))
                    st.rerun()

            with btn_cols[2]:
                is_last = (index == total_steps - 1)
                if st.button(label=" ", icon="⬇️", key=f"down_{step['id']}", help="Move down", use_container_width=True, disabled=is_last):
                    st.session_state.studio_workspace[timeline_key].insert(index + 1, st.session_state.studio_workspace[timeline_key].pop(index))
                    st.rerun()

            with btn_cols[3]:
                if st.button(label=" ", icon="✏️", key=f"edit_{step['id']}", help="Edit", use_container_width=True):
                    st.session_state[f'edit_mode_{step["id"]}'] = not edit_mode
                    st.rerun()

            with btn_cols[4]:
                if st.button(label=" ", icon="📋", key=f"copy_{step['id']}", help="Duplicate", use_container_width=True):
                    new_step = step.copy()
                    new_step['id'] = str(uuid.uuid4())
                    st.session_state.studio_workspace[timeline_key].insert(index + 1, new_step)
                    st.rerun()

            with btn_cols[5]:
                if st.button(label=" ", icon="🗑️", key=f"del_{step['id']}", help="Delete", use_container_width=True):
                    st.session_state.studio_workspace[timeline_key] = [
                        s for s in st.session_state.studio_workspace[timeline_key] if s.get('id') != step['id']
                    ]
                    st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

    # === CARD BODY ===
    # แสดง body เฉพาะเมื่อ expanded เท่านั้น
    if st.session_state[expanded_key]:
        if not edit_mode:
            st.markdown("<div class='step-body'>", unsafe_allow_html=True)
            valid_args = {k: v for k, v in step.get('args', {}).items() if v}
            
            if valid_args:
                st.markdown("<div class='args-section-title'><i class='fas fa-cog'></i>Arguments</div>", unsafe_allow_html=True)
                args_html = "<div class='args-grid'>" + "".join([
                    f"<div class='arg-card'>"
                    f"<div class='arg-label'>{k}</div>"
                    f"<div class='arg-value'>{str(v).replace('<', '&lt;').replace('>', '&gt;')}</div>"
                    f"</div>"
                    for k, v in valid_args.items()
                ]) + "</div>"
                st.markdown(args_html, unsafe_allow_html=True)
            else:
                st.markdown("<div class='args-grid'><div class='no-args'><i class='fas fa-inbox'></i>No arguments provided</div></div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            # Edit Mode
            st.markdown("<div class='edit-section'>", unsafe_allow_html=True)
            ws_state = st.session_state.studio_workspace
            if ws_state.get('keywords'):
                ws_state['categorized_keywords'] = categorize_keywords(ws_state['keywords'])
            categorized_keywords = ws_state.get('categorized_keywords', {})
            all_kws = [kw for kws in categorized_keywords.values() for kw in kws]
            st.markdown("##### 🔧 Edit Step")
            all_kw_names = [kw['name'] for kw in all_kws]
            current_index = all_kw_names.index(step.get('keyword')) if step.get('keyword') in all_kw_names else 0
            selected_kw_name = st.selectbox("Select Keyword", all_kw_names, index=current_index, key=f"kw_select_{step['id']}")
            selected_kw = next((kw for kw in all_kws if kw['name'] == selected_kw_name), None)

            if selected_kw: # ตรวจสอบแค่ว่ามี selected_kw หรือไม่
                # =========================================================================
                # ===== 🎯 START: MODIFICATION FOR 'Verify Result of data table' KEYWORD =====
                # =========================================================================
                if selected_kw_name.strip() == 'Verify Result of data table':
                    # Use the specialized UI renderer for this keyword
                    new_args = render_verify_table_arguments_for_edit_mode(
                        ws_state=ws_state,
                        unique_context_id=step['id'],
                        current_args=step.get('args', {})
                    )
                else:
                    # Use the original logic for all other keywords
                    new_args = {}
                    if selected_kw.get('args'):
                        st.markdown("**Arguments:**")
                        for i, arg_item in enumerate(selected_kw.get('args', [])):
                            arg_info = arg_item.copy() if isinstance(arg_item, dict) else {'name': str(arg_item), 'default': ''}
                            raw_arg_name = arg_info.get('name')
                            if not raw_arg_name: continue

                            clean_arg_name = raw_arg_name.strip('${}')
                            arg_info['name'] = clean_arg_name
                            
                            current_val = step.get('args', {}).get(clean_arg_name, arg_info.get('default', ''))
                            arg_info['default'] = current_val

                            new_args[clean_arg_name] = render_argument_input(
                                arg_info, ws_state, f"{step['id']}_{clean_arg_name}"
                            )
                # =======================================================================
                # ===== 🎯 END: MODIFICATION FOR 'Verify Result of data table' KEYWORD =====
                # =======================================================================

                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Save Changes", key=f"save_{step['id']}", use_container_width=True):
                        for i, s in enumerate(st.session_state.studio_workspace[timeline_key]):
                            if s['id'] == step['id']:
                                st.session_state.studio_workspace[timeline_key][i]['keyword'] = selected_kw_name
                                st.session_state.studio_workspace[timeline_key][i]['args'] = new_args
                                break
                        st.session_state[f'edit_mode_{step["id"]}'] = False
                        st.rerun()
                with col2:
                    if st.button("❌ Cancel", key=f"cancel_{step['id']}", use_container_width=True):
                        st.session_state[f'edit_mode_{step["id"]}'] = False
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)

def render_timeline_section(title, timeline_key, section_name):
    """Renders a collapsible section with card wrapper"""
    ws_state = st.session_state.studio_workspace
    timeline = ws_state.get(timeline_key, [])
    
    with st.expander(f"**{title}** ({len(timeline)} steps)", expanded=True):
        if not timeline:
            st.info(f"No steps in {section_name}. Click below to add one.")
        else:
            st.markdown("<div class='card-wrapper'>", unsafe_allow_html=True)
            
            for i, step in enumerate(timeline):
                render_step_card(step, i, timeline_key, len(timeline))
            
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("<div class='card-wrapper'><div style='width:96%; max-width:1200px;'>", unsafe_allow_html=True)
        if st.button(f"⊕ Add New Step to {section_name}", key=f"add_{timeline_key}", use_container_width=True):
            st.session_state['show_add_dialog'] = True
            st.session_state['add_dialog_timeline'] = timeline_key
            st.session_state['add_dialog_section'] = section_name
            st.rerun()
        st.markdown("</div></div>", unsafe_allow_html=True)

@st.dialog("Add New Step", width="large")
def render_add_step_dialog():
    """
    Renders the dialog with the compact list design, now using the updated
    icon set (⚡ for quick add, ⚙️ for configuration).
    """

    """
    Renders the dialog, fixing the ghost button issue by adding
    'position: relative' to the wrapper.
    """

    # --- 🎨 CSS ---
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display.swap');
        .stApp {
            font-family: 'Inter', sans-serif;
        }
        .info-banner {
            background-color: #1e293b; padding: 0.75rem 1rem; border-radius: 8px;
            margin-bottom: 1.5rem; border-left: 4px solid #6366f1;
        }
        .info-banner-title {
            font-size: 0.8rem; color: #a1a1aa; font-weight: 600;
            text-transform: uppercase; letter-spacing: 0.5px;
        }
        .info-banner-content { font-size: 1.1rem; color: #f4f4f5; font-weight: 700; }
        
        .placeholder-box {
            text-align: center; padding: 3rem 2rem; color: #71717a;
            background-color: #18181b; border: 2px dashed #3f3f46;
            border-radius: 12px; margin-top: 1rem;
        }

        /* --- Style for the container of our custom button --- */
        div[data-testid="stButton"] {
            margin: 3px 0; /* Add vertical spacing between buttons */
        }
        
        /* --- This is the core of the new method --- */
        /* Target the actual <button> element */
        div[data-testid="stButton"] > button {
            display: flex;
            align-items: center;
            justify-content: flex-start; /* Align text to the left */
            width: 100%;
            padding: 0.6rem 1rem;
            border-radius: 7px;
            border: 1px solid #3f3f46;
            background-color: #27272a;
            color: #e4e4e7;
            font-weight: 500;
            font-size: 0.95rem;
            text-align: left;
            transition: all 0.2s ease-in-out;
        }
        
        /* --- Hover and Active States for the button --- */
        div[data-testid="stButton"] > button:hover {
            border-color: #6366f1;
            background-color: #3f3f46;
            color: #ffffff;
        }
        
        div[data-testid="stButton"] > button:focus:not(:active) {
             border-color: #6366f1 !important;
             box-shadow: 0 0 0 1px #6366f1 !important;
        }

        /* Style for the button when its keyword is selected */
        .stButton button.active-keyword {
             background-color: #4338ca; 
             border-color: #818cf8; 
             color: #ffffff;
             box-shadow: 0 0 12px rgba(99, 102, 241, 0.25);
        }

    </style>
    """, unsafe_allow_html=True)

    # --- Python Logic ---
    ws_state = st.session_state.studio_workspace
    timeline_key = st.session_state.get('add_dialog_timeline')
    section_name = st.session_state.get('add_dialog_section')

    all_keywords_list = ws_state.get('keywords', [])
    if all_keywords_list and 'categorized_keywords' not in ws_state:
        ws_state['categorized_keywords'] = categorize_keywords(all_keywords_list)
    categorized_keywords = ws_state.get('categorized_keywords', {})
    keyword_map = {kw['name']: kw for kw in all_keywords_list}

    if 'selected_kw' not in st.session_state: st.session_state.selected_kw = None
    if 'recently_used_keywords' not in st.session_state: st.session_state.recently_used_keywords = []

    st.markdown(f"""
        <div class='info-banner'>
            <div class='info-banner-title'>Adding to</div>
            <div class='info-banner-content'>{section_name}</div>
        </div>
    """, unsafe_allow_html=True)

    left_col, right_col = st.columns([1, 1], gap="large")

    with left_col:
        st.markdown("### 🔍 Select Keyword")
        search_query = st.text_input("Search", key="kw_search_dialog", placeholder="Type to filter keywords...", label_visibility="collapsed").lower()

        # --- SIMPLIFIED RENDER FUNCTION ---
        def render_keyword_row(kw, key_prefix):
            has_args = bool(kw.get('args'))
            icon = "⚡" if not has_args else "⚙️"
            is_active = st.session_state.selected_kw and st.session_state.selected_kw['name'] == kw['name']
            
            # The button's label now includes the icon and text
            button_label = f"{icon}  {kw['name']}"
            
            # Use a single st.button and apply a class if it's active
            if st.button(button_label, key=f"{key_prefix}_kw_btn_{kw['name']}", use_container_width=True, type="secondary"):
                if kw['name'] in st.session_state.recently_used_keywords:
                    st.session_state.recently_used_keywords.remove(kw['name'])
                st.session_state.recently_used_keywords.insert(0, kw['name'])
                if not has_args:
                    new_step = {"id": str(uuid.uuid4()), "keyword": kw['name'], "args": {}}
                    ws_state.setdefault(timeline_key, []).append(new_step)
                    st.session_state['show_add_dialog'] = False
                    if 'selected_kw' in st.session_state: del st.session_state.selected_kw
                    st.toast(f"✅ Step '{kw['name']}' added!", icon="🎉")
                    st.rerun()
                else:
                    st.session_state.selected_kw = kw
                    st.session_state['scroll_to_top'] = True 
                    st.rerun()
            
            # A little trick to apply the 'active' style after the button is rendered
            if is_active:
                st.markdown(
                    f'<style>.stButton button[data-testid="stButton-secondary-{key_prefix}_kw_btn_{kw["name"]}"] {{ background-color: #4338ca; border-color: #818cf8; color: #ffffff; }}</style>',
                    unsafe_allow_html=True
                )


        recent_kws_names = st.session_state.recently_used_keywords[:3]
        if recent_kws_names:
            st.markdown("##### 📌 Recently Used")
            for kw_name in recent_kws_names:
                if kw := keyword_map.get(kw_name):
                    render_keyword_row(kw, key_prefix="recent")
            st.divider()
        
        st.markdown("##### All Keywords")
        if not categorized_keywords:
            st.warning("⚠️ No keywords loaded.")
        else:
            for category, keywords in sorted(categorized_keywords.items()):
                filtered_kws = [kw for kw in keywords if search_query in kw['name'].lower()]
                if filtered_kws:
                    with st.expander(f"{category} ({len(filtered_kws)})", expanded=bool(search_query)):
                        for kw in filtered_kws:
                            render_keyword_row(kw, key_prefix="all")
    
    # --- Right Column (Unchanged) ---
    with right_col:   
        if st.session_state.get('scroll_to_top'):
            st.components.v1.html("""
                <script>
                    window.parent.scrollTo({ top: 0, behavior: 'smooth' });
                </script>
            """, height=0)
            st.session_state['scroll_to_top'] = False
        
        selected_kw = st.session_state.get('selected_kw')
        if selected_kw:
            st.markdown(f"##### 2. Configure Arguments")
            st.markdown(f"<div class='keyword-info'><div class='keyword-info-title'>{selected_kw['name']}</div>{selected_kw.get('doc', 'No doc.')}</div>", unsafe_allow_html=True)
            
            # =================== ✨✨✨ START: NEW LOGIC ✨✨✨ ===================
            # Check for the special keyword FIRST
            if selected_kw['name'].strip() == 'Verify Result of data table':
                # If it's the special keyword, render its self-contained UI WITHOUT a form
                render_verify_table_arguments_for_dialog(ws_state, timeline_key, section_name, selected_kw)

            else:
                # For ALL OTHER keywords, use the st.form as before
                with st.form(key="step_form"):
                    args_data = {}
                    if selected_kw.get('args'):
                        for i, arg_item in enumerate(selected_kw.get('args', [])):
                            arg_info = arg_item.copy() if isinstance(arg_item, dict) else {'name': str(arg_item), 'default': ''}
                            raw_arg_name = arg_info.get('name')
                            if not raw_arg_name: continue
                            
                            clean_arg_name = raw_arg_name.strip('${}')
                            arg_info['name'] = clean_arg_name
                            unique_key = f"dialog_{selected_kw['name']}_{clean_arg_name}_{i}"
                            args_data[clean_arg_name] = render_argument_input(arg_info, ws_state, unique_key)

                    if st.form_submit_button(f"✅ Add Step to {section_name}", type="primary", use_container_width=True):
                        new_step = {"id": str(uuid.uuid4()), "keyword": selected_kw['name'], "args": args_data}
                        ws_state.setdefault(timeline_key, []).append(new_step)
                        
                        st.session_state['show_add_dialog'] = False
                        if 'selected_kw' in st.session_state: del st.session_state['selected_kw']
                        st.rerun()
        else:
            st.markdown("<div style='text-align:center; padding:3rem; color:#6b7280;'><i class='fas fa-arrow-left' style='font-size:2rem; margin-bottom:1rem; display:block;'></i><p>Select a keyword from the left.</p></div>", unsafe_allow_html=True)

def generate_full_script(ws_state):
    """
    Assembles the final Robot Framework script from the workspace state,
    intelligently handling Suite Setup/Teardown and formatting empty arguments as ${EMPTY}.
    """

    def format_single_step_line(step):
        """
        Helper to format a single step object into a string with its keyword and named arguments.
        Handles special multi-line formatting for 'Verify Result of data table'.
        """
        keyword = step.get('keyword', '')
        args = step.get('args', {})

        # --- ✨✨✨ START: NEW LOGIC FOR SPECIAL KEYWORD ✨✨✨ ---
        if keyword.strip() == 'Verify Result of data table':
            # 1. แยก arguments ออกเป็น 2 กลุ่ม: fixed และ columns
            fixed_args = {}
            col_args = {}
            for k, v in args.items():
                if k.startswith('col.') or k.startswith('assert.') or k.startswith('expected.'):
                    col_args[k] = v
                else:
                    fixed_args[k] = v

            # --- Helper function for formatting a single value ---
            def format_value(arg_name, arg_value):
                if arg_value == "": return "${EMPTY}"
                if arg_value is None: return None
                is_locator = any(s in arg_name.lower() for s in ['locator', 'field', 'button', 'element', 'menu'])
                if is_locator and not str(arg_value).startswith('${'):
                    return f"${{{arg_value}}}"
                return arg_value

            # 2. สร้างบรรทัดแรก (Keyword + Fixed arguments)
            first_line_parts = [keyword]
            for name, value in fixed_args.items():
                formatted_val = format_value(name, value)
                if formatted_val is not None:
                    first_line_parts.append(f"{name}={formatted_val}")
            
            # 3. จัดกลุ่มและสร้างบรรทัดสำหรับแต่ละ Column Assertion
            column_lines = []
            # หาชื่อ column ที่ไม่ซ้ำกันจาก key 'col.*'
            column_ids = sorted(list(set([k.split('.')[1] for k in col_args if k.startswith('col.')])))
            
            for col_id in column_ids:
                line_parts = ["..."]
                
                # เรียงลำดับ col, assert, expected ให้สวยงาม
                col_name = f"col.{col_id}"
                assert_name = f"assert.{col_id}"
                expected_name = f"expected.{col_id}"
                
                # เพิ่ม col.*
                val = format_value(col_name, col_args.get(col_name))
                if val is not None: line_parts.append(f"{col_name}={val}")

                # เพิ่ม assert.*
                val = format_value(assert_name, col_args.get(assert_name))
                if val is not None: line_parts.append(f"{assert_name}={val}")

                # เพิ่ม expected.*
                val = format_value(expected_name, col_args.get(expected_name))
                if val is not None: line_parts.append(f"{expected_name}={val}")
                
                column_lines.append("    ".join(line_parts))

            # 4. รวมทุกบรรทัดเข้าด้วยกัน แล้วส่งกลับเป็น string เดียว
            final_output = "    ".join(first_line_parts)
            if column_lines:
                final_output += "\n" + "\n".join(column_lines)
            return final_output
        # --- ✨✨✨ END: NEW LOGIC FOR SPECIAL KEYWORD ✨✨✨ ---

        # --- Original logic for all other keywords ---
        line_parts = [keyword]
        for arg_name, arg_value in args.items():
            formatted_value = ""
            if arg_value == "":
                formatted_value = "${EMPTY}"
            elif arg_value is not None:
                is_locator_arg = any(substr in arg_name.lower() for substr in ['locator', 'field', 'button', 'element', 'menu'])
                if is_locator_arg and not str(arg_value).startswith('${'):
                    formatted_value = f"${{{arg_value}}}"
                else:
                    formatted_value = arg_value
            else:
                continue
            line_parts.append(f"{arg_name}={formatted_value}")
        
        return "    ".join(line_parts)

    # --- 1. Collect all used locators from all sections ---
    all_steps = ws_state.get('suite_setup', []) + ws_state.get('timeline', []) + ws_state.get('suite_teardown', [])
    used_locator_names = set()
    for step in all_steps:
        for arg_name, arg_value in step.get('args', {}).items():
            is_locator_arg = any(substr in arg_name.lower() for substr in ['locator', 'field', 'button', 'element', 'menu'])
            if is_locator_arg and arg_value and arg_value != '${EMPTY}':
                used_locator_names.add(arg_value)

    # --- 2. Build *** Settings *** section ---
    settings_section = ["*** Settings ***"]
    if ws_state.get('common_keyword_path'):
        settings_section.append(f"Resource          ../../resources/commonkeywords.resource")

    # Logic for Suite Setup
    setup_steps = ws_state.get('suite_setup', [])
    if len(setup_steps) == 1:
        settings_section.append(f"Suite Setup       {format_single_step_line(setup_steps[0])}")
    elif len(setup_steps) > 1:
        first_line = format_single_step_line(setup_steps[0])
        settings_section.append(f"Suite Setup       Run Keywords    {first_line}")
        for step in setup_steps[1:]:
            settings_section.append(f"...    AND    {format_single_step_line(step)}")

    # Logic for Suite Teardown
    teardown_steps = ws_state.get('suite_teardown', [])
    if len(teardown_steps) == 1:
        settings_section.append(f"Suite Teardown    {format_single_step_line(teardown_steps[0])}")
    elif len(teardown_steps) > 1:
        first_line = format_single_step_line(teardown_steps[0])
        settings_section.append(f"Suite Teardown    Run Keywords    {first_line}")
        for step in teardown_steps[1:]:
            settings_section.append(f"...    AND    {format_single_step_line(step)}")

    # --- 3. Build *** Variables *** section ---
    variables_section = ["\n*** Variables ***"]
    used_locators = [loc for loc in ws_state.get('locators', []) if loc['name'] in used_locator_names]
    if used_locators:
        max_len = max((len(f"${{{loc['name']}}}") for loc in used_locators), default=20) + 4
        for loc in sorted(used_locators, key=lambda x: x['name']):
            variables_section.append(f"{f'${{{loc['name']}}}'.ljust(max_len)}{loc['value']}")

    # --- 4. Build *** Test Cases *** section ---
    test_cases_section = ["\n*** Test Cases ***"]
    test_cases_section.append("Generated Visual Test Case")
    
    timeline_steps = ws_state.get('timeline', [])
    if not timeline_steps:
        test_cases_section.append("    Log    No steps in test case.")
    else:
        for step in timeline_steps:
            # format_single_step_line อาจคืนค่ามาหลายบรรทัด
            formatted_lines_str = format_single_step_line(step)
            
            # แยกแต่ละบรรทัดออกจากกัน
            lines = formatted_lines_str.split('\n')
            
            # บรรทัดแรกต้องย่อหน้าด้วย 4 spaces
            test_cases_section.append(f"    {lines[0]}")
            
            # บรรทัดที่เหลือ (ที่ขึ้นต้นด้วย ... อยู่แล้ว) ก็ต้องย่อหน้าด้วย 4 spaces เช่นกัน
            if len(lines) > 1:
                for line in lines[1:]:
                    test_cases_section.append(f"    {line}")

    # --- 5. Combine all sections ---
    final_script_parts = []
    final_script_parts.extend(settings_section)
    if len(variables_section) > 1:
        final_script_parts.extend(variables_section)
    final_script_parts.extend(test_cases_section)
    
    return "\n".join(final_script_parts)

def render_test_flow_tab():
    inject_test_flow_css()
    ws_state = st.session_state.studio_workspace
    
    if st.session_state.get('show_add_dialog'):
        render_add_step_dialog()

    left_col, right_col = st.columns([0.6, 0.4], gap="large")

    with left_col:
        st.markdown("<h4 style='font-size: 1.6rem;'>📈 Test Flow Builder</h4>", unsafe_allow_html=True)
        render_timeline_section("🛠️ Setup", "suite_setup", "Setup")
        render_timeline_section("▶️ Test Case", "timeline", "Test Case")
        render_timeline_section("🧹 Teardown", "suite_teardown", "Teardown")

    with right_col:
        st.markdown("<h4 style='font-size: 1.6rem;'>🚀 Generated Script</h4>", unsafe_allow_html=True)
        if any(ws_state.get(key) for key in ['timeline', 'suite_setup', 'suite_teardown']):
            final_script = generate_full_script(ws_state)
            # --- ✅ FIX: Changed variable name from 'script' to 'final_script' ---
            st.code(final_script, language='robotframework', line_numbers=True)
            st.download_button(
                label="📥 Download Script", 
                data=final_script, 
                file_name="generated_test.robot", 
                mime="text/plain",
                use_container_width=True,
                type="primary"
            )
        else:
            st.info("Add some steps to generate the script.")