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
        
        /* ✅ FIX: เร่ง Dialog Animation */
        div[data-testid="stDialog"] {
            animation: fadeIn 0.15s ease-in !important;  /* เร็วขึ้นจาก 0.3s */
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: scale(0.98); }
            to { opacity: 1; transform: scale(1); }
        }
        
        /* Dialog container adjustments */
        div[data-testid="stDialog"] > div > div[data-testid="stVerticalBlock"] > div:first-child {
            padding-top: 0.5rem !important;
        }
        
        /* ✅ FIX: ลด blur effect เพื่อความเร็ว */
        div[data-testid="stDialog"] > div {
            background-color: rgba(15, 23, 42, 0.40) !important;  /* สีน้ำเงินเข้ม + โปร่ง */
            backdrop-filter: blur(8px) saturate(1.2) !important;  /* Blur + เพิ่มสีสัน */
            border: 1px solid rgba(255, 255, 255, 0.1) !important; /* ขอบโปร่งใส */
            transition: opacity 0.1s ease-in !important;  /* เร็วขึ้น */
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
            /* ✅ เพิ่ม GPU acceleration */
            will-change: transform;
            transform: translateZ(0);
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
            /* ✅ เพิ่ม GPU acceleration */
            will-change: transform;
            transform: translateZ(0);
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
        
        /* ✅ ปรับ Search box ให้ render เร็วขึ้น */
        div[data-testid="stDialog"] .stTextInput > div > div > input {
            background-color: #2d333b !important;
            border: 1px solid #444c56 !important;
            border-radius: 6px !important;
            padding: 0.65rem 1rem !important;
            font-size: 0.95rem !important;
            color: #adbac7 !important;
            transition: border-color 0.15s ease-in !important;  /* ลด transition time */
        }
        
        div[data-testid="stDialog"] .stTextInput > div > div > input:focus {
            border-color: #539bf5 !important;
            box-shadow: 0 0 0 2px rgba(83, 155, 245, 0.15) !important;  /* ลด shadow */
            background-color: #22272e !important;
        }
        
        div[data-testid="stDialog"] .stTextInput > div > div > input::placeholder {
            color: #768390 !important;
        }
        
        /* ✅ ปรับ Expander ให้ render เร็วขึ้น */
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
            transition: background-color 0.15s ease-in !important;  /* ลด transition */
            color: #adbac7 !important;
        }
        
        div[data-testid="stDialog"] [data-testid="stExpander"] > div:first-child:hover {
            background-color: #373e47 !important;
            border-color: #539bf5 !important;
        }
        
        /* ✅ ปรับ Button animation ให้เร็วขึ้น */
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
            transition: all 0.1s ease-in !important;  /* ลดจาก 0.2s */
        }
        
        div[data-testid="stDialog"] div[data-testid="stButton"] > button[kind="secondary"]:hover {
            border-color: #539bf5;
            background-color: #373e47;
            color: #cdd9e5;
            transform: translateX(2px);  /* ลดจาก 4px */
        }
        
        /* ✅ ซ่อน animation ที่ไม่จำเป็น */
        * {
            -webkit-tap-highlight-color: transparent;
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
@st.dialog("Add New Step", width="large", dismissible=False)
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
   
    # --- START: Manually inject Control Flow Keywords ---
    # (This ensures they *always* exist for any dialog that uses this base)
    categorized_keywords = ws_state.get('categorized_keywords', {}) # <-- นี่คือบรรทัดที่ 1 ที่มาแทนที่
    
    control_flow_kws = [
        {'name': 'IF Condition', 'args': [{'name': '${condition}', 'default': ''}], 'doc': 'Starts a conditional block.'},
        {'name': 'ELSE IF Condition', 'args': [{'name': '${condition}', 'default': ''}], 'doc': 'Starts an else-if block.'},
        {'name': 'ELSE', 'args': [], 'doc': 'Starts an else block.'},
        {'name': 'END', 'args': [], 'doc': 'Ends a conditional block.'}
    ]
    
    # Add them to the dictionary under a new category
    categorized_keywords['Control Flow'] = control_flow_kws
    
    # We also need to update the keyword_map so they can be "selected"
    keyword_map = {kw['name']: kw for kw in all_keywords_list} # <-- นี่คือบรรทัดที่ 2 ที่มาแทนที่
    for kw in control_flow_kws:
        if kw['name'] not in keyword_map:
            keyword_map[kw['name']] = kw
    # --- END: Manually inject Control Flow Keywords ---
    
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
        if st.button("← Back to Workspace", key=f"back_{dialog_state_key}", type="primary"):
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
            st.markdown(
                "<div style='font-size: 25px; font-weight: 600; margin-bottom: 0.5rem;'>⚙️ Configure Arguments</div>", 
                unsafe_allow_html=True
            )
    
            with st.container(border=True):
                st.markdown(
                    f"<span style='color: #1E90FF; font-weight: 600; font-size: 18px;'>{selected_kw['name']}</span>", 
                    unsafe_allow_html=True
                )
                st.caption(selected_kw.get('doc', 'No documentation available.'))

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
                        # ✅ แถว 1: Data Source + Data Test
                        col_ds, col_test = st.columns([1, 1])
                        
                        with col_ds:
                            quick_ds = st.selectbox(
                                "Data Source",
                                options=list(csv_keywords.keys()),
                                key=f"quick_csv_ds_{dialog_state_key}"
                            )
                        
                        quick_row_val = ""
                        with col_test:
                            # ✅ ดึงข้อมูลจากคอลัมน์แรกของ CSV
                            from modules.utils import util_get_csv_first_column_values
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
                                    key=f"quick_csv_row_{dialog_state_key}"
                                )
                            else:
                                quick_row_val = st.text_input(
                                    "Row Data Key",
                                    key=f"quick_csv_row_{dialog_state_key}",
                                    placeholder="e.g., robotapi"
                                )
                        
                        # ✅ แถว 2: Column + Insert to →
                        col_column, col_target = st.columns([1, 1])
                        
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
                                    st.warning("Please enter a 'Data Test'")
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
                
                # === Main Form - แก้ไข: ลบ st.form ออกเพื่อให้ Dropdown ทำงานโต้ตอบกันได้ ===
                kw_name_safe = selected_kw['name'].replace(' ', '_').replace('/', '_').replace('(', '').replace(')', '')
                # ลบบรรทัด form_key = ... ออก
                
                # ลบ with st.form(key=form_key): ออก (ขยับ code block ด้านล่างกลับมา 1 tab)
                
                # 🔴 START: ส่วนที่แก้ไข Indentation และลบ Form 🔴
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

                        current_value_in_state = st.session_state.get(unique_key)
                        if current_value_in_state is not None:
                            arg_info['default'] = current_value_in_state

                        # --- (1) ส่ง selected_kw_name ---
                        rendered_value = render_argument_input(
                            arg_info,
                            ws_state,
                            unique_key,
                            current_value=current_value_in_state,
                            selected_kw_name=selected_kw.get('name') 
                        )

                st.markdown("---")

                # เปลี่ยนจาก st.form_submit_button เป็น st.button ปกติ
                submitted_add = st.button(
                    f"✅ Add Step to Workspace",
                    key=f"btn_submit_add_{dialog_state_key}", # ต้องเพิ่ม key ไม่ให้ซ้ำ
                    type="primary",
                    use_container_width=True
                )

                if submitted_add:
                    final_args_data = {}
                    if selected_kw.get('args'):
                        for i, arg_item in enumerate(selected_kw.get('args', [])):
                            arg_info = arg_item.copy() if isinstance(arg_item, dict) else {'name': str(arg_item), 'default': ''}
                            raw_arg_name = arg_info.get('name')
                            if not raw_arg_name: continue

                            clean_arg_name = raw_arg_name.strip('${}')
                            arg_info['name'] = clean_arg_name
                            # Key ต้องเหมือนกับตอน Render เป๊ะๆ
                            unique_key = f"{dialog_state_key}_{kw_name_safe}_{clean_arg_name}_{i}"
                            
                            kw_name_lower = str(selected_kw.get('name', '')).lower()
                            arg_lower = clean_arg_name.lower()

                            # ---------------------------------------------------------
                            # ✅ FINAL SAVE LOGIC (Priority: Menu > Preset > Locator > Pattern > Default)
                            # ---------------------------------------------------------
                            final_value = None

                            # 1. Menu Locators (สูงสุด)
                            if 'go to menu name' in kw_name_lower and clean_arg_name == 'menu_locator':
                                selected_main = st.session_state.get(f"{unique_key}_main_menu_select", '')
                                final_value = f"${{mainmenu}}[{selected_main}]" if selected_main else ""
                            elif 'go to submenu name' in kw_name_lower and clean_arg_name == 'main_menu':
                                final_value = st.session_state.get(f"{unique_key}_main_menu_select", '')
                            elif 'go to submenu name' in kw_name_lower and clean_arg_name == 'submenu':
                                final_value = st.session_state.get(f"{unique_key}_sub_menu_select", '')
                            # elif clean_arg_name == 'pagename':
                            #     selected_page_key = st.session_state.get(f"{unique_key}_pagename_select", '')
                            #     final_value = f"${{menuname}}[{selected_page_key}]" if selected_page_key else ""

                            # 2. PRESETS (เช่น button_name, status)
                            # ✅ สำคัญ: ต้องเช็ค Preset ก่อน Locator
                            elif clean_arg_name in ARGUMENT_PRESETS:
                                config = ARGUMENT_PRESETS[clean_arg_name]
                                input_type = config.get('type')
                                if input_type == "select_or_input":
                                    selected = st.session_state.get(f"{unique_key}_select")
                                    if selected == "📝 Other (custom)":
                                        final_value = st.session_state.get(f"{unique_key}_custom")
                                    else:
                                        final_value = selected
                                elif input_type == "boolean":
                                    final_value = 'true' if st.session_state.get(unique_key, False) else 'false'
                                else: 
                                    final_value = st.session_state.get(unique_key)

                            # 3. LOCATOR (เช็คคำว่า button, field ฯลฯ)
                            elif any(s in arg_lower for s in ['locator', 'field', 'button', 'element', 'header', 'body', 'theader', 'tbody']):
                                final_value = st.session_state.get(f"{unique_key}_locator_select")

                            # 4. PATTERNS (เช่น timeout, password)
                            else:
                                matched_pattern = False
                                for pattern_key in ARGUMENT_PATTERNS.keys():
                                    if pattern_key in arg_lower:
                                        # Pattern ใช้ key หลัก
                                        final_value = st.session_state.get(unique_key)
                                        matched_pattern = True
                                        break
                                
                                # 5. DEFAULT
                                if not matched_pattern:
                                    # Default ใช้ _default_text
                                    final_value = st.session_state.get(f"{unique_key}_default_text")

                            # Fallback
                            if final_value is None:
                                final_value = st.session_state.get(unique_key, '')

                            final_args_data[clean_arg_name] = final_value
                        # --- END: MODIFIED SMART KEY LOGIC ---

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
                    
                    # Cleanup Logic (ต้องแก้ให้ลบ key ของ locator select ด้วย)
                    form_input_keys_to_clean_on_submit = []
                    if selected_kw.get('args'):
                        for i, arg_item in enumerate(selected_kw.get('args', [])):
                            clean_arg_name = arg_item.get('name', '').strip('${}')
                            if not clean_arg_name: continue
                            
                            unique_key = f"{dialog_state_key}_{kw_name_safe}_{clean_arg_name}_{i}"
                            
                            form_input_keys_to_clean_on_submit.append(unique_key)
                            form_input_keys_to_clean_on_submit.append(f"{unique_key}_locator_select") # ลบ key นี้
                            form_input_keys_to_clean_on_submit.append(f"{unique_key}_page_select")    # ลบ key นี้ด้วย
                            form_input_keys_to_clean_on_submit.append(f"{unique_key}_main_menu_select")
                            form_input_keys_to_clean_on_submit.append(f"{unique_key}_sub_menu_select")
                            form_input_keys_to_clean_on_submit.append(f"{unique_key}_pagename_select")
                            form_input_keys_to_clean_on_submit.append(f"{unique_key}_select")
                            form_input_keys_to_clean_on_submit.append(f"{unique_key}_custom")
                            form_input_keys_to_clean_on_submit.append(f"{unique_key}_default_text")

                    for key in form_input_keys_to_clean_on_submit:
                        if key in st.session_state: 
                            del st.session_state[key]

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