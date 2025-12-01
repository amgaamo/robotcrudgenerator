"""
Checkbox Keywords Generator - Browser Library Version
สำหรับ auto-generate checkbox template และ keyword ใช้ Browser library
รองรับหลาย pattern: Standard HTML, Ant Design, Material UI, Bootstrap, etc.
"""

import re
from bs4 import BeautifulSoup


def generate_checkbox_template_and_keyword(page_name, xpath_pattern):
    """
    Generate checkbox template locator and keyword using Browser library
    
    Args:
        page_name: Name of the page (e.g., "RoleManagement")
        xpath_pattern: XPath pattern with ::labelcheckbox:: placeholder
    
    Returns:
        dict with 'variables' and 'keywords' sections
    """
    # Clean page name - remove spaces, keep as is (already PascalCase)
    clean_name = page_name.strip().replace(' ', '')
    
    # Variable name
    var_name = f"LOCATOR_{clean_name.upper()}_CHECKBOX"
    
    # Keyword name
    keyword_name = f"Set {clean_name} Checkbox"
    
    # Generate variables section
    variables = f"""*** Variables ***
# Checkbox Template - Page: {clean_name}
${{{var_name}}}    {xpath_pattern}
"""
    
    # Generate keywords section  
    keywords = f"""*** Keywords ***
{keyword_name}  
    [Arguments]    ${{label}}    ${{action}}
    
    # Replace ::labelcheckbox:: with actual label
    ${{xpath}}=    Replace String    ${{{var_name}}}    ::labelcheckbox::    ${{label}}
    
    Wait For Elements State    ${{xpath}}    visible    timeout=10s
    ${{is_checked}}=    Get Checkbox State    ${{xpath}}
    
    IF    '${{action}}' == 'checked'
        IF    not ${{is_checked}}
            Check Checkbox    ${{xpath}}
        END
    ELSE IF    '${{action}}' == 'unchecked'
        IF    ${{is_checked}}
            Uncheck Checkbox    ${{xpath}}
        END
    ELSE IF    '${{action}}' == 'click'
        Click    ${{xpath}}
    ELSE
        Fail    Invalid action: ${{action}}. Use: checked, unchecked, or click
    END
    
    Sleep    0.2s
"""
    
    return {
        'variables': variables,
        'keywords': keywords
    }


def filter_checkbox_locators(all_locators):
    """
    Filter out checkbox locators from all locators
    
    Args:
        all_locators: List of all locators
    
    Returns:
        List of checkbox locators only
    """
    return [
        loc for loc in all_locators 
        if '_CHECKBOX' in loc.get('name', '').upper()
    ]


def separate_locators(all_locators):
    """
    Separate normal locators and checkbox locators
    
    Args:
        all_locators: List of all locators
    
    Returns:
        tuple: (normal_locators, checkbox_locators)
    """
    normal = []
    checkbox = []
    
    for loc in all_locators:
        if '_CHECKBOX' in loc.get('name', '').upper():
            checkbox.append(loc)
        else:
            normal.append(loc)
    
    return normal, checkbox


def detect_page_name_from_html(html_content):
    """
    Auto-detect page name from HTML
    
    Priority:
    1. <title> tag
    2. <h1> tag  
    3. data-page attribute
    4. <form> id/name
    5. Fallback: "Page"
    
    Args:
        html_content: HTML string
    
    Returns:
        Detected page name (PascalCase)
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Strategy 1: Title tag
    title = soup.find('title')
    if title and title.text.strip():
        return clean_page_name(title.text.strip())
    
    # Strategy 2: First h1
    h1 = soup.find('h1')
    if h1 and h1.text.strip():
        return clean_page_name(h1.text.strip())
    
    # Strategy 3: data-page attribute
    page_elem = soup.find(attrs={'data-page': True})
    if page_elem:
        return clean_page_name(page_elem['data-page'])
    
    # Strategy 4: form name/id
    form = soup.find('form')
    if form:
        form_id = form.get('id', '') or form.get('name', '')
        if form_id:
            return clean_page_name(form_id)
    
    # Fallback
    return "Page"


def clean_page_name(text):
    """
    Clean and format page name to PascalCase
    
    Examples:
        "Role Management - Admin" → "RoleManagement"
        "user-management-page" → "UserManagement"
        "Create New Role" → "CreateNewRole"
    
    Args:
        text: Raw page name
    
    Returns:
        Cleaned PascalCase name
    """
    # Remove common suffixes/words
    text = re.sub(r'\s*[-|–]\s*.*$', '', text)  # Remove after dash
    text = re.sub(r'\b(page|screen|form|admin|management)\b', '', text, flags=re.I)
    
    # Remove special chars except spaces and alphanumeric
    text = re.sub(r'[^\w\s]', ' ', text)
    
    # Split and capitalize each word
    words = text.strip().split()
    pascal_case = ''.join(word.capitalize() for word in words if word)
    
    # If empty, return default
    return pascal_case if pascal_case else "Page"


def analyze_checkbox_structure(html_content):
    """
    Analyze HTML to determine best XPath pattern for checkboxes
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    checkboxes = soup.select('input[type="checkbox"]')
    
    if not checkboxes:
        return {
            'pattern': "//label[contains(normalize-space(), '::labelcheckbox::')]/preceding-sibling::input[@type='checkbox']",
            'description': 'Default: Label after checkbox',
            'framework': 'standard'
        }
    
    # Framework detection
    framework_scores = {
        'ant_design': 0,
        'material_ui': 0,
        'bootstrap': 0,
        'standard': 0
    }
    
    for checkbox in checkboxes:
        # Check Ant Design
        ant_parent = checkbox.find_parent('div', class_=lambda x: x and 'ant-checkbox-wrapper' in x)
        if ant_parent:
            framework_scores['ant_design'] += 1
            continue
        
        # Check Material UI
        mui_parent = checkbox.find_parent(class_=lambda x: x and ('MuiCheckbox' in str(x) or 'Mui-checkbox' in str(x)))
        if mui_parent:
            framework_scores['material_ui'] += 1
            continue
        
        # ✅ Check Bootstrap - ปรับให้ดูทั้ง class และ structure
        checkbox_classes = checkbox.get('class', [])
        if isinstance(checkbox_classes, str):
            checkbox_classes = checkbox_classes.split()
        
        # Bootstrap: checkbox มี class "form-check-input" หรืออยู่ใน div.form-check
        if 'form-check-input' in checkbox_classes:
            framework_scores['bootstrap'] += 1
            continue
        
        bootstrap_parent = checkbox.find_parent('div', class_='form-check')
        if bootstrap_parent:
            framework_scores['bootstrap'] += 1
            continue
        
        # Standard HTML
        framework_scores['standard'] += 1
    
    # เลือก framework ที่มี score สูงสุด
    dominant_framework = max(framework_scores, key=framework_scores.get)
    
    if framework_scores[dominant_framework] == 0:
        dominant_framework = 'standard'
    
    # Ant Design
    if dominant_framework == 'ant_design':
        return {
            'pattern': "//div[contains(@class, 'ant-checkbox-wrapper') and .//span[normalize-space()='::labelcheckbox::']]//input[@type='checkbox']",
            'description': 'Ant Design: Checkbox wrapper with label in span',
            'framework': 'ant_design'
        }
    
    # Material UI
    if dominant_framework == 'material_ui':
        return {
            'pattern': "//label[.//span[normalize-space()='::labelcheckbox::']]/preceding-sibling::span//input[@type='checkbox'] | //label[.//span[normalize-space()='::labelcheckbox::']]//input[@type='checkbox']",
            'description': 'Material UI: MuiCheckbox with label',
            'framework': 'material_ui'
        }
    
    # Bootstrap
    if dominant_framework == 'bootstrap':
        # ✅ แก้ไข pattern ให้ใช้งานได้กับทั้ง 2 แบบ
        return {
            'pattern': "//input[@type='checkbox' and contains(@class, 'form-check-input')]/following-sibling::label[normalize-space()='::labelcheckbox::'] | //label[@for and normalize-space()='::labelcheckbox::' and contains(@class, 'form-label')]",
            'description': 'Bootstrap: form-check-input with label (supports both adjacent and linked)',
            'framework': 'bootstrap'
        }
    
    # Standard HTML - วิเคราะห์โครงสร้าง
    pattern_counts = {
        'preceding_sibling': 0,
        'following_sibling': 0,
        'parent': 0,
        'linked_by_for': 0  # ✅ เพิ่ม: label ที่ใช้ for attribute
    }
    
    for checkbox in checkboxes:
        # ข้าม checkbox ที่อยู่ใน framework อื่น
        if checkbox.find_parent('div', class_=lambda x: x and 'ant-checkbox-wrapper' in x):
            continue
        if checkbox.find_parent('div', class_='form-check'):
            continue
        
        checkbox_id = checkbox.get('id')
        
        # ✅ Check if label uses "for" attribute
        if checkbox_id:
            linked_label = soup.find('label', attrs={'for': checkbox_id})
            if linked_label:
                pattern_counts['linked_by_for'] += 1
                continue
        
        # Check if checkbox is in label
        if checkbox.find_parent('label'):
            pattern_counts['parent'] += 1
            continue
        
        # Check for label as next sibling
        next_elem = checkbox.next_sibling
        found_next = False
        while next_elem:
            if hasattr(next_elem, 'name') and next_elem.name == 'label':
                pattern_counts['following_sibling'] += 1
                found_next = True
                break
            next_elem = next_elem.next_sibling
            if next_elem and hasattr(next_elem, 'name'):
                break
        
        if found_next:
            continue
        
        # Check for label as previous sibling
        prev_elem = checkbox.previous_sibling
        while prev_elem:
            if hasattr(prev_elem, 'name') and prev_elem.name == 'label':
                pattern_counts['preceding_sibling'] += 1
                break
            prev_elem = prev_elem.previous_sibling
            if prev_elem and hasattr(prev_elem, 'name'):
                break
    
    # Choose most common pattern
    if sum(pattern_counts.values()) == 0:
        dominant = 'following_sibling'
    else:
        dominant = max(pattern_counts, key=pattern_counts.get)
    
    standard_patterns = {
        'linked_by_for': {
            'pattern': "//label[@for and normalize-space()='::labelcheckbox::']/@for | //input[@type='checkbox' and @id=//label[normalize-space()='::labelcheckbox::']/@for]",
            'description': 'Standard HTML: Label linked by "for" attribute',
            'framework': 'standard'
        },
        'parent': {
            'pattern': "//label[contains(normalize-space(), '::labelcheckbox::')]//input[@type='checkbox']",
            'description': 'Standard HTML: Checkbox inside label',
            'framework': 'standard'
        },
        'following_sibling': {
            'pattern': "//input[@type='checkbox']/following-sibling::label[normalize-space()='::labelcheckbox::']/..",
            'description': 'Standard HTML: Label after checkbox',
            'framework': 'standard'
        },
        'preceding_sibling': {
            'pattern': "//label[normalize-space()='::labelcheckbox::']/preceding-sibling::input[@type='checkbox']",
            'description': 'Standard HTML: Label before checkbox',
            'framework': 'standard'
        },
    }
    
    return standard_patterns.get(dominant, standard_patterns['following_sibling'])


def get_all_supported_patterns():
    """
    Get all supported checkbox patterns
    
    Returns:
        dict: All available patterns with descriptions
    """
    return {
        'ant_design': {
            'pattern': "//div[contains(@class, 'ant-checkbox-wrapper') and .//span[normalize-space()='::labelcheckbox::']]//input[@type='checkbox']",
            'description': 'Ant Design: Checkbox wrapper with label in span',
            'example': '<div class="ant-checkbox-wrapper"><span>Label</span></div>'
        },
        'material_ui': {
            'pattern': "//label[.//span[normalize-space()='::labelcheckbox::']]/preceding-sibling::span//input[@type='checkbox'] | //label[.//span[normalize-space()='::labelcheckbox::']]//input[@type='checkbox']",
            'description': 'Material UI: MuiCheckbox with label',
            'example': '<span class="MuiCheckbox"><input/></span><label><span>Label</span></label>'
        },
        'bootstrap': {
            'pattern': "//label[contains(@class, 'form-check-label') and normalize-space()='::labelcheckbox::']/preceding-sibling::input[@type='checkbox' and contains(@class, 'form-check-input')]",
            'description': 'Bootstrap: form-check pattern',
            'example': '<input class="form-check-input"/><label class="form-check-label">Label</label>'
        },
        'standard_parent': {
            'pattern': "//label[contains(normalize-space(), '::labelcheckbox::')]//input[@type='checkbox']",
            'description': 'Standard HTML: Checkbox inside label',
            'example': '<label>Label <input type="checkbox"/></label>'
        },
        'standard_preceding': {
            'pattern': "//label[contains(normalize-space(), '::labelcheckbox::')]/preceding-sibling::input[@type='checkbox']",
            'description': 'Standard HTML: Label after checkbox',
            'example': '<input type="checkbox"/><label>Label</label>'
        },
        'standard_following': {
            'pattern': "//label[contains(normalize-space(), '::labelcheckbox::')]/following-sibling::input[@type='checkbox']",
            'description': 'Standard HTML: Label before checkbox',
            'example': '<label>Label</label><input type="checkbox"/>'
        }
    }


def test_pattern_against_html(html_content, pattern):
    """
    Test if a pattern works against given HTML
    
    Args:
        html_content: HTML string
        pattern: XPath pattern to test
    
    Returns:
        bool: True if pattern finds checkboxes
    """
    try:
        from lxml import etree, html as lxml_html
        
        # Parse HTML
        doc = lxml_html.fromstring(html_content)
        
        # Test pattern with a dummy label
        test_pattern = pattern.replace('::labelcheckbox::', 'test')
        results = doc.xpath(test_pattern)
        
        return len(results) > 0
    except:
        return False


def get_best_pattern_with_fallback(html_content):
    """
    Get best pattern with multiple fallback options
    
    Args:
        html_content: HTML string
    
    Returns:
        dict with 'primary', 'fallbacks' and 'all_tested'
    """
    primary = analyze_checkbox_structure(html_content)
    all_patterns = get_all_supported_patterns()
    
    # Test all patterns
    tested_results = {}
    for name, pattern_info in all_patterns.items():
        works = test_pattern_against_html(html_content, pattern_info['pattern'])
        tested_results[name] = {
            **pattern_info,
            'works': works
        }
    
    # Get working fallbacks (exclude primary)
    fallbacks = [
        {
            'name': name,
            **info
        }
        for name, info in tested_results.items()
        if info['works'] and info['pattern'] != primary['pattern']
    ]
    
    return {
        'primary': primary,
        'fallbacks': fallbacks,
        'all_tested': tested_results
    }