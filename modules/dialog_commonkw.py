# modules/dialog_commonkw.py
"""
Common Dialog Module for Adding Steps - Improved UI Design
FIXED VERSION: ลบ Magic Trick ออกหมด, ใช้ Stable Key + Simple Logic
"""
import streamlit as st
import uuid
import streamlit.components.v1 as components
from .ui_common import ARGUMENT_PRESETS, ARGUMENT_PATTERNS

# *** ลบ import ทั้งหมดที่ทำให้เกิด circular dependency ออก ***
# *** จะ import ภายในฟังก์ชันแทน ***

# --- Enhanced CSS for Better Visual Design ---
def inject_add_dialog_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
        
        .stApp { 
            font-family: 'Inter', sans-serif; 
        }
        
        /* Dialog container adjustments */
        div[data-testid="stDialog"] > div > div[data-testid="stVerticalBlock"] > div:first-child {
            padding-top: 0.5rem !important;
        }
        
        /* Dialog background - Semi-transparent to show background */
        div[data-testid="stDialog"] > div {
            background-color: rgba(28, 33, 40, 0.75) !important;
            backdrop-filter: blur(10px);
        }
        
        /* Back button styling */
        .back-button-container {
            margin-bottom: 1rem;
        }
        
        /* Column layout improvements with clear borders and depth */
        .keyword-column {
            background: linear-gradient(145deg, #2d333b, #22272e);
            border: 1px solid #444c56;
            border-left: 3px solid #539bf5;
            border-radius: 8px;
            padding: 1.5rem;
            height: 70vh;
            overflow-y: auto;
            box-shadow: 
                0 0 0 1px rgba(110, 118, 129, 0.4),
                0 8px 24px rgba(0, 0, 0, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.05);
            position: relative;
        }
        
        .keyword-column::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(83, 155, 245, 0.3), transparent);
        }
        
        .config-column {
            background: linear-gradient(145deg, #2d333b, #22272e);
            border: 1px solid #444c56;
            border-left: 3px solid #768390;
            border-radius: 8px;
            padding: 1.5rem 2rem;
            height: 70vh;
            overflow-y: auto;
            box-shadow: 
                0 0 0 1px rgba(110, 118, 129, 0.4),
                0 8px 24px rgba(0, 0, 0, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.05);
            position: relative;
        }
        
        .config-column::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, rgba(118, 131, 144, 0.3), transparent);
        }
        
        /* Search box enhancement - Lighter background */
        div[data-testid="stDialog"] .stTextInput > div > div > input {
            background-color: #2d333b !important;
            border: 1px solid #444c56 !important;
            border-radius: 6px !important;
            padding: 0.65rem 1rem !important;
            font-size: 0.95rem !important;
            color: #adbac7 !important;
            transition: all 0.2s ease-in-out !important;
        }
        
        div[data-testid="stDialog"] .stTextInput > div > div > input:focus {
            border-color: #539bf5 !important;
            box-shadow: 0 0 0 3px rgba(83, 155, 245, 0.15) !important;
            background-color: #22272e !important;
        }
        
        div[data-testid="stDialog"] .stTextInput > div > div > input::placeholder {
            color: #768390 !important;
        }
        
        /* Expander improvements - Better contrast */
        div[data-testid="stDialog"] [data-testid="stExpander"] {
            background-color: transparent !important;
            border: none !important;
            margin-bottom: 8px !important;
        }
        
        div[data-testid="stDialog"] [data-testid="stExpander"] > div:first-child {
            background-color: #2d333b !important;
            border: 1px solid #444c56 !important;
            border-radius: 6px !important;
            padding: 0.7rem 1rem !important;
            transition: all 0.2s ease-in-out;
            color: #adbac7 !important;
        }
        
        div[data-testid="stDialog"] [data-testid="stExpander"] > div:first-child:hover {
            background-color: #373e47 !important;
            border-color: #539bf5 !important;
        }
        
        div[data-testid="stDialog"] [data-testid="stExpander"][open] > div:first-child {
            background-color: #373e47 !important;
            border-color: #539bf5 !important;
            box-shadow: 0 0 0 1px #539bf5;
        }
        
        /* Keyword button enhancements - Better visibility */
        div[data-testid="stDialog"] div[data-testid="stButton"] { 
            margin: 4px 0; 
        }
        
        div[data-testid="stDialog"] div[data-testid="stButton"] > button[kind="secondary"] {
            display: flex;
            align-items: center;
            justify-content: flex-start;
            width: 100%;
            padding: 0.7rem 1rem;
            border-radius: 6px;
            border: 1px solid #444c56;
            background-color: #2d333b;
            color: #adbac7;
            font-weight: 500;
            font-size: 0.92rem;
            text-align: left;
            transition: all 0.2s ease-in-out;
        }
        
        div[data-testid="stDialog"] div[data-testid="stButton"] > button[kind="secondary"]:hover {
            border-color: #539bf5;
            background-color: #373e47;
            color: #cdd9e5;
            transform: translateX(4px);
        }
        
        div[data-testid="stDialog"] div[data-testid="stButton"] > button:focus:not(:active) {
            border-color: #539bf5 !important;
            box-shadow: 0 0 0 3px rgba(83, 155, 245, 0.15) !important;
        }
        
        div[data-testid="stDialog"] .stButton button.active-keyword {
            background-color: #316dca;
            border-color: #539bf5;
            color: #ffffff;
            font-weight: 600;
            box-shadow: 0 0 0 1px #539bf5, 0 4px 16px rgba(83, 155, 245, 0.3);
            transform: translateX(4px);
        }
        
        /* Section headers - Better contrast */
        .section-header {
            display: flex;
            align-items: center;
            gap: 0.5rem;
            font-size: 1rem;
            font-weight: 600;
            color: #adbac7;
            margin-bottom: 1rem;
            padding-bottom: 0.75rem;
            border-bottom: 2px solid #373e47;
        }
        
        .section-header-icon {
            font-size: 1.25rem;
        }
        
        /* Keyword info box - Enhanced visibility */
        .keyword-info {
            background-color: #2d333b;
            border: 1px solid #444c56;
            border-radius: 6px;
            padding: 1.25rem;
            margin-bottom: 1.5rem;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }
        
        .keyword-info-title {
            font-size: 1.1rem;
            font-weight: 700;
            color: #539bf5;
            margin-bottom: 0.75rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .keyword-info-title::before {
            content: "⚙️";
            font-size: 1.25rem;
        }
        
        .keyword-info-doc {
            color: #768390;
            line-height: 1.6;
            font-size: 0.9rem;
        }
        
        /* Empty state styling - GitHub Dark style */
        .empty-state {
            text-align: center;
            padding: 3rem 1.5rem;
            color: #8b949e;
        }
        
        .empty-state-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
            opacity: 0.4;
        }
        
        .empty-state-text {
            font-size: 1rem;
            font-weight: 500;
            color: #8b949e;
        }
        
        /* Primary button enhancement - GitHub style */
        div[data-testid="stDialog"] button[type="primary"] {
            background-color: #238636 !important;
            border: 1px solid rgba(240, 246, 252, 0.1) !important;
            padding: 0.85rem 1.5rem !important;
            font-weight: 600 !important;
            font-size: 1rem !important;
            border-radius: 6px !important;
            color: #ffffff !important;
            box-shadow: 0 0 transparent, 0 0 transparent, 0 1px 0 rgba(27, 31, 36, 0.04) !important;
            transition: all 0.2s ease-in-out !important;
        }
        
        div[data-testid="stDialog"] button[type="primary"]:hover {
            background-color: #2ea043 !important;
            border-color: rgba(240, 246, 252, 0.1) !important;
            box-shadow: 0 0 transparent, 0 0 transparent, 0 1px 0 rgba(27, 31, 36, 0.04), inset 0 1px 0 rgba(255, 255, 255, 0.03) !important;
        }
        
        /* Scrollbar styling - Better visibility */
        .keyword-column::-webkit-scrollbar,
        .config-column::-webkit-scrollbar {
            width: 10px;
        }
        
        .keyword-column::-webkit-scrollbar-track,
        .config-column::-webkit-scrollbar-track {
            background: #1c2128;
            border-radius: 5px;
        }
        
        .keyword-column::-webkit-scrollbar-thumb,
        .config-column::-webkit-scrollbar-thumb {
            background-color: #444c56;
            border: 2px solid #22272e;
            border-radius: 6px;
        }
        
        .keyword-column::-webkit-scrollbar-thumb:hover,
        .config-column::-webkit-scrollbar-thumb:hover {
            background-color: #545d68;
        }
        
        /* Category badge - Better contrast */
        .category-badge {
            display: inline-block;
            background-color: #373e47;
            color: #768390;
            border: 1px solid #444c56;
            padding: 0.2rem 0.6rem;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 600;
            margin-left: 0.5rem;
        }
        
        /* Reduce spacing */
        div[data-testid="stDialog"] [data-testid="stVerticalBlock"] { 
            gap: 0.25rem; 
        }
        
        div[data-testid="stDialog"] h3 { 
            margin-bottom: 0.5rem; 
        }
        
        div[data-testid="stDialog"] h5 { 
            margin-top: 0.5rem; 
            margin-bottom: 0.3rem; 
        }
        
        div[data-testid="stDialog"] .stDivider { 
            margin: 0.5rem 0; 
        }
    </style>
    """, unsafe_allow_html=True)


# --- Helper Function for Rendering Keyword Row ---
def _render_keyword_row(kw, key_prefix, selected_kw_state_key, recently_used_list, add_step_callback, context, ws_state, dialog_state_key, keyword_filter_func=None):
    if keyword_filter_func and not keyword_filter_func(kw): 
        return
    
    has_args = bool(kw.get('args'))
    icon = "⚡" if not has_args else "⚙️"
    selected_kw_obj = st.session_state.get(selected_kw_state_key)
    is_active = selected_kw_obj and selected_kw_obj['name'] == kw['name']
    button_label = f"{icon}  {kw['name']}"
    button_key = f"{key_prefix}_kw_btn_{kw['name'].replace(' ', '_').replace('/', '_')}"

    if st.button(button_label, key=button_key, use_container_width=True, type="secondary"):
        if kw['name'] in recently_used_list: 
            recently_used_list.remove(kw['name'])
        recently_used_list.insert(0, kw['name'])
        
        if not has_args:  # Quick Add
            new_step = {"id": str(uuid.uuid4()), "keyword": kw['name'], "args": {}}
            add_step_callback(context, new_step)
            st.session_state[dialog_state_key] = False
            if selected_kw_state_key in st.session_state: 
                del st.session_state[selected_kw_state_key]
            st.toast(f"✅ Step '{kw['name']}' added!", icon="🎉")
            st.rerun()
        else:  # Select for configuration
            st.session_state[selected_kw_state_key] = kw
            st.session_state[f'{dialog_state_key}_scroll_to_top'] = True
            st.rerun()

    if is_active:
        button_test_id = f"stButton-secondary-{button_key}"
        st.markdown(f'<style>.stButton button[data-testid="{button_test_id}"] {{ background-color: #316dca; border-color: #539bf5; color: #ffffff; font-weight: 600; box-shadow: 0 0 0 1px #539bf5; }}</style>', unsafe_allow_html=True)


# --- Main Dialog Function ---
@st.dialog("Add New Step", width="large")
def render_add_step_dialog_base(
    dialog_state_key: str,
    context_state_key: str,
    selected_kw_state_key: str,
    add_step_callback: callable,
    ws_state: dict,
    title: str = "Add New Step",
    keyword_filter_func: callable = None,
    search_state_key: str = "kw_search_dialog_base",
    recently_used_state_key: str = "recently_used_keywords_base",
):
    """Renders the improved dialog for adding steps - FIXED VERSION (No Magic Tricks)"""
    # Import functions here to avoid circular import
    from .test_flow_manager import categorize_keywords
    from .ui_common import (
        render_argument_input,
        render_verify_table_arguments_for_dialog
    )
    
    inject_add_dialog_css()

    # --- Get Context and State ---
    context = st.session_state.get(context_state_key, {})
    section_name = "Unknown Section"
    if isinstance(context, dict):
        section_name = context.get('key', "Unknown CRUD Section").upper().replace('_', ' ')
    elif isinstance(context, str):
        section_name = context.upper().replace('_', ' ')

    all_keywords_list = ws_state.get('keywords', [])
    if all_keywords_list and 'categorized_keywords' not in ws_state:
        ws_state['categorized_keywords'] = categorize_keywords(all_keywords_list)
    categorized_keywords = ws_state.get('categorized_keywords', {})
    keyword_map = {kw['name']: kw for kw in all_keywords_list}
    
    if selected_kw_state_key not in st.session_state: 
        st.session_state[selected_kw_state_key] = None
    if recently_used_state_key not in st.session_state: 
        st.session_state[recently_used_state_key] = []
    recently_used_list = st.session_state[recently_used_state_key]
    selected_kw = st.session_state.get(selected_kw_state_key)

    # --- Cleanup Function ---
    def close_dialog_and_cleanup():
        st.session_state[dialog_state_key] = False
        if selected_kw_state_key in st.session_state: 
            del st.session_state[selected_kw_state_key]

        form_input_keys_to_clean = []
        if selected_kw and selected_kw.get('args'):
            for i, arg_item in enumerate(selected_kw.get('args', [])):
                clean_arg_name = arg_item.get('name', '').strip('${}')
                if clean_arg_name:
                    kw_name_safe = selected_kw['name'].replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '')
                    unique_key = f"{dialog_state_key}_{kw_name_safe}_{clean_arg_name}_{i}"
                    form_input_keys_to_clean.append(unique_key)
        for key in form_input_keys_to_clean:
            if key in st.session_state: 
                del st.session_state[key]

        verify_ui_context_id = ""
        if isinstance(context, dict): 
            verify_ui_context_id = f"add_dialog_crud_{context.get('key', 'unknown')}_verify_table"
        else: 
            verify_ui_context_id = f"add_dialog_tf_{context}_verify_table"
        verify_state_key = f"verify_table_assertions_{verify_ui_context_id}"
        if verify_state_key in st.session_state: 
            del st.session_state[verify_state_key]

        # ✅ ลบค่า CSV Quick Insert
        csv_keys = [
            f"quick_csv_ds_{dialog_state_key}",
            f"quick_csv_row_{dialog_state_key}",
            f"quick_csv_col_{dialog_state_key}",
            f"quick_csv_target_{dialog_state_key}",
        ]
        for key in csv_keys:
            if key in st.session_state:
                del st.session_state[key]

        st.rerun()

    # --- Back Button ---
    with st.container():
        if st.button("← Back to Workspace", key=f"back_{dialog_state_key}"):
            close_dialog_and_cleanup()
    
    st.markdown("<div style='margin-bottom: 1rem;'></div>", unsafe_allow_html=True)

    # --- Two Column Layout with better proportions ---
    left_col, right_col = st.columns([0.45, 0.55], gap="medium")

    # --- Left Column: Keyword Selection ---
    with left_col:
        st.markdown('<div class="section-header"><span class="section-header-icon">🔍</span>Select Keyword</div>', unsafe_allow_html=True)
        
        search_query = st.text_input(
            "Search", 
            key=search_state_key, 
            placeholder="🔎 Type to filter keywords...", 
            label_visibility="collapsed"
        ).lower()

        st.markdown("<div style='margin-top: 1rem;'></div>", unsafe_allow_html=True)

        # Display All Keywords by Category
        if not categorized_keywords:
            st.warning("⚠️ No keywords loaded.")
        else:
            filtered_count_total = 0
            try:
                from .keyword_categorizer import get_category_priority
                sorted_items = sorted(categorized_keywords.items(), key=lambda item: get_category_priority(item[0]))
            except ImportError:
                sorted_items = categorized_keywords.items()

            for category, keywords in sorted_items:
                filtered_kws = [
                    kw for kw in keywords
                    if (not keyword_filter_func or keyword_filter_func(kw)) and search_query in kw['name'].lower()
                ]
                
                if filtered_kws:
                    filtered_count_total += len(filtered_kws)
                    expand_this = bool(search_query) or filtered_count_total <= 8

                    with st.expander(f"{category} · {len(filtered_kws)} keywords", expanded=expand_this):
                        for kw in filtered_kws:
                            _render_keyword_row(
                                kw, "all", selected_kw_state_key, recently_used_list,
                                add_step_callback, context, ws_state, dialog_state_key, None
                            )

            if search_query and filtered_count_total == 0:
                st.markdown('<div class="empty-state"><div class="empty-state-icon">🔍</div><div class="empty-state-text">No keywords match your search</div></div>', unsafe_allow_html=True)

    # --- Right Column: Argument Configuration ---
    with right_col:
        # Scrolling fix
        scroll_state_key = f'{dialog_state_key}_scroll_to_top'
        if st.session_state.get(scroll_state_key):
            components.html("""<script>window.parent.scrollTo({ top: 0, behavior: 'smooth' });</script>""", height=0)
            st.session_state[scroll_state_key] = False

        selected_kw = st.session_state.get(selected_kw_state_key)

        if selected_kw:
            st.markdown('<div class="section-header"><span class="section-header-icon">⚙️</span>Configure Arguments</div>', unsafe_allow_html=True)
            
            doc_text = selected_kw.get('doc', 'No documentation available.')
            st.markdown(f"""
                <div class='keyword-info'>
                    <div class='keyword-info-title'>{selected_kw['name']}</div>
                    <div class='keyword-info-doc'>{doc_text}</div>
                </div>
            """, unsafe_allow_html=True)

            # --- Special Handling for Verify Result ---
            if selected_kw['name'].strip() == 'Verify Result of data table':
                context_for_verify = context.copy()
                context_for_verify['add_callback'] = add_step_callback
                context_for_verify['dialog_state_key'] = dialog_state_key
                render_verify_table_arguments_for_dialog(ws_state, context_for_verify, section_name, selected_kw)

            # --- Standard Form for Other Keywords ---
            else:
                # === CSV Quick Insert (ไม่ใช้ st.form) ===
                with st.expander("📊 Quick Insert from CSV Data", expanded=False):
                    st.caption("Select value and target argument to insert")
                    
                    # Import extract function locally
                    from .crud_generator.ui_crud import extract_csv_datasource_keywords
                    csv_keywords = extract_csv_datasource_keywords(ws_state)
                    
                    if csv_keywords and selected_kw and selected_kw.get('args'):
                        col_ds, col_row, col_column, col_target = st.columns([2, 1.5, 1.5, 2])
                        
                        with col_ds:
                            quick_ds = st.selectbox(
                                "Data Source",
                                options=list(csv_keywords.keys()),
                                key=f"quick_csv_ds_{dialog_state_key}"
                            )
                        
                        quick_row_val = ""
                        with col_row:
                            quick_row_val = st.text_input(
                                "Row Key",
                                key=f"quick_csv_row_{dialog_state_key}",
                                placeholder="e.g., robotapi"
                            )
                        
                        quick_col = None
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
                                            key=f"quick_csv_col_{dialog_state_key}"
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
                                    key=f"quick_csv_target_{dialog_state_key}"
                                )
                            else:
                                st.caption("_No text args_")
                        
                        # ✅ แสดงปุ่ม Insert เสมอ (ไม่มี preview)
                        if quick_ds and target_arg:
                            ds_info = csv_keywords.get(quick_ds, {})
                            ds_var = ds_info.get('ds_var', 'DATA')
                            col_var = ds_info.get('col_var', 'COL')
                            
                            # สร้าง syntax สำหรับ insert
                            insert_syntax = ""
                            if quick_row_val:
                                if len(headers) > 1 and quick_col:
                                    insert_syntax = f"${{{ds_var}['{quick_row_val}'][${{{col_var}.{quick_col}}}]}}"
                                else:
                                    insert_syntax = f"${{{ds_var}['{quick_row_val}']}}"
                            
                            # ✅ ปุ่ม Insert (แสดงเสมอ)
                            if st.button("✅ Insert", type="primary", use_container_width=True, 
                                        key=f"quick_csv_insert_btn_{dialog_state_key}"):
                                if not target_arg:
                                    st.warning("Please select a target argument 'Insert to →'")
                                elif not quick_row_val:
                                    st.warning("Please enter a 'Row Key'")
                                elif insert_syntax:
                                    # ✅ Insert ค่าลง session_state
                                    kw_name_clean = selected_kw['name'].replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '')
                                    for i, arg_item in enumerate(selected_kw.get('args', [])):
                                        arg_name = arg_item.get('name', '').strip('${}')
                                        if arg_name == target_arg:
                                            unique_key = f"{dialog_state_key}_{kw_name_clean}_{arg_name}_{i}"
                                            st.session_state[unique_key] = insert_syntax
                                            st.toast(f"✅ Inserted '{insert_syntax}' into '{target_arg}'", icon="✅")
                                            st.rerun()
                                            break
                    else:
                        st.info("No CSV data sources found or this keyword has no arguments.")
                
                st.markdown("---")
                
                # === Main Form - ใช้ Stable Key เท่านั้น ===
                kw_name_safe = selected_kw['name'].replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '')
                form_key = f"step_form_{dialog_state_key}_{kw_name_safe}"
                
                with st.form(key=form_key):
                    # 🔴 START: บล็อกโค้ดสำหรับ "วาด" (Render) ที่หายไป 🔴
                    args_data = {}
                    form_input_keys = [] # เก็บ Key สำหรับ Cleanup
                    
                    if selected_kw.get('args'):
                        for i, arg_item in enumerate(selected_kw.get('args', [])):
                            arg_info = arg_item.copy() if isinstance(arg_item, dict) else {'name': str(arg_item), 'default': ''}
                            raw_arg_name = arg_info.get('name')
                            if not raw_arg_name: 
                                continue
                            
                            clean_arg_name = raw_arg_name.strip('${}')
                            arg_info['name'] = clean_arg_name
                            
                            unique_key = f"{dialog_state_key}_{kw_name_safe}_{clean_arg_name}_{i}"
                            form_input_keys.append(unique_key) # เก็บ Base Key
                            
                            # ดึงค่าปัจจุบันจาก session_state (ที่อาจถูก set โดย CSV Quick Insert)
                            current_value_in_state = st.session_state.get(unique_key)
                            
                            if current_value_in_state is not None:
                                arg_info['default'] = current_value_in_state
                            
                            # วาด Input (ฟังก์ชันนี้จะเติม Suffix _default_text, _locator_select ฯลฯ ให้เอง)
                            rendered_value = render_argument_input(
                                arg_info, 
                                ws_state, 
                                unique_key,
                                current_value=current_value_in_state
                            )
                            # (เราไม่จำเป็นต้องใช้ rendered_value ที่นี่ เพราะ st.form จะจัดการ state เอง)
                    
                    st.markdown("---")
                    
                    # 🔴 ปุ่ม Submit ที่หายไป 🔴
                    submitted_add = st.form_submit_button(
                        f"✅ Add Step to Workspace", 
                        type="primary", 
                        use_container_width=True
                    )
                    # 🔴 END: สิ้นสุดบล็อกโค้ดที่หายไป 🔴

                    # ▼▼▼ บล็อกโค้ดสำหรับ "ประมวลผล" (Logic) ที่คุณมีอยู่แล้ว (แต่ต้องอยู่ข้างใน if) ▼▼▼
                    if submitted_add:
                        final_args_data = {} # ✅ สร้างตัวแปร (แก้ NameError)
                        
                        if selected_kw.get('args'):
                            for i, arg_item in enumerate(selected_kw.get('args', [])):
                                arg_info = arg_item.copy() if isinstance(arg_item, dict) else {'name': str(arg_item), 'default': ''}
                                raw_arg_name = arg_info.get('name')
                                if not raw_arg_name: 
                                    continue
                                
                                clean_arg_name = raw_arg_name.strip('${}')
                                arg_info['name'] = clean_arg_name
                                
                                unique_key = f"{dialog_state_key}_{kw_name_safe}_{clean_arg_name}_{i}"
                                
                                # --- START: NEW SMART KEY LOGIC ---
                                final_value = None
                                
                                # Re-run the logic from ui_common.render_argument_input
                                is_locator_arg = any(s in clean_arg_name.lower() for s in ['locator', 'field', 'button', 'element', 'menu', 'header', 'body', 'theader', 'tbody'])
                                
                                # 1. 🐞 FIX: ตรวจสอบ PRESETS ก่อน
                                if clean_arg_name in ARGUMENT_PRESETS:
                                    config = ARGUMENT_PRESETS[clean_arg_name]
                                    input_type = config.get('type')
                                    if input_type == "select_or_input":
                                        selected = st.session_state.get(f"{unique_key}_select")
                                        if selected == "📝 Other (custom)":
                                            final_value = st.session_state.get(f"{unique_key}_custom")
                                        else:
                                            final_value = selected
                                    else:
                                        # 'boolean' or 'select'
                                        final_value = st.session_state.get(unique_key)
                                
                                # 2. 🐞 FIX: ค่อยตรวจสอบ LOCATOR ทีหลัง
                                elif is_locator_arg:
                                    final_value = st.session_state.get(f"{unique_key}_locator_select")

                                # 3. ตรวจสอบ PATTERNS
                                else:
                                    matched_pattern = False
                                    arg_lower = clean_arg_name.lower()
                                    for pattern_key in ARGUMENT_PATTERNS.keys():
                                        if pattern_key in arg_lower:
                                            final_value = st.session_state.get(unique_key)
                                            matched_pattern = True
                                            break
                                    
                                    # 4. Default Text Input
                                    if not matched_pattern:
                                        final_value = st.session_state.get(f"{unique_key}_default_text")
                                
                                # Fallback to the original logic if new value is None
                                if final_value is None:
                                    final_value = st.session_state.get(unique_key, '') # Fallback
                                    
                                final_args_data[clean_arg_name] = final_value
                                # --- END: NEW SMART KEY LOGIC ---

                        # ✅ แก้ไข IndentationError
                        new_step = {
                            "id": str(uuid.uuid4()), 
                            "keyword": selected_kw['name'], 
                            "args": final_args_data
                        }
                        
                        add_step_callback(context, new_step)
                        
                        # Cleanup
                        st.session_state[dialog_state_key] = False
                        if selected_kw_state_key in st.session_state: 
                            del st.session_state[selected_kw_state_key]
                        
                        # --- 🐞 FIX: แก้ไข Logic การลบ Key ---
                        # (ต้องลบ Key ที่มี Suffix ด้วย)
                        form_input_keys_to_clean_on_submit = []
                        if selected_kw.get('args'):
                            for i, arg_item in enumerate(selected_kw.get('args', [])):
                                clean_arg_name = arg_item.get('name', '').strip('${}')
                                if not clean_arg_name: continue
                                
                                unique_key = f"{dialog_state_key}_{kw_name_safe}_{clean_arg_name}_{i}"
                                
                                # เพิ่ม Key ที่มี Suffix ที่เป็นไปได้ทั้งหมด
                                form_input_keys_to_clean_on_submit.append(unique_key)
                                form_input_keys_to_clean_on_submit.append(f"{unique_key}_locator_select")
                                form_input_keys_to_clean_on_submit.append(f"{unique_key}_select")
                                form_input_keys_to_clean_on_submit.append(f"{unique_key}_custom")
                                form_input_keys_to_clean_on_submit.append(f"{unique_key}_default_text")

                        for key in form_input_keys_to_clean_on_submit:
                            if key in st.session_state: 
                                del st.session_state[key]
                        # --- END FIX ---
                        
                        # ลบค่า CSV Quick Insert
                        csv_keys = [
                            f"quick_csv_ds_{dialog_state_key}",
                            f"quick_csv_row_{dialog_state_key}",
                            f"quick_csv_col_{dialog_state_key}",
                            f"quick_csv_target_{dialog_state_key}",
                        ]
                        for key in csv_keys:
                            if key in st.session_state:
                                del st.session_state[key]
                        
                        st.rerun()

        else:  # No keyword selected
            st.markdown("""
                <div class='empty-state'>
                    <div class='empty-state-icon'>👈</div>
                    <div class='empty-state-text'>Select a keyword from the left panel to configure its arguments</div>
                </div>
            """, unsafe_allow_html=True)