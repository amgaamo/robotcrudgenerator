"""
Robot Framework Locator Generator - Main Application
Clean architecture with separated backend modules
"""

import streamlit as st
from streamlit_option_menu import option_menu

# Backend imports
from modules.session_manager import init_session_state 
from modules.styles import get_css

# UI Modules Imports (New Modular Structure)
from modules.ui_components import render_header
from modules.ui_sidebar import render_sidebar
from modules.ui_assets import render_resources_view_new, html_editor_dialog
from modules.ui_test_data import render_test_data_tab, csv_creator_dialog

# Existing Modules
from modules.crud_generator import manager as crud_manager
from modules.crud_generator.ui_crud import (
    render_crud_generator_tab, render_fill_form_dialog, render_verify_detail_dialog, 
    render_api_csv_step_dialog, render_kw_factory_import_dialog
)
from modules import kw_manager
from modules.ui_keyword_factory import (
    render_keyword_factory_tab, render_kw_factory_fill_form_dialog, 
    render_kw_factory_verify_detail_dialog, render_kw_factory_api_csv_step_dialog
)
from modules.dialog_commonkw import render_add_step_dialog_base

# HTML Parser Check
try:
    from modules.html_parser import HTMLLocatorParser
    PARSER_AVAILABLE = True
except ImportError:
    PARSER_AVAILABLE = False

# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title="RF Code Generator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply styles
st.markdown(get_css(), unsafe_allow_html=True)

# ============================================================================
# RENDER STUDIO TAB (Orchestrator with Original Design)
# ============================================================================

def render_studio_tab():
    """ 
    Renders the "Studio Workspace" using streamlit-option-menu
    to maintain the original design look & feel.
    """
    
    # 1. รายชื่อเมนูและไอคอน (ตามต้นฉบับ)
    tab_options_list = [
        "Assets", 
        "Test Data",
        "Keyword Factory", 
        "CRUD Generator"
    ]
    
    tab_icons = [
        "safe2-fill",
        "server",
        "gear-wide-connected",
        "rocket-takeoff"
    ]   

    # 2. จัดการ State ของ Tab ที่เลือก
    if 'main_studio_tab_index' not in st.session_state:
        st.session_state.main_studio_tab_index = 0

    # 3. Wrapper Div เพื่อจัด layout ให้สวยงาม (เหมือนต้นฉบับ)
    st.markdown("<div style='width: fit-content; max-width: 100%; margin-bottom: 10px;'>", unsafe_allow_html=True)

    selected_tab_name = option_menu(
        menu_title=None,
        options=tab_options_list,
        icons=tab_icons,
        key="main_studio_tabs",
        orientation="horizontal",
        default_index=st.session_state.main_studio_tab_index,
        
        # --- CSS Styles ตามต้นฉบับ ---
        styles={
            "container": {
                "padding": "6px !important", 
                "background-color": "transparent",
                "border": "1px solid #30363d",   
                "border-radius": "12px",           
                "margin-bottom": "1rem",
            },
            "icon": {
                "font-size": "1rem", 
                "margin-right": "6px", 
            },
            "nav-link": {
                "font-size": "0.9rem",
                "font-weight": "600",
                "color": "#8b949e",
                "background-color": "transparent",
                "border-radius": "8px",
                "padding": "8px 14px",
                "transition": "all 0.3s ease",
                "margin": "0 4px",
            },
            "nav-link:hover": {
                "background-color": "rgba(48, 54, 61, 0.7)", 
                "color": "#c9d1d9"
            },
            "nav-link-selected": {
                "background-color": "#f85149", 
                "color": "#ffffff",
                "border-radius": "8px",
            },
            "nav-link-selected:hover": {
                "background-color": "#6cb0ff", 
                "color": "#ffffff",
            }
        }
    )
    
    st.markdown("</div>", unsafe_allow_html=True) 

    # # Header ของ Workspace
    # st.markdown("## <br><i class='bi bi-robot'></i> Studio Workspace", unsafe_allow_html=True)
    # st.caption("A visual editor to build your complete Robot Framework test script.")
    # st.markdown("---")
    
    # 4. อัปเดต State และเรียก Render ฟังก์ชันตาม Tab ที่เลือก
    try:
        st.session_state.main_studio_tab_index = tab_options_list.index(selected_tab_name)
    except ValueError:
        st.session_state.main_studio_tab_index = 0
    
    if selected_tab_name == "Assets":
        render_resources_view_new()

    elif selected_tab_name == "Test Data":
        render_test_data_tab()

    elif selected_tab_name == "Keyword Factory":
        render_keyword_factory_tab()

    elif selected_tab_name == "CRUD Generator":
        render_crud_generator_tab()

# ============================================================================
# MAIN APPLICATION
# ============================================================================

def main():
    """Main application entry point"""
    init_session_state()
    
    # Inject Bootstrap Icons
    st.markdown(
        '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.css">',
        unsafe_allow_html=True
    )

    ws_state = st.session_state.studio_workspace

    # --- Callback Functions ---
    def add_step_to_crud(context_dict, new_step):
        section_key = context_dict.get("key")
        if section_key:
            crud_manager.add_step(section_key, new_step)

    def crud_keyword_filter(keyword):
        kw_name = keyword.get('name', '').lower()
        return not (kw_name.startswith('import datasource') or kw_name.startswith('request service'))

    def add_step_to_kw(context_dict, new_step):
        kw_id = context_dict.get("key")
        if kw_id:
            # Handle control flow args defaults
            if new_step.get('keyword') == 'IF Condition' and 'args' not in new_step:
                 new_step['args'] = {'condition': ''}
            elif new_step.get('keyword') == 'END':
                 new_step['args'] = {}
            kw_manager.add_step(kw_id, new_step)

    def kw_factory_filter(keyword):
        all_generated_kw_names = [kw['name'] for kw in kw_manager.get_all_keywords()]
        kw_name = keyword.get('name', '')
        if kw_name.lower().startswith(('import datasource', 'request service')): return False
        if kw_name in ['IF Condition', 'ELSE IF Condition', 'ELSE', 'END']: return True
        if kw_name in all_generated_kw_names: return False
        return True
    
    # Placeholder for Test Flow callback (if needed later)
    def add_step_to_timeline(context_timeline_key, new_step):
        ws_state.setdefault(context_timeline_key, []).append(new_step)


    # --- Dialog Routing (Controller Logic) ---
    
    # 1. CRUD Generator Dialogs
    if st.session_state.get('show_crud_add_dialog'):
        render_add_step_dialog_base(
            dialog_state_key='show_crud_add_dialog',
            context_state_key='crud_add_dialog_context',
            selected_kw_state_key='selected_kw_crud',
            add_step_callback=add_step_to_crud,
            ws_state=ws_state,
            title=f"Add New Step to CRUD Flow",
            keyword_filter_func=crud_keyword_filter,
            search_state_key="kw_search_dialog_crud",
            recently_used_state_key="recently_used_keywords_crud"
        )
        return

    elif st.session_state.get('show_api_csv_dialog'):
        render_api_csv_step_dialog()
        return
        
    elif st.session_state.get('show_fill_form_dialog'):
        render_fill_form_dialog()
        return
        
    elif st.session_state.get('show_verify_detail_dialog'):
        render_verify_detail_dialog()
        return

    elif st.session_state.get('show_kw_factory_dialog'):
        render_kw_factory_import_dialog()
        return

    # 2. Keyword Factory Dialogs
    elif st.session_state.get('show_kw_factory_add_dialog'):
        render_add_step_dialog_base(
            dialog_state_key='show_kw_factory_add_dialog',
            context_state_key='kw_factory_add_dialog_context',
            selected_kw_state_key='selected_kw_kw_factory',
            add_step_callback=add_step_to_kw,
            ws_state=ws_state,
            title=f"Add Step to Keyword",
            keyword_filter_func=kw_factory_filter,
            search_state_key="kw_search_dialog_kw_factory",
            recently_used_state_key="recently_used_keywords_kw_factory",
        )
        return
        
    elif st.session_state.get('show_kw_factory_fill_form_dialog'):
        render_kw_factory_fill_form_dialog()
        return
        
    elif st.session_state.get('show_kw_factory_verify_dialog'):
        render_kw_factory_verify_detail_dialog()
        return
        
    elif st.session_state.get('show_kw_factory_api_csv_dialog'):
        render_kw_factory_api_csv_step_dialog()
        return

    # 3. Test Flow / Timeline Dialogs (Future Use)
    elif st.session_state.get('show_add_dialog'):
        render_add_step_dialog_base(
            dialog_state_key='show_add_dialog',
            context_state_key='add_dialog_timeline',
            selected_kw_state_key='selected_kw',
            add_step_callback=add_step_to_timeline,
            ws_state=ws_state,
            title=f"Add New Step to Timeline",
            search_state_key="kw_search_dialog_testflow",
            recently_used_state_key="recently_used_keywords"
        )
        return

    # 4. CSV Creator Dialog (Global)
    elif ws_state.get('show_csv_creator'):
        csv_creator_dialog()
        return
    
    # 5. HTML Editor Dialog (Modal Check)
    if ws_state.get('editing_html_index') is not None:
        if ws_state['editing_html_index'] < len(ws_state['html_pages']):
            html_editor_dialog()

    # --- Main Render Sequence ---
    render_sidebar()
    render_header()
    
    if not PARSER_AVAILABLE:
        st.error("HTML Parser module not available. Please check installation.")
        return

    render_studio_tab()

if __name__ == "__main__":
    main()