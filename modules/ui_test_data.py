import streamlit as st
import pandas as pd
import os
import uuid
import json
from datetime import datetime
from .file_manager import append_robot_content_intelligently, create_new_robot_file, append_to_api_base, scan_robot_project
from .utils import parse_data_sources

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def save_df_to_csv(project_path, filename, dataframe):
    """Save DataFrame to CSV in datatest folder"""
    try:
        if not filename.endswith('.csv'):
            filename += '.csv'
        datatest_folder = os.path.join(project_path, 'resources', 'datatest')
        os.makedirs(datatest_folder, exist_ok=True)
        full_path = os.path.join(datatest_folder, filename)
        dataframe.to_csv(full_path, index=False, encoding='utf-8')
        st.info(f"📂 Saved to: {full_path}")
        return True
    except Exception as e:
        st.error(f"❌ Error saving file: {str(e)}")
        return False

# ============================================================================
# DIALOGS
# ============================================================================

def csv_creator_dialog():
    """Renders the dialog for creating or uploading a CSV file"""
    ws_state = st.session_state.studio_workspace

    @st.dialog("Create/Upload CSV Data", width="large")
    def csv_creator():
        # ✅ CSS: ซ่อนปุ่ม X มุมขวาบน
        st.markdown("""
            <style>
            div[data-testid="stDialog"] button[aria-label="Close"] { display: none; }
            </style>
        """, unsafe_allow_html=True)

        st.markdown("#### <i class='fa-solid fa-file-csv'></i> Create or Upload CSV Data", unsafe_allow_html=True)
        
        mode = st.radio(
            "Create From:", ["New File", "Upload Existing File"],
            index=0 if ws_state.get('csv_creator_mode', 'New File') == 'New File' else 1,
            horizontal=True, label_visibility="collapsed"
        )
        ws_state['csv_creator_mode'] = mode
        st.markdown("---")

        if mode == "New File":
            st.subheader("Create a New CSV File")
            ws_state['csv_new_filename'] = st.text_input(
                "1. New File Name (in 'datatest' folder)", 
                value=ws_state.get('csv_new_filename', ''),
                key="csv_new_filename_input",
                placeholder="e.g., login_data.csv"
            )

            columns_input = st.text_input(
                "2. Define Columns (comma-separated)", 
                value=ws_state.get('csv_new_columns_str', ''),
                key="csv_new_columns_input",
                placeholder="e.g., username,password,role"
            )
            
            if columns_input != ws_state.get('csv_new_columns_str', ''):
                ws_state['csv_new_columns_str'] = columns_input
                if columns_input.strip():
                    columns = [col.strip() for col in columns_input.split(',') if col.strip()]
                    if columns:
                        ws_state['csv_columns_list'] = columns
                        if 'csv_rows_data' not in ws_state: ws_state['csv_rows_data'] = []
                        st.success(f"✅ Created table with {len(columns)} columns!")
                        st.rerun()
                    else:
                        ws_state['csv_columns_list'] = None; ws_state['csv_rows_data'] = []
                else:
                    ws_state['csv_columns_list'] = None; ws_state['csv_rows_data'] = []

            if ws_state.get('csv_columns_list'):
                st.markdown("---"); st.caption("3. Add Data Rows")
                columns = ws_state['csv_columns_list']
                
                with st.expander("➕ Add New Row", expanded=True):
                    st.markdown("**Fill in the values for each column:**")
                    new_row_data = {}
                    num_cols = len(columns)
                    cols_per_row = 2
                    for i in range(0, num_cols, cols_per_row):
                        cols = st.columns(cols_per_row)
                        for j in range(cols_per_row):
                            idx = i + j
                            if idx < num_cols:
                                col_name = columns[idx]
                                with cols[j]:
                                    new_row_data[col_name] = st.text_input(f"**{col_name}**", key=f"new_row_input_{col_name}", placeholder=f"Enter {col_name}...")
                    
                    if st.button("✅ Add Row", type="primary", use_container_width=True, key="add_row_btn"):
                        if any(value.strip() for value in new_row_data.values()):
                            ws_state.setdefault('csv_rows_data', []).append(new_row_data.copy())
                            st.success(f"✅ Row added!"); st.rerun()
                        else:
                            st.warning("⚠️ Please fill in at least one field.")

                st.markdown("---")
                if ws_state.get('csv_rows_data'):
                    st.markdown(f"**📋 Data Table ({len(ws_state['csv_rows_data'])} rows)**")
                    df = pd.DataFrame(ws_state['csv_rows_data'], columns=columns)
                    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, hide_index=False, key="simple_data_editor")
                    ws_state['csv_rows_data'] = edited_df.to_dict('records')

            st.markdown("---")
            
            col_save, col_cancel = st.columns([1, 1], gap="medium")
            with col_save:
                save_disabled = not (ws_state.get('csv_new_filename') and ws_state.get('csv_rows_data'))
                if st.button("💾 Save to datatest folder", type="primary", use_container_width=True, key="save_new_csv", disabled=save_disabled):
                    if not st.session_state.project_path:
                        st.error("⚠️ Please set the project path in the sidebar first.")
                    else:
                        if save_df_to_csv(st.session_state.project_path, ws_state['csv_new_filename'], pd.DataFrame(ws_state['csv_rows_data'], columns=ws_state['csv_columns_list'])):
                            st.success(f"✅ File '{ws_state['csv_new_filename']}' saved successfully!")
                            st.session_state.project_structure = scan_robot_project(st.session_state.project_path)
                            ws_state['csv_new_filename'] = ''; ws_state['csv_columns_list'] = None; ws_state['csv_rows_data'] = []
                            ws_state['show_csv_creator'] = False
                            st.rerun()
            
            with col_cancel:
                if st.button("❌ Cancel", type="secondary", use_container_width=True, key="cancel_new_csv"):
                    ws_state['show_csv_creator'] = False
                    ws_state['csv_new_filename'] = ''
                    ws_state['csv_new_columns_str'] = ''
                    ws_state['csv_columns_list'] = None
                    ws_state['csv_rows_data'] = []
                    st.rerun()

        elif mode == "Upload Existing File":
            st.subheader("Upload and Edit an Existing CSV")
            uploaded_file = st.file_uploader("1. Upload your CSV file", type=['csv'], key="csv_uploader_mode")
            
            if uploaded_file and uploaded_file.name != ws_state.get('csv_uploaded_filename'):
                ws_state['csv_uploaded_filename'] = uploaded_file.name; ws_state['csv_save_as_name'] = uploaded_file.name
                try:
                    df = pd.read_csv(uploaded_file)
                    ws_state['csv_uploaded_data'] = df
                    st.success(f"✅ Loaded {len(df)} rows and {len(df.columns)} columns!")
                except Exception as e: st.error(f"❌ Failed to read CSV: {e}")

            if ws_state.get('csv_uploaded_data') is not None:
                st.text_input("2. Save As", value=ws_state.get('csv_save_as_name', ''), key="csv_save_as_input", on_change=lambda: ws_state.update({'csv_save_as_name': st.session_state.csv_save_as_input}))
                st.caption("3. Edit Data")
                edited_df = st.data_editor(ws_state['csv_uploaded_data'], num_rows="dynamic", use_container_width=True, key="csv_data_editor_upload")
                ws_state['csv_uploaded_data'] = edited_df

            st.markdown("---")
            col_save, col_cancel = st.columns([1, 1], gap="medium")
            with col_save:
                if st.button("💾 Save to datatest folder", type="primary", use_container_width=True, key="save_uploaded_csv"):
                    if not ws_state.get('csv_save_as_name'): st.error("⚠️ Provide Save As name.")
                    elif ws_state.get('csv_uploaded_data') is None: st.error("⚠️ Upload file first.")
                    elif not st.session_state.project_path: st.error("⚠️ Set project path first.")
                    else:
                        if save_df_to_csv(st.session_state.project_path, ws_state['csv_save_as_name'], ws_state['csv_uploaded_data']):
                            st.success("✅ File saved!"); st.session_state.project_structure = scan_robot_project(st.session_state.project_path)
                            ws_state['show_csv_creator'] = False; st.rerun()
            with col_cancel:
                if st.button("❌ Cancel", type="secondary", use_container_width=True, key="cancel_uploaded_csv"):
                    ws_state['show_csv_creator'] = False
                    ws_state['csv_uploaded_filename'] = None
                    ws_state['csv_uploaded_data'] = None
                    st.rerun()

    csv_creator()

def data_source_export_dialog(source, index):
    """Export dialog for Data Sources"""
    @st.dialog(f"Export Code for: {source.get('name', '').upper()}", width="large")
    def export_dialog():
        ds_name = source.get('name')
        csv_file = source.get('file_name')
        col_name = source.get('col_name')
        if not (ds_name and csv_file and col_name): st.error("Missing Info"); return
        
        name_upper = ds_name.replace(" ", "").upper()
        var_name = f"CSVPATH_{name_upper}"
        kw_name = f"Import DataSource {ds_name.upper()}"
        col_var = col_name 
        ds_var = f"{name_upper}" 
        
        var_code = f"${{{var_name}}}            ${{CURDIR}}${{/}}datatest${{/}}{csv_file}"
        kw_code = (f"\n{kw_name}\n"
                   f"    Import datasource file        ${{{var_name}}}\n"
                   f"    Set Global Variable           ${{{col_var}}}                             ${{value_col}}\n"
                   f"    Set Global Variable           ${{{ds_var}}}                              ${{datasource_val}}")

        st.markdown("<h3><b>*** Variables ***</b></h3>", unsafe_allow_html=True); st.code(var_code, language="robotframework")
        st.markdown("<h3><b>*** Keywords ***</b></h3>", unsafe_allow_html=True); st.code(kw_code, language="robotframework")
        st.markdown("---"); st.subheader("💾 Save to Project File")
        
        if st.button("Append to datasources.resource", type="primary"):
            if not st.session_state.project_path: st.error("Set project path first.")
            else:
                target_path = os.path.join(st.session_state.project_path, "resources", "datasources.resource")
                success, msg = append_robot_content_intelligently(target_path, variables_code=var_code, keywords_code=kw_code)
                if success: st.toast(f"✅ Appended to: `{os.path.relpath(target_path, st.session_state.project_path)}`", icon="🎉")
                else: st.error(msg)
    export_dialog()

# ============================================================================
# MAIN RENDER FUNCTION
# ============================================================================

def render_test_data_tab():
    """Renders Test Data Tab (CSV & API) with Compact Design"""
    st.markdown("#### 🗃️ Test Data Management", unsafe_allow_html=True)
    ws_state = st.session_state.studio_workspace

    # Auto-load datasources.resource
    if not st.session_state.get('datasources_auto_loaded') and st.session_state.project_path:
        ds_path = os.path.join(st.session_state.project_path, 'resources', 'datasources.resource')
        if os.path.exists(ds_path):
            try:
                content = open(ds_path, 'r', encoding='utf-8').read()
                imported = parse_data_sources(content)
                if imported:
                    ws_state.setdefault('data_sources', [])
                    existing = {s['name'] for s in ws_state['data_sources']}
                    new_cnt = 0
                    for s in imported:
                        if s['name'] not in existing: ws_state['data_sources'].append(s); new_cnt += 1
                    if new_cnt > 0: st.success(f"✅ Auto-loaded {new_cnt} sources")
                st.session_state.datasources_auto_loaded = True
            except Exception as e: st.warning(f"⚠️ Load error: {e}"); st.session_state.datasources_auto_loaded = True
        else: st.session_state.datasources_auto_loaded = True

    # CSS for Buttons
    st.markdown("""<style>button[key="toggle_csv_datasources"],button[key="toggle_api_services"] { padding: 2px 8px !important; min-height: 28px !important; height: 28px !important; font-size: 0.85rem !important; }</style>""", unsafe_allow_html=True)

    # ------------------------------------------------------------------------
    # 📊 CSV Data Sources Section
    # ------------------------------------------------------------------------
    if 'show_csv_datasources' not in st.session_state: st.session_state.show_csv_datasources = True
    
    with st.container(border=True):
        c1, c2 = st.columns([20, 1])
        with c1:
            st.markdown("""<div style='display: flex; align-items: center; gap: 10px;'>
                <span style='font-size: 1.05rem; font-weight: 600; color: #cbd5e1;'>📊 CSV Data Sources</span>
            </div>""", unsafe_allow_html=True)
        with c2:
            toggle_icon = "▼" if st.session_state.show_csv_datasources else "▶"
            if st.button(toggle_icon, key="toggle_csv_datasources", use_container_width=True):
                st.session_state.show_csv_datasources = not st.session_state.show_csv_datasources
                st.rerun()
        
        if st.session_state.show_csv_datasources:    
            if st.button("➕ Create New CSV File", use_container_width=False, type="secondary"): 
                ws_state['show_csv_creator'] = True
                st.rerun()
            
            l_col, r_col = st.columns([1.1, 2], gap="large")
            
            # --- LEFT: Import ---
            with l_col:
                st.markdown("##### 📥 Import Data Sources")
                uploaded = st.file_uploader("Import from datasources.resource", type=['resource'], key="ds_imp", label_visibility="collapsed")
                if uploaded and uploaded.file_id != st.session_state.get('last_uploaded_ds_id'):
                    st.session_state['last_uploaded_ds_id'] = uploaded.file_id
                    try:
                        sources = parse_data_sources(uploaded.getvalue().decode("utf-8"))
                        if sources:
                            ws_state.setdefault('data_sources', [])
                            exist = {s['name'] for s in ws_state['data_sources']}
                            new_cnt = 0
                            for s in sources:
                                if s['name'] not in exist: ws_state['data_sources'].append(s); new_cnt += 1
                            if new_cnt > 0: st.success(f"Imported {new_cnt} links!"); st.rerun()
                            else: st.info("All exist.")
                        else: st.warning("No valid keywords found.")
                    except Exception as e: st.error(f"Error: {e}")
            
            # --- RIGHT: Link Table (Compact Design) ---
            with r_col:
                st.markdown("##### 🔗 Data Source Links")
                csv_opts = []
                if st.session_state.project_structure.get('csv_files'):
                    csv_opts = sorted(list(set([os.path.basename(f) for f in st.session_state.project_structure['csv_files'] if 'resources/datatest' in f.replace(os.sep, '/')])))

                if not ws_state.get('data_sources'):
                    st.info("No data source links defined.")
                else:
                    # ✅ CSS: เพิ่ม Style เพื่อบีบให้แถวชิดกัน
                    st.markdown("""
                    <style>
                        /* Header Styling */
                        .ds-header-row {
                            display: flex; gap: 1rem; padding: 0.4rem 0.2rem;
                            border-bottom: 1px solid #30363d; margin-bottom: 0.4rem;
                            font-size: 0.8rem; font-weight: 600; color: #8b949e; letter-spacing: 0.5px;
                        }
                        .ds-header-cell { flex: 1; }
                        /* Column Ratios (Match st.columns) */
                        .cell-2-5 { flex: 2.5; } .cell-2 { flex: 2; } .cell-1-5 { flex: 1.5; } .cell-0-6 { flex: 0.6; }
                        
                        /* Row Container */
                        .ds-row-container { padding: 2px 0; border-bottom: 1px solid rgba(48, 54, 61, 0.3); }
                        /* Compact Input */
                        .ds-row-container .stTextInput, .ds-row-container .stSelectbox, .ds-row-container .stButton { margin-bottom: 0px !important; }
                        /* Imported Label */
                        .imported-data-box { font-family: monospace; font-size: 0.8rem; color: #79c0ff; background: rgba(56, 139, 253, 0.1); padding: 4px 8px; border-radius: 4px; margin-top: 4px; }
                        .complete-form-label { opacity: 0.5; text-align: center; font-size: 0.8rem; margin-top: 6px; }
                    </style>
                    
                    <div class="ds-header-row">
                        <div class="ds-header-cell cell-2-5">NAME</div>
                        <div class="ds-header-cell cell-2-5">FILE</div>
                        <div class="ds-header-cell cell-2">COL VAR</div>
                        <div class="ds-header-cell cell-1-5">ACTIONS</div>
                        <div class="ds-header-cell cell-0-6"></div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    for i, src in enumerate(ws_state['data_sources']):
                        is_imp = src.get('is_imported', False)
                        
                        st.markdown('<div class="ds-row-container">', unsafe_allow_html=True)
                        # ✅ ใช้ gap="small" เพื่อบีบช่องว่างแนวตั้ง
                        rc = st.columns([2.5, 2.5, 2, 1.5, 0.6], gap="small")
                        
                        with rc[0]:
                            if is_imp: st.markdown(f'<div class="imported-data-box">{src.get("name")}</div>', unsafe_allow_html=True)
                            else: src['name'] = st.text_input(f"N{i}", src.get('name',''), key=f"ds_n_{i}", label_visibility="collapsed", placeholder="DS_NAME")
                        
                        with rc[1]:
                            if is_imp: st.markdown(f'<div class="imported-data-box">{src.get("file_name")}</div>', unsafe_allow_html=True)
                            else: 
                                opts = [''] + csv_opts
                                idx = opts.index(src.get('file_name')) if src.get('file_name') in opts else 0
                                src['file_name'] = st.selectbox(f"F{i}", opts, index=idx, key=f"ds_f_{i}", label_visibility="collapsed")
                        
                        with rc[2]:
                            if is_imp: st.markdown(f'<div class="imported-data-box">{src.get("col_name")}</div>', unsafe_allow_html=True)
                            else: src['col_name'] = st.text_input(f"C{i}", src.get('col_name',''), key=f"ds_c_{i}", label_visibility="collapsed", placeholder="col_var")
                        
                        with rc[3]:
                            if is_imp: 
                                st.markdown('<div class="imported-data-box" style="text-align:center; color:#8b949e; border:1px solid #30363d;">📋 Imported</div>', unsafe_allow_html=True)
                            elif src.get('name') and src.get('file_name') and src.get('col_name'):
                                if st.button("💾 Export", key=f"exp_{i}", use_container_width=True): 
                                    data_source_export_dialog(src, i)
                            else: 
                                st.markdown('<div class="complete-form-label">Complete Form</div>', unsafe_allow_html=True)
                        
                        with rc[4]:
                            if st.button("🗑️", key=f"del_ds_{i}", use_container_width=True, type="secondary"): 
                                ws_state['data_sources'].pop(i)
                                st.rerun()
                        
                        st.markdown('</div>', unsafe_allow_html=True)

                st.markdown("---")
                if st.button("🔗 Add Data Source Link (Manual)", use_container_width=True, type="secondary"):
                    ws_state.setdefault('data_sources', []).append({'name': '', 'file_name': '', 'col_name': '', 'is_imported': False})
                    st.rerun()

    # ------------------------------------------------------------------------
    # 🌐 API Services Section
    # ------------------------------------------------------------------------
    if 'show_api_services' not in st.session_state: st.session_state.show_api_services = False
    
    with st.container(border=True):
        c1, c2 = st.columns([20, 1])
        with c1:
            st.markdown("""<div style='display: flex; align-items: center; gap: 10px;'>
                <span style='font-size: 1.05rem; font-weight: 600; color: #cbd5e1;'>🌐 API Services</span>
            </div>""", unsafe_allow_html=True)
        with c2:
            toggle_icon = "▼" if st.session_state.show_api_services else "▶"
            if st.button(toggle_icon, key="toggle_api_services", use_container_width=True):
                st.session_state.show_api_services = not st.session_state.show_api_services
                st.rerun()
        
        if st.session_state.show_api_services:
            st.markdown("---")
            render_api_generator_tab()

# ============================================================================
# API SERVICES RENDERERS (Fully Included)
# ============================================================================

def render_api_generator_tab():
    """Renders API Generator content"""
    st.markdown("<h4 style='font-size: 1.4rem; margin-bottom: 0.5rem;'> 📡 Intelligent API Keyword Generator</h4>", unsafe_allow_html=True)
    st.caption("Generate robust Robot Framework API keywords from sample request/response data.")
    ws_state = st.session_state.studio_workspace
    if 'editing_api_service_id' not in ws_state: ws_state['editing_api_service_id'] = None

    act_c = st.columns([3, 1])
    with act_c[0]:
        if st.button("➕ Create New API Service", use_container_width=False, type="primary"):
            ws_state.setdefault('api_services', []).append({
                'id': str(uuid.uuid4()), 'service_name': 'service_newapi', 'path_var_name': 'VAR_PATH_NEWAPI',
                'endpoint_path': 'api/endpoint', 'http_method': 'POST', 'req_body_sample': '{\n  "key": "value"\n}',
                'analyzed_fields': {}, 'resp_body_sample': '{\n  "status": "success"\n}', 'response_extractions': [],
                'headers_type': 'custom', 'bearer_token_var': '${GLOBAL_ACCESS_TOKEN}', 'custom_header_use_uid_ucode': True,
                'custom_header_manual_pairs': 'Content-Type: application/json', 'add_status_validation': True,
                'status_field_path': 'status', 'status_success_value': 'success', 'error_message_path': 'message'
            })
            st.rerun()
    with act_c[1]:
        if ws_state.get('api_services') and st.button("🗑️ Clear All", use_container_width=True):
            ws_state['api_services'] = []; st.rerun()

    st.markdown("---")
    if ws_state['editing_api_service_id'] is None: render_api_list_view()
    else: render_api_editor_view()

def render_api_list_view():
    ws_state = st.session_state.studio_workspace
    st.markdown("<h4 style='font-size: 1.3rem; margin-bottom: 0.5rem;'><i class='fa-solid fa-link'></i> Your API Services</h4>", unsafe_allow_html=True)
    if not ws_state.get('api_services'): st.info("No API services defined."); return

    for i, svc in enumerate(ws_state.get('api_services', [])):
        with st.container(border=True):
            cols = st.columns([4, 1, 1])
            with cols[0]:
                st.markdown(f"<div style='font-size: 1.2rem; font-weight: 600;'>{svc.get('service_name')}</div><br>", unsafe_allow_html=True)
                st.markdown(f"<p style='font-size: 0.85rem; color: #a3a3a3; margin-top: -8px;'>PATH: <code>{svc.get('endpoint_path')}</code></p>", unsafe_allow_html=True)
            with cols[1]:
                if st.button("✏️ Edit", key=f"edit_api_{svc['id']}", use_container_width=True): ws_state['editing_api_service_id'] = svc['id']; st.rerun()
            with cols[2]:
                if st.button("🗑️ Delete", key=f"del_api_{svc['id']}", use_container_width=True): ws_state['api_services'].pop(i); st.rerun()

def render_api_editor_view():
    ws_state = st.session_state.studio_workspace
    svc_id = ws_state['editing_api_service_id']
    svc_data = next((s for s in ws_state['api_services'] if s['id'] == svc_id), None)
    if not svc_data: ws_state['editing_api_service_id'] = None; st.rerun(); return

    if st.button("← Back to Service List"): ws_state['editing_api_service_id'] = None; st.rerun()
    st.markdown(f"<br><div style='display:flex;align-items:center;gap:8px;margin-bottom:20px;'><span style='background:rgba(88,166,255,0.15);color:var(--primary-hover);padding:6px 12px;border-radius:6px;font-weight:600;'>✏️ Editing</span><span style='font-size:20px;font-weight:700;'>{svc_data.get('service_name')}</span></div>", unsafe_allow_html=True)

    l_p, r_p = st.columns([6, 5], gap="large")
    with l_p:
        st.markdown("<h2>Configuration</h2>", unsafe_allow_html=True)
        render_editor_form(svc_data)
    with r_p:
        st.markdown("<h2>Live Code Preview</h2>", unsafe_allow_html=True)
        render_live_code_preview(svc_data)

def render_editor_form(svc):
    sid = svc['id']
    with st.expander("📂 Endpoint & Configuration", expanded=True):
        svc['service_name'] = st.text_input("Service Name", svc['service_name'], key=f"en_sn_{sid}")
        c1, c2 = st.columns(2)
        svc['http_method'] = c1.selectbox("Method", ["POST", "GET", "PUT", "DELETE"], index=["POST", "GET", "PUT", "DELETE"].index(svc['http_method']), key=f"en_hm_{sid}")
        svc['endpoint_path'] = c2.text_input("Endpoint", svc['endpoint_path'], key=f"en_ep_{sid}")

    with st.expander("⚙️ Request Options", expanded=True):
        ops = ['simple', 'bearer', 'custom']
        svc['headers_type'] = st.selectbox("Header Type", ops, index=ops.index(svc.get('headers_type','simple')), key=f"ht_{sid}")
        if svc['headers_type'] == 'bearer': svc['bearer_token_var'] = st.text_input("Token Var", svc.get('bearer_token_var',''), key=f"bt_{sid}")
        elif svc['headers_type'] == 'custom':
            svc['custom_header_use_uid_ucode'] = st.checkbox("Use uid/ucode", svc.get('custom_header_use_uid_ucode', True), key=f"uid_{sid}")
        svc['custom_header_manual_pairs'] = st.text_area("Extra Headers", svc.get('custom_header_manual_pairs',''), key=f"eh_{sid}")

    with st.expander("📝 Request Body & Arguments", expanded=True):
        svc['req_body_sample'] = st.text_area("JSON Body", svc['req_body_sample'], height=200, key=f"rb_{sid}")
        if st.button("✨ Analyze", key=f"an_{sid}", use_container_width=True):
            try:
                flat = flatten_json_for_args(json.loads(svc['req_body_sample']))
                svc['analyzed_fields'] = {}
                for p, v in flat.items():
                    svc['analyzed_fields'][p] = {"value": v, "is_argument": False, "arg_name": p.replace('.','_').replace('[','_').replace(']',''), "json_path": p, "default_value": ""}
                st.success("Analyzed!"); st.rerun()
            except Exception as e: st.error(e)
        
        if svc.get('analyzed_fields'):
            st.markdown("---")
            for path, field in svc['analyzed_fields'].items():
                c1, c2, c3, c4 = st.columns([0.5, 2.5, 2, 2])
                field['is_argument'] = c1.checkbox("", field.get('is_argument',False), key=f"isa_{sid}_{path}")
                c2.markdown(f"`{path}`\n<span style='color:grey'>{str(field.get('value'))[:20]}</span>", unsafe_allow_html=True)
                field['arg_name'] = c3.text_input("Arg", field.get('arg_name',''), key=f"agn_{sid}_{path}", disabled=not field['is_argument'], label_visibility="collapsed")
                field['assigned_value'] = c4.text_input("Val", field.get('assigned_value',str(field.get('value',''))), key=f"asv_{sid}_{path}", label_visibility="collapsed")

    with st.expander("📥 Response Handling", expanded=True):
        svc['add_status_validation'] = st.checkbox("Validate Status", svc.get('add_status_validation', True), key=f"val_{sid}")
        if svc['add_status_validation']:
            c1, c2, c3 = st.columns(3)
            svc['status_field_path'] = c1.text_input("Status Path", svc.get('status_field_path','status'), key=f"sp_{sid}")
            svc['status_success_value'] = c2.text_input("Success Val", svc.get('status_success_value','success'), key=f"sv_{sid}")
            svc['error_message_path'] = c3.text_input("Error Path", svc.get('error_message_path','message'), key=f"ep_{sid}")
        
        st.markdown("---")
        svc['resp_body_sample'] = st.text_area("Response JSON", svc['resp_body_sample'], height=200, key=f"rbs_{sid}")
        if st.button("🔍 Find Vars", key=f"fv_{sid}", use_container_width=True):
            try:
                paths = flatten_json_with_paths(json.loads(svc['resp_body_sample']))
                svc.setdefault('response_extractions', [])
                exist = {x['json_path'] for x in svc['response_extractions']}
                for p, v in paths.items():
                    if p not in exist:
                        svc['response_extractions'].append({"id": str(uuid.uuid4()), "json_path": p, "sample_value": str(v)[:100], "is_enabled": False, "var_name": generate_variable_name_from_path(p)})
                st.success("Found vars!"); st.rerun()
            except Exception as e: st.error(e)
        
        if svc.get('response_extractions'):
            for item in svc['response_extractions']:
                c1, c2, c3 = st.columns([1, 4, 4])
                item['is_enabled'] = c1.checkbox("", item.get('is_enabled', False), key=f"rie_{item['id']}")
                c2.markdown(f"`{item['json_path']}`")
                item['var_name'] = c3.text_input("Var", item['var_name'], key=f"riv_{item['id']}", disabled=not item['is_enabled'], label_visibility="collapsed")

def render_live_code_preview(svc):
    with st.container(border=True):
        st.markdown("##### 📦 For `api_base.resource`")
        vc = generate_path_variable_code(svc)
        kc = generate_set_path_keyword_line(svc)
        st.code(vc, language='robotframework'); st.code(kc, language='robotframework')
        if st.button("💾 Append to api_base", key=f"apb_{svc['id']}", type="primary"):
            if st.session_state.project_path:
                tp = os.path.join(st.session_state.project_path, "resources", "services", "api_base.resource")
                s, m = append_to_api_base(tp, vc, kc)
                if s: st.success(m)
                else: st.error(m)

    with st.container(border=True):
        st.markdown("##### 📄 For service file")
        code = generate_main_keyword_code(svc)
        st.code(code, language='robotframework')
        
        opt = st.radio("Mode", ["Append", "Create"], key=f"smo_{svc['id']}", horizontal=True)
        if opt == "Append":
            files = [f for f in st.session_state.project_structure.get('robot_files',[]) if 'resources/services' in f.replace(os.sep,'/')]
            if files:
                sel = st.selectbox("File", sorted([f.replace(os.sep,'/') for f in files]), key=f"saf_{svc['id']}")
                if st.button("Append", key=f"ab_{svc['id']}"):
                    s, m = append_robot_content_intelligently(os.path.join(st.session_state.project_path, sel), keywords_code=code)
                    if s: st.success(m)
                    else: st.error(m)
        else:
            fn = st.text_input("Name", f"{svc['service_name']}.resource", key=f"nfn_{svc['id']}")
            if st.button("Create", key=f"cb_{svc['id']}"):
                path = os.path.join(st.session_state.project_path, "resources", "services", fn)
                c = f"*** Settings ***\nResource    ../../resources/resourcekeywords.resource\n\n*** Keywords ***\n{code}"
                if create_new_robot_file(path, c): st.success("Created!"); st.session_state.project_structure = scan_robot_project(st.session_state.project_path); st.rerun()

# Helper Functions for API
def flatten_json_for_args(obj, parent='', sep='.'):
    items = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{parent}{sep}{k}" if parent else k
            if isinstance(v, dict): items.update(flatten_json_for_args(v, new_key, sep))
            elif isinstance(v, list) and v and isinstance(v[0], dict): items.update(flatten_json_for_args(v[0], f"{new_key}[0]", sep=sep))
            else: items[new_key] = v
    elif isinstance(obj, list) and obj:
        if isinstance(obj[0], dict): items.update(flatten_json_for_args(obj[0], f"{parent_key}[0]", sep=sep))
        else: items[f"{parent_key}[0]"] = obj[0]
    else: items[parent_key] = obj
    return items

def flatten_json_with_paths(obj, parent_path=''):
    paths = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            np = f"{parent_path}.{k}" if parent_path else k
            if isinstance(v, (dict, list)): paths.update(flatten_json_with_paths(v, np))
            else: paths[np] = v
    elif isinstance(obj, list) and obj:
        for i, item in enumerate(obj):
            if i==0:
                np = f"{parent_path}[{i}]"
                if isinstance(item, (dict, list)): paths.update(flatten_json_with_paths(item, np))
                else: paths[np] = item
    return paths

def generate_variable_name_from_path(p):
    clean = p.replace('[0]', '').replace(']', '')
    parts = [x for x in clean.split('.') if x.lower() not in ['data', 'result']]
    if not parts: parts = clean.split('.')[-1:]
    return f"GLOBAL_{'_'.join(parts).upper()}"

def generate_path_variable_code(s): return f"${{VAR_PATH_{s.get('service_name','').replace('service_','').upper()}}}    {s.get('endpoint_path','')}"
def generate_set_path_keyword_line(s): return f"    Set Global Variable         ${{SERVICE_{s.get('service_name','').replace('service_','').upper()}_PATH}}           ${{URLTEST}}/${{API_URLPATH_TEST}}/${{VAR_PATH_{s.get('service_name','').replace('service_','').upper()}}}"

def rebuild_json_from_analyzed_fields(fields):
    res = {}
    for p, fd in fields.items():
        keys = p.split('.')
        curr = res
        for i, k in enumerate(keys[:-1]):
            ck = k.replace('[0]', '')
            if ck not in curr: curr[ck] = {}
            curr = curr[ck]
        lk = keys[-1].replace('[0]', '')
        if fd.get('is_argument'): curr[lk] = f"__PLACEHOLDER_{fd['arg_name']}__"
        else:
            val = fd.get('assigned_value', fd.get('value'))
            if val == 'null' or val == 'None': curr[lk] = None
            elif val == 'true': curr[lk] = True
            elif val == 'false': curr[lk] = False
            elif isinstance(val, str) and val.isdigit(): curr[lk] = int(val)
            else: curr[lk] = val
    return res

def generate_main_keyword_code(s):
    kw = f"Request {s.get('service_name','').replace('_',' ').title()}"
    args = ["${headeruser}", "${headerpassword}"]
    for p, f in s.get('analyzed_fields', {}).items():
        if f.get('is_argument'): args.append(f"${{{f['arg_name']}}}")
    
    arg_lines = []
    if len(args) <= 8: arg_lines.append(f"    [Arguments]    {'    '.join(args)}")
    else:
        arg_lines.append(f"    [Arguments]    {'    '.join(args[:8])}")
        for i in range(8, len(args), 8): arg_lines.append(f"    ...    {'    '.join(args[i:i+8])}")
    
    body_code = ""
    try:
        bd = rebuild_json_from_analyzed_fields(s.get('analyzed_fields', {}))
        pj = json.dumps(bd, indent=4, ensure_ascii=False)
        for p, f in s.get('analyzed_fields', {}).items():
            if f.get('is_argument'): pj = pj.replace(f'"__PLACEHOLDER_{f["arg_name"]}__"', f"${{{f['arg_name']}}}")
        
        bl = pj.split('\n')
        if len(bl) > 2:
            ol = ['    ${bodydata}=    Catenate    {']
            for l in bl[1:-1]: ol.append(f"    ...    {l}")
            ol.append('    ...    }')
            body_code = "\n".join(ol)
        else: body_code = f"    ${{bodydata}}=    Catenate    {pj}"
    except: body_code = f"    ${{bodydata}}=    Catenate    {s.get('req_body_sample','{}')}"

    prep = []; ex_args = [f"    ...    servicename={s.get('service_name')}", f"    ...    method={s.get('http_method')}", f"    ...    urlpath=${{VAR_PATH_{s.get('service_name','').replace('service_','').upper()}}}", "    ...    requestbody=${bodydata}", "    ...    expectedstatus=200"]
    
    custom = []
    if s.get('headers_type') == 'custom' and s.get('custom_header_use_uid_ucode'):
        prep.append("\n    api_base.Request Service for get session data    ${headeruser}    ${headerpassword}")
        custom.extend(["uid=${GLOBAL_API_UID}", "ucode=${GLOBAL_API_UCODE}"])
    if s.get('headers_type') == 'bearer': custom.append(f"Authorization=Bearer {s.get('bearer_token_var')}")
    
    manual = s.get('custom_header_manual_pairs','')
    if manual:
        for l in manual.split('\n'):
            if ':' in l: k, v = l.split(':', 1); custom.append(f"{k.strip()}={v.strip()}")
    
    if not custom: ex_args.append("    ...    headers_type=simple")
    else:
        ex_args.append("    ...    headers_type=custom_headers")
        prep.append(f"    &{{custom_headers_dict}}=    Create Dictionary    {'    '.join(custom)}")
        ex_args.append("    ...    &{custom_headers}=${custom_headers_dict}")

    val_code = []
    if s.get('add_status_validation'):
        val_code.extend([f"    ${{status_val}}=    Set Variable    ${{GLOBAL_RESPONSE_JSON}}[{s.get('status_field_path')}]", f"    IF    '${{status_val}}' == '{s.get('status_success_value')}'"])
        for m in s.get('response_extractions', []):
            if m.get('is_enabled'):
                rp = ''.join([f"[{p}]" for p in m['json_path'].replace(']','').replace('[','.').split('.')])
                val_code.append(f"        Set Global Variable    ${{{m['var_name']}}}    ${{GLOBAL_RESPONSE_JSON}}{rp}")
        val_code.extend(["    ELSE", f"        Fail    API Failed: ${{GLOBAL_RESPONSE_JSON}}[{s.get('error_message_path')}]", "    END"])
    else:
        for m in s.get('response_extractions', []):
            if m.get('is_enabled'):
                rp = ''.join([f"[{p}]" for p in m['json_path'].replace(']','').replace('[','.').split('.')])
                val_code.append(f"    Set Global Variable    ${{{m['var_name']}}}    ${{GLOBAL_RESPONSE_JSON}}{rp}")

    return "\n".join([kw, *arg_lines, *prep, body_code, "", "    utility-services.Execute API Request", *ex_args, "", *val_code])