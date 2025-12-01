import uuid
from .template_common import find_keyword, find_locator, create_step

def generate_delete_template(ws, all_keywords, all_locators):

    # CRITICAL: This structure MUST match manager.py _create_default_steps_structure()
    steps = {
        'suite_setup': [],
        'test_setup': [],
        'action_list': [],
        'action_form': [],        # Required by manager.py (empty for Delete)
        'action_detail': [],      # Required by manager.py (empty for Delete)
        'verify_list_search': [], # Required by manager.py (used in Delete)
        'verify_list_table': [],  # Required by manager.py (used in Delete)
        'verify_list_nav': [],    # Required by manager.py (empty for Delete)
        'verify_detail_page': [], # Required by manager.py (empty for Delete)
        'verify_detail_back': [], # Required by manager.py (empty for Delete)
        'test_teardown': [],
        'suite_teardown': []
    }
    
    # 1. Suite Setup (same as Create/Update)
    steps['suite_setup'] = _generate_suite_setup(all_keywords)
    
    # 2. Action List (Search -> Click Delete -> Confirm Modal)
    steps['action_list'] = _generate_action_list_delete(all_keywords, all_locators)
    
    # 3. Verify List (Search -> Verify rowdata=0)
    # This returns a dict with 'search' and 'table' keys
    verify_list_steps = _generate_verify_list_delete(all_keywords, all_locators)
    steps['verify_list_search'] = verify_list_steps['search']
    steps['verify_list_table'] = verify_list_steps['table']
    # Note: verify_list_nav is intentionally left empty for Delete
    
    # 4. Suite Teardown (same as Create/Update)
    steps['suite_teardown'] = _generate_suite_teardown(all_keywords)
    
    return steps


def _generate_suite_setup(all_keywords):
    """Generate Suite Setup steps (Login, Navigate) - Reused from Create/Update"""
    steps = []
    
    kw = find_keyword(all_keywords, 'Initialize System and Go to Login Page')
    if kw:
        steps.append(create_step(kw['name'], {}))
    
    kw = find_keyword(all_keywords, 'Login System')
    if kw:
        steps.append(create_step(kw['name'], {
            'username': '${USER_ADMIN}',
            'password': '${PASSWORD_ADMIN}'
        }))
    
    kw = find_keyword(all_keywords, 'Go to SUBMENU name')
    if kw:
        steps.append(create_step(kw['name'], {
            'main_menu': 'MENU_NAME',
            'submenu': 'SUB_MENU_NAME'
        }))
    
    kw = find_keyword(all_keywords, 'Verify Page Name is correct')
    if kw:
        steps.append(create_step(kw['name'], {
            'pagename': 'PAGE_NAME'
        }))
    
    return steps


def _generate_action_list_delete(all_keywords, all_locators):
    steps = []
    
    # 1. Fill search field
    kw_search = find_keyword(all_keywords, 'Fill in search field')
    if kw_search:
        loc_search = find_locator(all_locators, ['SEARCH', 'FILTER'])
        steps.append(create_step(kw_search['name'], {
            'locator_field': loc_search if loc_search else {'name': 'LOCATOR_SEARCH_INPUT'},
            'keyword': '${SEARCH_VALUE_TO_DELETE}'
        }))
    
    # 2. Click Search button
    kw_click = find_keyword(all_keywords, 'Click button on list page')
    if kw_click:
        loc_search_btn = find_locator(all_locators, ['SEARCH_BTN', 'SEARCH_BUTTON'])
        steps.append(create_step(kw_click['name'], {
            'locator_field': loc_search_btn['name'] if loc_search_btn else 'LOCATOR_SEARCH_BTN'
        }))

    # 3. Wait Loading Progress
    kw_wait = find_keyword(all_keywords, 'Wait Loading progress')
    if kw_wait:
        steps.append(create_step(kw_wait['name'], {}))

    # 4. Click Delete button
    if kw_click:
        loc_delete = find_locator(all_locators, ['DELETE_BTN', 'TRASH_BTN', 'REMOVE_BTN'])
        steps.append(create_step(kw_click['name'], {
            'locator_field': loc_delete['name'] if loc_delete else 'LOCATOR_DELETE_BTN'
        }))
        
    # 5. Click Modal OK to confirm deletion
    kw_modal = find_keyword(all_keywords, 'Click Modal Button')
    if kw_modal:
        steps.append(create_step(kw_modal['name'], {
            'button_name': 'OK'
        }))
    
    return steps


def _generate_verify_list_delete(all_keywords, all_locators):
    steps = {
        'search': [],
        'table': []
    }
    
    # 1. Fill search field again (to verify item is gone)
    kw_search = find_keyword(all_keywords, 'Fill in search field')
    if kw_search:
        loc_search = find_locator(all_locators, ['SEARCH', 'FILTER'])
        steps['search'].append(create_step(kw_search['name'], {
            'locator_field': loc_search if loc_search else {'name': 'LOCATOR_SEARCH_INPUT'},
            'keyword': '${SEARCH_VALUE_TO_DELETE}'
        }))
    
    # 2. Click Search button
    kw_click = find_keyword(all_keywords, 'Click button on list page')
    if kw_click:
        loc_search_btn = find_locator(all_locators, ['SEARCH_BTN', 'SEARCH_BUTTON'])
        steps['search'].append(create_step(kw_click['name'], {
            'locator_field': loc_search_btn['name'] if loc_search_btn else 'LOCATOR_SEARCH_BTN'
        }))
    
    # 3. Wait Loading Progress
    kw_wait = find_keyword(all_keywords, 'Wait Loading progress')
    if kw_wait:
        steps['search'].append(create_step(kw_wait['name'], {}))
    
    # ==================================================================
    # 4. (แก้ไขใหม่) Verify Data Table Result is No Record Found
    # ==================================================================
    kw_verify_norecord = find_keyword(all_keywords, 'Verify data table result is No Record Found')
    if kw_verify_norecord:
        steps['table'].append(create_step(kw_verify_norecord['name'], {
            # Key: ชื่อ Argument ใน Robot (ตามไฟล์ commonkeywords)
            # Value: ค่าที่จะส่งไป
            'locator_tbody': 'LOCATOR_TABLE_BODY',
            'msg_norecord': '${VAR_DEFAULT_NORECORDFOUND}'
        }))
    
    return steps

def _generate_suite_teardown(all_keywords):
    """Generate Suite Teardown steps (Logout, Close browser) - Reused from Create/Update"""
    steps = []
    
    kw = find_keyword(all_keywords, 'Logout System')
    if kw:
        steps.append(create_step(kw['name'], {}))
    
    kw = find_keyword(all_keywords, 'Close All Active Browsers')
    if kw:
        steps.append(create_step(kw['name'], {}))
    
    return steps