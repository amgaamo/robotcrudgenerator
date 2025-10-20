"""
Test Flow Manager Module
Handles the business logic for the Test Flow tab, including script generation.
(Version 15.2 - Integrated with advanced categorizer)
"""
# 🎯 1. IMPORT: เพิ่มบรรทัดนี้เพื่อเรียกใช้ฟังก์ชันจัดกลุ่มแบบใหม่
from .keyword_categorizer import categorize_keywords

# 🎯 2. REMOVE: ลบฟังก์ชัน categorize_keywords ของเก่าที่เคยอยู่ตรงนี้ทิ้งไป
# def categorize_keywords(keywords):
#     """Categorizes a list of keywords based on their names."""
#     ... (โค้ดเก่าทั้งหมดถูกลบ) ...

def _format_step_for_script(step):
    """Formats a single step dictionary into a Robot Framework string line."""
    keyword = step.get('keyword', '')
    args = step.get('args', {})
    
    args_list = []
    for arg_name, arg_value in args.items():
        if arg_value:
            is_locator = any(s in arg_name.lower() for s in ['locator', 'field', 'button', 'element'])
            if is_locator and not str(arg_value).startswith('${'):
                formatted_value = f"${{{arg_value}}}"
            else:
                formatted_value = str(arg_value)
            args_list.append(formatted_value)
            
    return f"{keyword}    {'    '.join(args_list)}".strip()

def generate_robot_script_from_timeline(ws_state):
    """
    Generates a complete Robot Framework script from the timeline state.
    """
    settings_lines = ["*** Settings ***"]
    if ws_state.get('keywords'):
        settings_lines.append("Resource    ../resources/commonkeywords.resource") # Example path
    
    setup_steps = ws_state.get('suite_setup', [])
    test_steps = ws_state.get('timeline', [])
    teardown_steps = ws_state.get('suite_teardown', [])

    if setup_steps:
        scope = ws_state.get('suite_setup_scope', 'Suite')
        setup_keyword = f"{scope} Setup"
        if len(setup_steps) == 1:
            settings_lines.append(f"{setup_keyword}    {_format_step_for_script(setup_steps[0])}")
        else:
            setup_run_keywords = [f"{setup_keyword}    Run Keywords"]
            for i, step in enumerate(setup_steps):
                prefix = "..." if i == 0 else "...    AND"
                setup_run_keywords.append(f"    {prefix}    {_format_step_for_script(step)}")
            settings_lines.extend(setup_run_keywords)

    if teardown_steps:
        scope = ws_state.get('suite_teardown_scope', 'Suite')
        teardown_keyword = f"{scope} Teardown"
        if len(teardown_steps) == 1:
            settings_lines.append(f"{teardown_keyword}    {_format_step_for_script(teardown_steps[0])}")
        else:
            teardown_run_keywords = [f"{teardown_keyword}    Run Keywords"]
            for i, step in enumerate(teardown_steps):
                prefix = "..." if i == 0 else "...    AND"
                teardown_run_keywords.append(f"    {prefix}    {_format_step_for_script(step)}")
            settings_lines.extend(teardown_run_keywords)

    used_locators = set()
    all_steps = setup_steps + test_steps + teardown_steps
    for step in all_steps:
        for arg_name, arg_value in step.get('args', {}).items():
            if any(s in arg_name.lower() for s in ['locator', 'field', 'button', 'element']) and arg_value:
                used_locators.add(arg_value)

    variables_lines = []
    if used_locators:
        variables_lines.append("\n*** Variables ***")
        all_locators_map = {loc['name']: loc['value'] for loc in ws_state.get('locators', [])}
        max_len = max(len(f"${{{name}}}") for name in used_locators) + 4 if used_locators else 0
        for name in sorted(list(used_locators)):
            value = all_locators_map.get(name, f"# Locator '{name}' not found in assets!")
            variables_lines.append(f"${{{name}}}".ljust(max_len) + value)

    test_cases_lines = ["\n*** Test Cases ***"]
    test_cases_lines.append("Generated Test Case")
    for step in test_steps:
        test_cases_lines.append(f"    {_format_step_for_script(step)}")

    full_script = "\n".join(settings_lines) + "\n" + "\n".join(variables_lines) + "\n" + "\n".join(test_cases_lines)
    
    return full_script