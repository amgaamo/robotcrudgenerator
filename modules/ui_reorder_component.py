"""
Reusable Drag & Drop Reordering Component - V2 (Fixed Infinite Rerun)
Uses streamlit-sortables for intuitive reordering of Arguments and Steps
"""
import streamlit as st
from typing import List, Dict, Callable, Any


def render_sortable_arguments(keyword_id: str, kw: Dict) -> None:
    """
    Render draggable/sortable arguments list - RERUN SAFE VERSION
    """
    try:
        from streamlit_sortables import sort_items
    except ImportError:
        st.error("📦 **Missing Package:** `streamlit-sortables` is required.")
        st.code("pip install streamlit-sortables", language="bash")
        render_fallback_arguments(keyword_id, kw)
        return
    
    st.markdown("### 🧩 Keyword Arguments")
    
    current_args = kw.get('args', [])
    
    # Statistics & Actions
    col_stats, col_actions = st.columns([3, 1])
    with col_stats:
        st.caption(f"📊 **{len(current_args)} arguments** • Drag to reorder")
    with col_actions:
        if len(current_args) > 1:
            with st.popover("⚡", use_container_width=True):
                st.caption("**Quick Actions:**")
                if st.button("🔤 A→Z", use_container_width=True, key=f"sort_az_{keyword_id}"):
                    kw['args'] = sorted(current_args, key=lambda x: x['name'].lower())
                    st.rerun()
                if st.button("🔡 Z→A", use_container_width=True, key=f"sort_za_{keyword_id}"):
                    kw['args'] = sorted(current_args, key=lambda x: x['name'].lower(), reverse=True)
                    st.rerun()
                if st.button("🔄 Reverse", use_container_width=True, key=f"reverse_{keyword_id}"):
                    kw['args'] = list(reversed(current_args))
                    st.rerun()
    
    if not current_args:
        st.info("💡 No arguments yet. Add steps with variables like `${variable}`")
        return
    
    # ===== Drag & Drop Section =====
    with st.container(border=True):
        st.markdown("**🎯 Drag to Reorder**")
        
        # Create simple list of names ONLY
        arg_names = [arg['name'] for arg in current_args]
        
        # Sortable - ONLY names, no formatting
        sorted_names = sort_items(arg_names, key=f'args_sort_{keyword_id}')
        
        # Filter out any names that don't exist anymore (e.g., deleted)
        valid_sorted_names = [name for name in sorted_names if name in arg_names]
        
        # Check if order changed
        if valid_sorted_names != arg_names:
            # Rebuild in new order (safely)
            new_args = []
            for name in valid_sorted_names:
                matching_arg = next((a for a in current_args if a['name'] == name), None)
                if matching_arg:
                    new_args.append(matching_arg)
            
            if new_args:  # Only update if we have valid args
                kw['args'] = new_args
                st.rerun()
    
    st.markdown("")
    
    # ===== Edit Defaults Section (SEPARATE) =====
    with st.expander("📝 **Edit Default Values**", expanded=False):
        st.caption("Set optional default values:")
        
        for idx, arg in enumerate(current_args):
            col1, col2, col3, col4 = st.columns([0.5, 2, 2, 0.5])
            
            with col1:
                st.markdown(f"**{idx+1}**")
            
            with col2:
                st.code(arg['name'], language='robotframework')
            
            with col3:
                # Use session state directly
                input_key = f"default_{keyword_id}_{arg['name']}"
                
                # Initialize if not exists
                if input_key not in st.session_state:
                    st.session_state[input_key] = arg.get('default', '')
                
                new_val = st.text_input(
                    "Default",
                    key=input_key,
                    label_visibility="collapsed",
                    placeholder="e.g., ${EMPTY}"
                )
                
                # Update silently (no rerun)
                arg['default'] = new_val
            
            with col4:
                if st.button("🗑️", key=f"del_arg_{keyword_id}_{arg['name']}", 
                           help="Remove argument", use_container_width=True):
                    kw['args'] = [a for a in current_args if a['name'] != arg['name']]
                    # Clean up session state
                    if input_key in st.session_state:
                        del st.session_state[input_key]
                    # Clean up sortables state to prevent stale data
                    sortable_key = f'args_sort_{keyword_id}'
                    if sortable_key in st.session_state:
                        del st.session_state[sortable_key]
                    st.rerun()


def render_sortable_steps(keyword_id: str, kw: Dict) -> None:
    """
    Render draggable/sortable steps list - RERUN SAFE VERSION
    """
    try:
        from streamlit_sortables import sort_items
    except ImportError:
        st.error("📦 Missing streamlit-sortables")
        return
    
    steps = kw.get('steps', [])
    
    if not steps:
        st.info("No steps yet.")
        return
    
    st.caption(f"📊 **{len(steps)} steps** • Drag to reorder")
    
    # Check for control flow
    has_control_flow = any(s.get('keyword') in 
                          ['IF Condition', 'ELSE IF Condition', 'ELSE', 'END'] 
                          for s in steps)
    
    if has_control_flow:
        st.warning("⚠️ Contains IF/ELSE/END blocks. Reorder carefully!")
    
    with st.container(border=True):
        st.markdown("**🎯 Drag to Reorder**")
        
        # Create display list and map to actual step objects
        displays = []
        display_to_step = {}  # Map display → step object
        
        for idx, step in enumerate(steps):
            kw_name = step.get('keyword', 'Unknown')
            
            # Icon
            icon = ("🔀" if kw_name == 'IF Condition' 
                   else "↪️" if kw_name in ['ELSE IF Condition', 'ELSE']
                   else "🔚" if kw_name == 'END'
                   else "✏️" if 'Fill' in kw_name
                   else "🔍" if 'Verify' in kw_name
                   else "👆" if 'Click' in kw_name
                   else "▪️")
            
            # Extract locator info
            step_args = step.get('args', {})
            locator_info = ""
            
            if isinstance(step_args, dict):
                locator_field = step_args.get('locator_field', '')
                if locator_field:
                    # Clean up
                    if locator_field.startswith('${') and locator_field.endswith('}'):
                        locator_field = locator_field[2:-1]
                    if locator_field.startswith('LOCATOR_'):
                        locator_field = locator_field[8:]
                    
                    if len(locator_field) > 30:
                        locator_field = locator_field[:27] + '...'
                    
                    locator_info = f" → {locator_field}"
            
            # Create display WITHOUT index prefix (will be added by sortables)
            # Use step ID to make it unique
            step_id = step.get('id', f'step_{idx}')
            display = f"{icon} {kw_name}{locator_info} [{step_id[:8]}]"
            
            displays.append(display)
            display_to_step[display] = step  # Map display to actual step object
        
        # Sortable
        sorted_displays = sort_items(displays, key=f'steps_sort_{keyword_id}')
        
        # Check if changed
        if sorted_displays != displays:
            # Rebuild using display → step mapping
            new_steps = []
            for display in sorted_displays:
                if display in display_to_step:
                    new_steps.append(display_to_step[display])
            
            # Safety check
            if len(new_steps) == len(steps):
                kw['steps'] = new_steps
                st.rerun()
            else:
                st.error(f"⚠️ Reorder failed: {len(new_steps)}/{len(steps)} steps. Please refresh.")
                # Reset state
                if f'steps_sort_{keyword_id}' in st.session_state:
                    del st.session_state[f'steps_sort_{keyword_id}']


def render_fallback_arguments(keyword_id: str, kw: Dict) -> None:
    """Fallback when streamlit-sortables not available"""
    st.markdown("### 🧩 Keyword Arguments")
    
    current_args = kw.get('args', [])
    if not current_args:
        st.info("No arguments")
        return
    
    st.caption(f"📊 {len(current_args)} arguments")
    st.info("💡 Install `streamlit-sortables` for drag & drop: `pip install streamlit-sortables`")
    
    # Simple list
    for idx, arg in enumerate(current_args):
        col1, col2, col3, col4 = st.columns([0.5, 2.5, 2, 1.5])
        
        with col1:
            st.markdown(f"**{idx+1}**")
        
        with col2:
            st.code(arg['name'], language='robotframework')
        
        with col3:
            new_default = st.text_input(
                "Default",
                value=arg.get('default', ''),
                key=f"fb_default_{keyword_id}_{arg['name']}",
                label_visibility="collapsed"
            )
            arg['default'] = new_default
        
        with col4:
            subcols = st.columns([1, 1])
            with subcols[0]:
                if st.button("⏫", key=f"fb_top_{keyword_id}_{idx}",
                           disabled=(idx==0), use_container_width=True):
                    moved = current_args.pop(idx)
                    current_args.insert(0, moved)
                    kw['args'] = current_args
                    st.rerun()
            with subcols[1]:
                if st.button("⏬", key=f"fb_bot_{keyword_id}_{idx}",
                           disabled=(idx==len(current_args)-1), use_container_width=True):
                    moved = current_args.pop(idx)
                    current_args.append(moved)
                    kw['args'] = current_args
                    st.rerun()


def render_installation_instructions():
    """Show installation guide"""
    with st.expander("📦 **How to Enable Drag & Drop**"):
        st.markdown("""
        Install required package:
        ```bash
        pip install streamlit-sortables
        ```
        
        Or add to `requirements.txt`:
        ```
        streamlit-sortables
        ```
        """)