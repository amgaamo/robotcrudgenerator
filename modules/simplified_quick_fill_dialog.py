import streamlit as st
from typing import Dict, List, Set
import re


# ============================================================
# 🎯 SECTION 1: AUTO-GROUPING BY PAGE
# ============================================================

def group_locators_by_page_name(all_locators: List[Dict]) -> Dict[str, List[Dict]]:
    """Group locators by their 'page_name' attribute."""
    groups = {}
    ungrouped = []
    
    for loc in all_locators:
        page_name = loc.get('page_name')
        
        if page_name:
            display_name = clean_page_name_for_display(page_name)
            if display_name not in groups:
                groups[display_name] = []
            groups[display_name].append(loc)
        else:
            ungrouped.append(loc)
    
    if ungrouped:
        groups["🔹 No Page"] = ungrouped
    
    sorted_groups = dict(sorted(
        groups.items(),
        key=lambda x: ('zzz' if '🔹' in x[0] else x[0].lower())
    ))
    
    return sorted_groups


def clean_page_name_for_display(page_name: str) -> str:
    """Clean up page name for better display."""
    import os
    base_name = os.path.basename(page_name)
    name_without_ext = os.path.splitext(base_name)[0]
    display_name = name_without_ext.replace('_', ' ').title()
    return display_name


def auto_select_form_fields(locators: List[Dict]) -> List[str]:
    """Auto-select locators that are likely form inputs."""
    FORM_KEYWORDS = [
        '_INPUT', '_TEXTFIELD','_SELECT','_SEL','_CHECKBOX','_RADIO','_DATE','_FILE',
        '_LINK'
    ]
    
    EXCLUDE_KEYWORDS = [
        'BUTTON', 'BTN', 'LINK', 'ICON', 'IMAGE', 'LABEL', 'HEADER', 
        'FOOTER', 'MENU', 'TAB', 'MODAL', 'DIALOG', 'ALERT',
        'TITLE', 'ERROR', 'MSG', 'VALIDATION', 'INVALID', 'EMPTY', 'SEARCH'
    ]
    
    auto_selected = []
    
    for loc in locators:
        loc_name = loc['name'].upper()
        should_exclude = any(exclude_kw in loc_name for exclude_kw in EXCLUDE_KEYWORDS)
        if should_exclude:
            continue
        
        is_form_field = any(form_kw in loc_name for form_kw in FORM_KEYWORDS)
        if is_form_field:
            auto_selected.append(loc['name'])
    
    return auto_selected


def get_clean_locator_name(raw_name: str) -> str:
    """Remove LOCATOR_ prefix for display."""
    if raw_name.startswith('LOCATOR_'):
        return raw_name[8:]
    return raw_name


# ============================================================
# 🎯 SECTION 2: MAIN DIALOG
# ============================================================

def render_kw_factory_fill_form_dialog():
    """Simplified Quick Fill Form Dialog - Compact One-Page UI"""
    from .utils import FILL_FORM_DEFAULTS
    from modules import kw_manager
    
    ws_state = st.session_state.studio_workspace
    context = st.session_state.get('kw_factory_add_dialog_context', {})
    keyword_id = context.get("key")
    
    if not keyword_id:
        st.error("Error: Keyword context not found.")
        if st.button("Close"):
            st.session_state.show_kw_factory_fill_form_dialog = False
            st.rerun()
        return
    
    # Session state keys
    dialog_key = f"simplified_fill_{keyword_id}"
    selected_page_key = f"{dialog_key}_selected_page"
    selected_fields_key = f"{dialog_key}_selected_fields"
    ant_design_key = f"{dialog_key}_ant_design"
    configs_key = f"{dialog_key}_configs"
    
    # Initialize states
    if selected_page_key not in st.session_state:
        st.session_state[selected_page_key] = None
    if selected_fields_key not in st.session_state:
        st.session_state[selected_fields_key] = []
    if ant_design_key not in st.session_state:
        st.session_state[ant_design_key] = False
    if configs_key not in st.session_state:
        st.session_state[configs_key] = {}
    
    # Get all locators
    all_locators = ws_state.get('locators', [])
    if not all_locators:
        st.warning("⚠️ No locators found in Assets. Please add locators first.")
        if st.button("❌ Close", use_container_width=True):
            cleanup_dialog_state(dialog_key)
            st.session_state.show_kw_factory_fill_form_dialog = False
            st.rerun()
        return
    
    # Group locators by page
    grouped_locators = group_locators_by_page_name(all_locators)
    page_names = list(grouped_locators.keys())
    
    # ====== HEADER ======
    st.markdown("### ✏️ Quick Fill Form")
    
    # ====== Page Selection ======
    current_page = st.session_state[selected_page_key]
    page_options = ["--- select ---"] + page_names
    
    if not current_page or current_page not in page_names:
        default_index = 0
    else:
        default_index = page_options.index(current_page)
    
    selected_page = st.selectbox(
        "📄 Page:",
        options=page_options,
        index=default_index,
        key=f"{dialog_key}_page_dropdown"
    )
    
    # Check if page is selected
    if selected_page == "--- select ---":
        st.info("👆 Please select a page to continue")
        if st.button("❌ Close", use_container_width=True):
            cleanup_dialog_state(dialog_key)
            st.session_state.show_kw_factory_fill_form_dialog = False
            st.rerun()
        return
    
    # Detect page change and auto-select fields
    if selected_page != st.session_state[selected_page_key]:
        st.session_state[selected_page_key] = selected_page
        page_locators = grouped_locators[selected_page]
        auto_selected = auto_select_form_fields(page_locators)
        st.session_state[selected_fields_key] = auto_selected

        st.session_state[configs_key] = {} # <-- [FIX] เพิ่มบรรทัดนี้เพื่อเคลียร์ Configs เก่า

        for loc_name in auto_selected:
            if loc_name not in st.session_state[configs_key]:
                st.session_state[configs_key][loc_name] = FILL_FORM_DEFAULTS.copy()
        st.rerun()
    
    st.markdown("---")
    
    # ====== SECTION 1: SELECTED FIELDS (COMPACT CHIPS) ======
    page_locators = grouped_locators[selected_page]
    page_locator_names = [loc['name'] for loc in page_locators]
    selected_fields = st.session_state[selected_fields_key]
    
    # Remove duplicates
    unique_fields = []
    seen = set()
    for field_name in selected_fields:
        if field_name not in seen:
            unique_fields.append(field_name)
            seen.add(field_name)
    
    if len(unique_fields) != len(selected_fields):
        st.session_state[selected_fields_key] = unique_fields
        selected_fields = unique_fields
    
    # Display selected fields
    if selected_fields:
        
        # --- START: เพิ่มช่องค้นหาสำหรับ Selected Fields ---
        search_selected_key = f"{dialog_key}_search_selected"
        search_query_selected = st.text_input(
            f"🔎 Search Selected Fields ({len(selected_fields)} total)",
            key=search_selected_key,
            placeholder="Type to filter selected fields..."
        )

        if search_query_selected:
            fields_to_display = [
                loc_name for loc_name in selected_fields 
                if search_query_selected.upper() in get_clean_locator_name(loc_name).upper()
            ]
        else:
            fields_to_display = selected_fields
        # --- END: เพิ่มช่องค้นหา ---

        col_title, col_add = st.columns([3, 1])
        # with col_title:
        #     st.markdown(f"**📋 Selected:** {len(fields_to_display)} fields")
        with col_add:
            if st.button("➕ Add More", key=f"{dialog_key}_add_btn", use_container_width=True):
                st.session_state[f"{dialog_key}_show_add_field"] = True
                st.rerun()
        
        # Compact field chips (3 per row with inline X button)
        num_cols = 3
        
        # --- แก้ไข: ใช้ fields_to_display ---
        for i in range(0, len(fields_to_display), num_cols):
            cols = st.columns(num_cols)
            for j in range(num_cols):
                idx = i + j
                if idx < len(fields_to_display):
                    field_name = fields_to_display[idx]
        # --- สิ้นสุดการแก้ไข ---
                    clean_name = get_clean_locator_name(field_name)
                    
                    with cols[j]:
                        subcol1, subcol2 = st.columns([5, 1])
                        with subcol1:
                            st.markdown(
                                f'<div style="background:#1e3a5f;padding:5px 10px;border-radius:5px;'
                                f'font-size:0.85em;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;" '
                                f'title="{field_name}">🔹 {clean_name}</div>',
                                unsafe_allow_html=True
                            )
                        with subcol2:
                            # --- แก้ไข: ใช้ field_name ใน key เพื่อให้ลบได้ถูกต้อง ---
                            if st.button("❌", key=f"{dialog_key}_rm_{field_name}", help=f"Remove {clean_name}"):
                                st.session_state[selected_fields_key].remove(field_name)
                                if field_name in st.session_state[configs_key]:
                                    del st.session_state[configs_key][field_name]
                                st.rerun()
    else:
        st.info("No fields selected.")
        if st.button("➕ Add Fields", key=f"{dialog_key}_add_btn_empty", use_container_width=True):
            st.session_state[f"{dialog_key}_show_add_field"] = True
            st.rerun()
    
    # Add Field Dialog
    if st.session_state.get(f"{dialog_key}_show_add_field", False):
        # ⚠️ CRITICAL: Check clear flag FIRST - BEFORE ANY UI RENDERING
        clear_flag_key = f"{dialog_key}_clear_flag"
        search_key = f"{dialog_key}_search_fields"
        
        if clear_flag_key not in st.session_state:
            st.session_state[clear_flag_key] = False
        
        # Handle clear action immediately (before any widgets)
        if st.session_state.get(clear_flag_key, False):
            st.session_state[clear_flag_key] = False
            # Delete search state to clear the input box
            if search_key in st.session_state:
                del st.session_state[search_key]
            st.rerun()
        
        # Now safe to render UI
        st.markdown("---")
        st.markdown("**🔍 Select Additional Fields:**")
        
        available_to_add = [loc_name for loc_name in page_locator_names if loc_name not in selected_fields]
        
        if available_to_add:
            # Search box with smaller font
            st.markdown("""
                <style>
                .stTextInput input {
                    font-size: 0.9em;
                }
                div[data-testid="stCheckbox"] label p {
                    font-size: 0.8em !important;
                }
                </style>
            """, unsafe_allow_html=True)
            
            search_query = st.text_input(
                "🔎 Search fields:",
                key=search_key,
                placeholder="Type to filter fields...",
                help="Search by field name"
            )
            
            # Filter fields based on search query
            if search_query:
                filtered_fields = [
                    loc_name for loc_name in available_to_add 
                    if search_query.upper() in get_clean_locator_name(loc_name).upper()
                ]
                st.caption(f"✓ Found {len(filtered_fields)} fields matching '{search_query}'")
            else:
                filtered_fields = available_to_add
                st.caption(f"📝 {len(filtered_fields)} fields available")
            
            # Display filtered fields in 4 columns (smaller text)
            if filtered_fields:
                add_cols = st.columns(4)
                for add_idx, loc_name in enumerate(filtered_fields):
                    col_idx = add_idx % 4
                    with add_cols[col_idx]:
                        if st.checkbox(
                            get_clean_locator_name(loc_name), 
                            key=f"{dialog_key}_add_{add_idx}_{hash(loc_name)}",
                            label_visibility="visible"
                        ):
                            st.session_state[selected_fields_key].append(loc_name)
                            if loc_name not in st.session_state[configs_key]:
                                st.session_state[configs_key][loc_name] = FILL_FORM_DEFAULTS.copy()
                            st.rerun()
            else:
                st.info(f"❌ No fields found matching '{search_query}'")
            
            st.markdown("---")
            col_left, col_center, col_right = st.columns([1, 2, 1])
            with col_center:
                if st.button("✅ Done Adding", key=f"{dialog_key}_done_add", use_container_width=True, type="primary"):
                    st.session_state[f"{dialog_key}_show_add_field"] = False
                    # Cleanup search state
                    if search_key in st.session_state:
                        del st.session_state[search_key]
                    if clear_flag_key in st.session_state:
                        del st.session_state[clear_flag_key]
                    st.rerun()
        else:
            st.info("All fields already selected.")
            if st.button("Close", key=f"{dialog_key}_close_add", use_container_width=True):
                st.session_state[f"{dialog_key}_show_add_field"] = False
                st.rerun()
    
    st.markdown("---")
    
    # ====== SECTION 2: CONFIGURATION (COMPACT TABLE) ======
    if not selected_fields:
        st.info("👆 Select fields to configure them")
    else:
        # Quick Config Header + Ant Design Checkbox
        cfg_header_col1, cfg_header_col2 = st.columns([3, 0.65])
        with cfg_header_col1:
            st.markdown("**⚙️ Quick Configuration:**")
        with cfg_header_col2:
            new_ant_val = st.checkbox(
                "🎨 Ant Design (All)",
                value=st.session_state[ant_design_key],
                key=f"{dialog_key}_ant_checkbox_main",
                help="Apply Ant Design to all fields"
            )
            if new_ant_val != st.session_state[ant_design_key]:
                st.session_state[ant_design_key] = new_ant_val
                st.rerun()
        
        # Compact Table Header with is_select column
        # Columns: Field(2), is_sel(0.5), Sel Attr(0.8), Checkbox(0.5), Switch(0.5), SwitchVal(1), Del(0.4)
        # header_cols = st.columns([2, 0.5, 0.8, 0.5, 0.5, 1, 0.4])
        # with header_cols[0]: st.caption("**Field**")
        # with header_cols[1]: st.caption("**select?**")
        # with header_cols[2]: st.caption("**Sel Attr**")
        # with header_cols[3]: st.caption("**☑️ Checkbox?**")
        # with header_cols[4]: st.caption("**🔘 switch?**")
        # with header_cols[5]: st.caption("**Locator Switch Checked**")
        # with header_cols[6]: st.caption("**Del**")

        st.markdown("""
            <style>
            .header-row {
                background: linear-gradient(135deg, #1e3a5f 0%, #2c5282 100%);
                padding: 8px;
                border-radius: 8px;
                margin-bottom: 10px;
            }
            .header-cell {
                color: #e0e7ff;
                font-weight: bold;
                font-size: 0.85em;
                text-align: left;
            }
            </style>
        """, unsafe_allow_html=True)

        # Create styled header
        header_html = """
        <div class="header-row" style="display: flex; gap: 5px; align-items: left;">
            <div class="header-cell" style="flex: 2;">Field</div>
            <div class="header-cell" style="flex: 0.5;">select?</div>
            <div class="header-cell" style="flex: 0.8;">Sel Attr</div>
            <div class="header-cell" style="flex: 0.5;">☑️ checkbox?</div>
            <div class="header-cell" style="flex: 0.5;">🔘 switch?</div>
            <div class="header-cell" style="flex: 1;">Locator Switch Checked</div>
            <div class="header-cell" style="flex: 0.4;">Del</div>
        </div>
        """
        st.markdown(header_html, unsafe_allow_html=True)

        # Use HTML hr for minimal spacing
        st.markdown('<hr style="margin: 5px 0; border-color: #444;">', unsafe_allow_html=True)
        
        visible_fields = selected_fields[:10]
        hidden_fields = selected_fields[10:]
        
        # Render visible fields
        for field_idx, field_name in enumerate(visible_fields):
            if field_name not in st.session_state[configs_key]:
                st.session_state[configs_key][field_name] = FILL_FORM_DEFAULTS.copy()
            
            config = st.session_state[configs_key][field_name]
            render_config_row(field_idx, field_name, config, dialog_key, selected_fields_key, configs_key)
        
        # Render hidden fields
        if hidden_fields:
            with st.expander(f"📋 Show {len(hidden_fields)} more fields", expanded=False):
                for field_idx, field_name in enumerate(hidden_fields, start=10):
                    if field_name not in st.session_state[configs_key]:
                        st.session_state[configs_key][field_name] = FILL_FORM_DEFAULTS.copy()
                    config = st.session_state[configs_key][field_name]
                    render_config_row(field_idx, field_name, config, dialog_key, selected_fields_key, configs_key)
    
    st.markdown("---")
    
    # ====== LIVE CODE PREVIEW ======
    if selected_fields:
        st.markdown("### 🔍 Live Code Preview")
        preview_code = generate_fill_form_preview(
            selected_fields, 
            st.session_state[configs_key], 
            st.session_state[ant_design_key]
        )
        st.code(preview_code, language='robotframework', line_numbers=True)
    
    st.markdown("---")
    
    # ====== FOOTER ======
    num_selected = len(selected_fields)
    ant_status = "✓" if st.session_state[ant_design_key] else "✗"
    st.caption(f"📦 {num_selected} fields • Ant: {ant_status}")
    
    col_gen, col_cancel = st.columns(2)
    with col_gen:
        if st.button("✅ Generate Steps", disabled=num_selected == 0, type="primary", use_container_width=True, key=f"{dialog_key}_generate"):
            generate_fill_steps(keyword_id, st.session_state[selected_fields_key], st.session_state[configs_key], st.session_state[ant_design_key])
            cleanup_dialog_state(dialog_key)
            st.session_state.show_kw_factory_fill_form_dialog = False
            st.toast(f"✅ Generated {num_selected} steps!", icon="✨")
            st.rerun()
    with col_cancel:
        if st.button("❌ Cancel", use_container_width=True, key=f"{dialog_key}_cancel"):
            cleanup_dialog_state(dialog_key)
            st.session_state.show_kw_factory_fill_form_dialog = False
            st.rerun()


# ============================================================
# 🎯 SECTION 3: LIVE CODE PREVIEW GENERATOR
# ============================================================

def generate_fill_form_preview(selected_fields: List[str], configs: Dict, ant_design_all: bool) -> str:
    """สร้าง Live Code Preview โดยใช้ logic เดียวกับ actual generation"""
    from .utils import generate_arg_name_from_locator, format_robot_step_line
    
    if not selected_fields:
        return "# No fields selected yet"
    
    code_lines = []
    
    for field_name in selected_fields:
        config = configs.get(field_name, {})
        
        # สร้าง variable name
        arg_var = generate_arg_name_from_locator(field_name)
        if not arg_var:
            clean_loc = field_name.replace('LOCATOR_', '').lower()
            arg_var = f"${{{clean_loc or 'value'}}}"
        
        # สร้าง step args เหมือนกับ generate_fill_steps
        select_attr = config.get('sel_attr', 'label') if config.get('is_select', False) else None
        
        step_args = {
            "locator_field": field_name,
            "value": arg_var,
            "is_switchtype": config.get('is_switchtype', False),
            "is_checkboxtype": config.get('is_checkboxtype', False),
            "sel_attr": select_attr,
            "is_antdesign": ant_design_all,
        }
        
        # เพิ่ม locator_switch_checked เฉพาะเมื่อเป็น switch
        if config.get('is_switchtype', False):
            step_args["locator_switch_checked"] = config.get('locator_switch_checked', '${EMPTY}')
        
        # สร้าง step object
        step = {
            "keyword": "Fill in data form",
            "args": step_args
        }
        
        # ใช้ format_robot_step_line เหมือนกับตอน generate จริง
        code = format_robot_step_line(step)
        code_lines.append(code)
    
    return "\n".join(code_lines)


# ============================================================
# 🎯 SECTION 4: HELPER FUNCTIONS
# ============================================================

def render_config_row(field_idx, field_name, config, dialog_key, selected_fields_key, configs_key):
    """Render a single configuration row with is_select checkbox and conditional Switch Val"""
    # Columns: Field(2), is_sel(0.5), Sel Attr(0.8), Checkbox(0.5), Switch(0.5), SwitchVal(1), Del(0.4)
    row_cols = st.columns([2, 0.5, 0.8, 0.5, 0.5, 1, 0.4])
    
    # 1. Field Name
    with row_cols[0]:
        clean_name = get_clean_locator_name(field_name)
        st.markdown(f'<div style="padding-top: 5px; font-size: 0.9em;"><b>{clean_name}</b></div>', unsafe_allow_html=True)
    
    # 2. is_select checkbox (NEW)
    with row_cols[1]:
        is_select = st.checkbox(
            "sel",
            value=config.get('is_select', False),
            key=f"{dialog_key}_is_sel_{field_idx}",
            label_visibility="collapsed",
            help="Enable select dropdown"
        )
        config['is_select'] = is_select
    
    # 3. Select Attribute (enabled only if is_select is checked)
    with row_cols[2]:
        if is_select:
            attr = st.selectbox(
                "attr",
                options=['label', 'value'],
                index=['label', 'value'].index(config.get('sel_attr', 'label')),
                key=f"{dialog_key}_attr_{field_idx}",
                label_visibility="collapsed"
            )
            config['sel_attr'] = attr
        else:
            # Show disabled dropdown
            st.selectbox(
                "attr",
                options=['label'],
                index=0,
                key=f"{dialog_key}_attr_dis_{field_idx}",
                label_visibility="collapsed",
                disabled=True
            )
            config['sel_attr'] = 'label'
    
    # 4. Checkbox (is_checkbox)
    with row_cols[3]:
        is_checkbox = st.checkbox(
            "cb",
            value=config.get('is_checkboxtype', False),
            key=f"{dialog_key}_cb_{field_idx}",
            label_visibility="collapsed"
        )
        config['is_checkboxtype'] = is_checkbox
    
    # 5. Switch (is_switch_type)
    with row_cols[4]:
        is_switch = st.checkbox(
            "sw",
            value=config.get('is_switchtype', False),
            key=f"{dialog_key}_sw_{field_idx}",
            label_visibility="collapsed"
        )
        config['is_switchtype'] = is_switch
    
    # 6. Switch Value (enabled only if is_switch is checked)
    with row_cols[5]:
        if is_switch:
            switch_val = st.text_input(
                "val",
                value=config.get('locator_switch_checked', '${EMPTY}'),
                key=f"{dialog_key}_val_{field_idx}",
                placeholder="${EMPTY}",
                label_visibility="collapsed"
            )
            config['locator_switch_checked'] = switch_val
        else:
            # Show disabled input
            st.text_input(
                "val",
                value='${EMPTY}',
                key=f"{dialog_key}_val_dis_{field_idx}",
                placeholder="${EMPTY}",
                label_visibility="collapsed",
                disabled=True
            )
            config['locator_switch_checked'] = '${EMPTY}'
    
    # 7. Delete
    with row_cols[6]:
        if st.button("🗑️", key=f"{dialog_key}_del_{field_idx}", help="Remove"):
            st.session_state[selected_fields_key].remove(field_name)
            if field_name in st.session_state[configs_key]:
                del st.session_state[configs_key][field_name]
            st.rerun()
            
    # Minimal separator
    st.markdown('<hr style="margin: 2px 0; border-color: #333;">', unsafe_allow_html=True)


def generate_fill_steps(keyword_id: str, selected_fields: List[str], configs: Dict, ant_design_all: bool):
    """Generate Fill in data form steps with configurations."""
    from modules import kw_manager
    
    locators_with_custom_args = {}
    
    for field_name in selected_fields:
        config = configs.get(field_name, {})
        
        # Only include sel_attr if is_select is True
        select_attr = config.get('sel_attr', 'label') if config.get('is_select', False) else None
        
        locators_with_custom_args[field_name] = {
            'is_switchtype': config.get('is_switchtype', False),
            'is_checkboxtype': config.get('is_checkboxtype', False),
            'sel_attr': select_attr,
            'is_antdesign': ant_design_all,
            'locator_switch_checked': config.get('locator_switch_checked', '${EMPTY}') if config.get('is_switchtype', False) else None
        }
    
    kw_manager.add_quick_fill_form_steps_with_custom_args(keyword_id, locators_with_custom_args)


def cleanup_dialog_state(dialog_key: str):
    """Clean up all dialog-related session state."""
    keys_to_remove = [
        f"{dialog_key}_selected_page",
        f"{dialog_key}_selected_fields",
        f"{dialog_key}_ant_design",
        f"{dialog_key}_configs",
        f"{dialog_key}_show_add_field"
    ]
    
    for key in keys_to_remove:
        if key in st.session_state:
            del st.session_state[key]