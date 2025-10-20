"""
Delete Template Generator
Generates a complete CRUD Delete test flow template
"""
import uuid
from .template_common import find_keyword, find_locator, create_step

def generate_delete_template(ws, all_keywords, all_locators):
    """
    Generate a complete Delete test template
    
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
        'action_detail': [],      # <-- ว่าง
        'verify_list': [],
        'verify_detail': [],      # <-- ว่าง
        'test_teardown': [],
        'suite_teardown': []
    }
    
    # 1. Suite Setup (เหมือน Create/Update)
    steps['suite_setup'] = _generate_suite_setup(all_keywords)
    
    # 2. Action List (Search -> Click Delete -> Confirm Modal)
    steps['action_list'] = _generate_action_list_delete(all_keywords, all_locators)
    
    # 3. Verify List (Search -> Verify rowdata=0)
    steps['verify_list'] = _generate_verify_list_delete(all_keywords, all_locators)
    
    # 4. Suite Teardown (เหมือน Create/Update)
    steps['suite_teardown'] = _generate_suite_teardown(all_keywords)
    
    return steps


def _generate_suite_setup(all_keywords):
    """Generate Suite Setup steps (Login, Navigate) - Reused from Update"""
    steps = []
    
    kw = find_keyword(all_keywords, 'Initialize System and Go to Login Page')
    if kw:
        steps.append(create_step(kw['name'], {}))
    
    kw = find_keyword(all_keywords, 'Login System')
    if kw:
        steps.append(create_step(kw['name'], {
            'headeruser': '${USER_ADMIN}',
            'headerpassword': '${PASSWORD_ADMIN}'
        }))
    
    kw = find_keyword(all_keywords, 'Go to SUBMENU name')
    if kw:
        steps.append(create_step(kw['name'], {
            'menuname': 'MENU_NAME',
            'submenuname': 'SUB_MENU_NAME'
        }))
    
    kw = find_keyword(all_keywords, 'Verify Page Name is correct')
    if kw:
        steps.append(create_step(kw['name'], {
            'pagename': 'PAGE_NAME'
        }))
    
    return steps


def _generate_action_list_delete(all_keywords, all_locators):
    """
    Generate Action List steps for Delete:
    1. Search for item
    2. Click Delete button
    3. Confirm modal
    """
    steps = []
    
    # 1. Fill search field
    kw_search = find_keyword(all_keywords, 'Fill in search field')
    if kw_search:
        loc_search = find_locator(all_locators, ['SEARCH', 'FILTER'])
        steps.append(create_step(kw_search['name'], {
            'locator_field': loc_search if loc_search else {'name': 'LOCATOR_SEARCH_INPUT'},
            'value': '${SEARCH_VALUE_TO_DELETE}'
        }))
    
    # 2. Click Search button
    kw_click = find_keyword(all_keywords, 'Click button on list page')
    if kw_click:
        loc_search_btn = find_locator(all_locators, ['SEARCH_BTN', 'SEARCH_BUTTON'])
        steps.append(create_step(kw_click['name'], {
            'locator': loc_search_btn['name'] if loc_search_btn else 'LOCATOR_SEARCH_BTN'
        }))
    
    # 3. Click Delete button
    if kw_click:
        loc_delete = find_locator(all_locators, ['DELETE_BTN', 'TRASH_BTN', 'REMOVE_BTN'])
        steps.append(create_step(kw_click['name'], {
            'locator': loc_delete['name'] if loc_delete else 'LOCATOR_DELETE_BTN'
        }))
        
    # 4. Click Modal OK
    kw_modal = find_keyword(all_keywords, 'Click Modal Button')
    if kw_modal:
        steps.append(create_step(kw_modal['name'], {
            'button_name': 'OK'
        }))
    
    return steps


def _generate_verify_list_delete(all_keywords, all_locators):
    """
    Generate Verify List steps for Delete:
    1. Search for item again
    2. Verify table shows 0 results
    """
    steps = []
    
    # 1. Fill search field again
    kw_search = find_keyword(all_keywords, 'Fill in search field')
    if kw_search:
        loc_search = find_locator(all_locators, ['SEARCH', 'FILTER'])
        steps.append(create_step(kw_search['name'], {
            'locator_field': loc_search if loc_search else {'name': 'LOCATOR_SEARCH_INPUT'},
            'value': '${SEARCH_VALUE_TO_DELETE}'
        }))
    
    # 2. Click Search button
    kw_click = find_keyword(all_keywords, 'Click button on list page')
    if kw_click:
        loc_search_btn = find_locator(all_locators, ['SEARCH_BTN', 'SEARCH_BUTTON'])
        steps.append(create_step(kw_click['name'], {
            'locator': loc_search_btn['name'] if loc_search_btn else 'LOCATOR_SEARCH_BTN'
        }))
    
    # 3. Verify Result of data table (expecting 0 rows)
    kw_verify_table = find_keyword(all_keywords, 'Verify Result of data table')
    if kw_verify_table:
        steps.append(create_step(kw_verify_table['name'], {
            'theader': 'LOCATOR_TABLE_HEADER',
            'tbody': 'LOCATOR_TABLE_BODY',
            'rowdata': '0',  # <-- นี่คือส่วนสำคัญ
            'ignore_case': '${True}',
            'assertion_columns': []
        }))
    
    return steps


def _generate_suite_teardown(all_keywords):
    """Generate Suite Teardown steps - Reused from Update"""
    steps = []
    
    kw = find_keyword(all_keywords, 'Logout System')
    if kw:
        steps.append(create_step(kw['name'], {}))
    
    kw = find_keyword(all_keywords, 'Close All Active Browsers')
    if kw:
        steps.append(create_step(kw['name'], {}))
    
    return steps