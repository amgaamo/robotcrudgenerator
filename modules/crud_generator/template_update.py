"""
Update Template Generator
Generates a complete CRUD Update test flow template
"""
import uuid
from .template_common import find_keyword, find_locator, create_step, get_form_locators


def generate_update_template(ws, all_keywords, all_locators):
    """
    Generate a complete Update test template
    
    Args:
        ws: Workspace dictionary
        all_keywords: List of available keywords
        all_locators: List of available locators
    
    Returns:
        Dictionary of steps organized by section
    """
    steps = {
        'suite_setup': [],
        'test_setup': [],
        'action_list': [],
        'action_detail': [],
        'verify_list': [],
        'verify_detail': [],
        'test_teardown': [],
        'suite_teardown': []
    }
    
    # 1. Suite Setup (same as Create)
    steps['suite_setup'] = _generate_suite_setup(all_keywords)
    
    # 2. Action List (Search + Click Edit) - DIFFERENT
    steps['action_list'] = _generate_action_list_update(all_keywords, all_locators)
    
    # 3. Action Detail (Modify form + Save) - DIFFERENT
    steps['action_detail'] = _generate_action_detail_update(all_keywords, all_locators, ws)
    
    # 4. Verify List (Search updated item) - DIFFERENT
    steps['verify_list'] = _generate_verify_list_update(all_keywords, all_locators, ws)
    
    # 5. Verify Detail (Verify updated fields) - DIFFERENT
    steps['verify_detail'] = _generate_verify_detail_update(all_keywords, all_locators, ws)
    
    # 6. Suite Teardown (same as Create)
    steps['suite_teardown'] = _generate_suite_teardown(all_keywords)
    
    return steps


def _generate_suite_setup(all_keywords):
    """Generate Suite Setup steps (Login, Navigate) - Same as Create"""
    steps = []
    
    # 1. Initialize System
    kw = find_keyword(all_keywords, 'Initialize System and Go to Login Page')
    if kw:
        steps.append(create_step(kw['name'], {}))
    
    # 2. Login
    kw = find_keyword(all_keywords, 'Login System')
    if kw:
        steps.append(create_step(kw['name'], {
            'headeruser': '${USER_ADMIN}',
            'headerpassword': '${PASSWORD_ADMIN}'
        }))
    
    # 3. Navigate to menu
    kw = find_keyword(all_keywords, 'Go to SUBMENU name')
    if kw:
        steps.append(create_step(kw['name'], {
            'menuname': 'MENU_NAME',
            'submenuname': 'SUB_MENU_NAME'
        }))
    
    # 4. Verify page name
    kw = find_keyword(all_keywords, 'Verify Page Name is correct')
    if kw:
        steps.append(create_step(kw['name'], {
            'pagename': 'PAGE_NAME'
        }))
    
    return steps


def _generate_action_list_update(all_keywords, all_locators):
    """
    Generate Action List steps for Update
    Different from Create: Search existing item + Click Edit
    """
    steps = []
    
    # 1. Fill search field with existing item
    kw_search = find_keyword(all_keywords, 'Fill in search field')
    if kw_search:
        loc_search = find_locator(all_locators, ['SEARCH', 'FILTER'])
        steps.append(create_step(kw_search['name'], {
            'locator_field': loc_search if loc_search else {'name': 'LOCATOR_SEARCH_INPUT'},
            'value': '${SEARCH_VALUE_TO_UPDATE}'  # Variable for item to update
        }))
    
    # 2. Click Search button
    kw_click = find_keyword(all_keywords, 'Click button on list page')
    if kw_click:
        loc_search_btn = find_locator(all_locators, ['SEARCH_BTN', 'SEARCH_BUTTON'])
        steps.append(create_step(kw_click['name'], {
            'locator': loc_search_btn['name'] if loc_search_btn else 'LOCATOR_SEARCH_BTN'
        }))
    
    # 3. Click Edit button (DIFFERENT from Create which clicks New)
    if kw_click:
        loc_edit = find_locator(all_locators, ['EDIT_BTN', 'PENCIL', 'MODIFY_BTN'])
        steps.append(create_step(kw_click['name'], {
            'locator': loc_edit['name'] if loc_edit else 'LOCATOR_EDIT_BTN'
        }))
    
    return steps


def _generate_action_detail_update(all_keywords, all_locators, ws):
    """
    Generate Action Detail steps for Update (Save + Modal only)
    User will manually add form modification steps
    """
    steps = []
    
    # User will manually add fill steps via UI
    # No auto-generation of form fields
    
    # 2. Click Save button
    kw_click = find_keyword(all_keywords, 'Click button on detail page')
    if kw_click:
        loc_save = find_locator(all_locators, ['SAVE', 'SUBMIT', 'CONFIRM'])
        steps.append(create_step(kw_click['name'], {
            'locator': loc_save['name'] if loc_save else 'LOCATOR_SAVE_BTN'
        }))
    
    # 3. Click Modal OK
    kw_modal = find_keyword(all_keywords, 'Click Modal Button')
    if kw_modal:
        steps.append(create_step(kw_modal['name'], {
            'button_name': 'OK'
        }))
    
    return steps


def _generate_verify_list_update(all_keywords, all_locators, ws):
    """
    Generate Verify List steps for Update
    Different from Create: Search for updated value
    """
    steps = []
    
    # 1. Fill search field with UPDATED value
    kw_search = find_keyword(all_keywords, 'Fill in search field')
    if kw_search:
        loc_search = find_locator(all_locators, ['SEARCH', 'FILTER'])
        steps.append(create_step(kw_search['name'], {
            'locator_field': loc_search if loc_search else {'name': 'LOCATOR_SEARCH_INPUT'},
            'value': '${UPDATED_VALUE}'  # Search for the updated value
        }))
    
    # 2. Click Search button
    kw_click = find_keyword(all_keywords, 'Click button on list page')
    if kw_click:
        loc_search_btn = find_locator(all_locators, ['SEARCH_BTN', 'SEARCH_BUTTON'])
        steps.append(create_step(kw_click['name'], {
            'locator': loc_search_btn['name'] if loc_search_btn else 'LOCATOR_SEARCH_BTN'
        }))
    
    # 3. Verify Result of data table (should show updated item)
    kw_verify_table = find_keyword(all_keywords, 'Verify Result of data table')
    if kw_verify_table:
        steps.append(create_step(kw_verify_table['name'], {
            'theader': 'LOCATOR_TABLE_HEADER',
            'tbody': 'LOCATOR_TABLE_BODY',
            'rowdata': '1',
            'ignore_case': '${True}',
            'assertion_columns': []  # User can configure columns to verify
        }))
    
    # 4. Click View button to verify details
    if kw_click:
        loc_view = find_locator(all_locators, ['VIEW_BTN', 'EDIT_BTN'])
        steps.append(create_step(kw_click['name'], {
            'locator': loc_view['name'] if loc_view else 'LOCATOR_VIEW_BTN'
        }))
    
    return steps


def _generate_verify_detail_update(all_keywords, all_locators, ws):  # ← เพิ่ม all_locators
    """
    Generate Verify Detail steps for Update (Back button only)
    User will manually add verification steps
    """
    steps = []
    
    # User will manually add verify steps via UI
    # No auto-generation from fill steps
    
    # Click Back button
    kw_click = find_keyword(all_keywords, 'Click button on detail page')
    if kw_click:
        loc_back = find_locator(all_locators, ['BACK_BTN', 'BACK_BUTTON'])  # ← ตอนนี้มี all_locators แล้ว
        steps.append(create_step(kw_click['name'], {
            'locator': loc_back['name'] if loc_back else 'LOCATOR_BACK_BTN'
        }))
    
    return steps


def _generate_suite_teardown(all_keywords):
    """Generate Suite Teardown steps - Same as Create"""
    steps = []
    
    # 1. Logout
    kw = find_keyword(all_keywords, 'Logout System')
    if kw:
        steps.append(create_step(kw['name'], {}))
    
    # 2. Close browsers
    kw = find_keyword(all_keywords, 'Close All Active Browsers')
    if kw:
        steps.append(create_step(kw['name'], {}))
    
    return steps