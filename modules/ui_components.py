"""
Shared UI Components
Reusable components for all modules
"""
import streamlit as st

# ======= CSV VALUE HELPER (SHARED) =======

def get_available_csv_datasources(ws_state):
    """
    Extract CSV data sources from workspace (works for all modules).
    
    Returns:
        dict: {ds_name: {ds_var, col_var, csv_filename, headers}}
    """
    from .crud_generator import manager  # Import here to avoid circular import
    
    result = {}
    data_sources = ws_state.get('data_sources', [])
    
    for ds in data_sources:
        ds_name = ds.get('name', '').upper()
        csv_filename = ds.get('file_name', '')
        col_var = ds.get('col_name', '')
        
        if not ds_name or not csv_filename:
            continue
        
        # Get CSV headers
        headers = manager.get_csv_headers(csv_filename)
        
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
                variable_syntax = f"${{{ds_var}['{row_key}'][${{{{col_var}.{selected_column}}}}}]}}"
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