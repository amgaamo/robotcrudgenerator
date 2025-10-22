"""
HTML Parser for Robot Framework Locator Generation
Ported from JavaScript locator generator logic
"""

from bs4 import BeautifulSoup
import re
from typing import List, Set

class LocatorField:
    """Represents a single locator field"""
    def __init__(self, variable: str, xpath: str, priority: int = 5):
        self.variable = variable
        self.xpath = xpath
        self.priority = priority  # 1=highest, 5=lowest

class HTMLLocatorParser:
    """Parse HTML and extract locators with priority"""
    
    def __init__(self):
        self.found_identifiers: Set[str] = set()
    
    def is_id_descriptive(self, elem_id: str) -> bool:
        """
        Check if an ID is descriptive or just a generated one.
        Returns False if ID is like 'menu-1', 'sidebar-sub-menu-4', etc.
        """
        if not elem_id:
            return False
        
        # FIX: Regex to cover 'sidebar-sub-menu-10'
        if re.match(r'^(menu|sidebar|item|link|btn|elem|sub-menu).*[\-_]\d+$', elem_id, re.IGNORECASE):
            return False
        
        return True

    def get_menu_text(self, element) -> str:
        """
        Get clean text from a menu element, removing icons and other clutter.
        """
        if not element:
            return ''
            
        clone = BeautifulSoup(str(element), 'html.parser')
        
        for unwanted in clone.select('span[nz-icon], span.anticon, fa-stack, i.ti, svg'):
            unwanted.decompose()
            
        text = clone.get_text(strip=True)
        if text:
            return text
            
        return element.get_text(strip=True)

    def get_tag_suffix(self, xpath: str) -> str:
        """
        Get suffix based on element tag from xpath
        Returns appropriate suffix like _BTN, _INPUT, _SELECT, etc.
        """
        xpath_lower = xpath.lower()
        
        # Button elements
        if '//button' in xpath_lower or "[@type='button']" in xpath_lower or "[@type='submit']" in xpath_lower:
            return '_BTN'
        
        # Input elements
        elif '//input' in xpath_lower:
            if "[@type='checkbox']" in xpath_lower:
                return '_CHECKBOX'
            elif "[@type='radio']" in xpath_lower:
                return '_RADIO'
            elif "[@type='file']" in xpath_lower:
                return '_FILE'
            else:
                return '_INPUT'
        
        # Select elements
        elif '//select' in xpath_lower or '//nz-select' in xpath_lower:
            return '_SELECT'
        
        # Date picker
        elif '//nz-date-picker' in xpath_lower:
            return '_DATE'
        
        # Textarea
        elif '//textarea' in xpath_lower:
            return '_TEXTAREA'
        
        # Link/Anchor
        elif '//a' in xpath_lower:
            return '_LINK'

        # --- REMOVED MENU LOGIC ---
        # Menu logic is now handled in the extractor functions themselves
        
        # Table elements
        elif '//table' in xpath_lower:
            if '//thead' in xpath_lower or '/thead' in xpath_lower:
                return '_THEAD'
            elif '//tbody' in xpath_lower or '/tbody' in xpath_lower:
                return '_TBODY'
            else:
                return '_TABLE'
        
        # Label elements
        elif '//label' in xpath_lower:
            return '_LABEL'
        
        # Common containers
        elif '//span' in xpath_lower:
            return '_SPAN'
        elif '//div' in xpath_lower:
            return '_DIV'
        elif '//p' in xpath_lower:
            return '_TEXT'
        
        # Default: no suffix
        return ''
    
    def create_variable_name(self, text: str, is_technical_source: bool = False) -> str:
        """
        Create Robot Framework variable name from text.
        """
        if not text:
            return ''
        
        clean_text = re.sub(r'([a-z])([A-Z])', r'\1_\2', text)
        clean_text = re.sub(r'\s*\*?[:]?$', '', clean_text)
        clean_text = re.sub(r'[/()]', ' ', clean_text).strip()

        if is_technical_source or re.search(r'[a-zA-Z]', clean_text):
            clean_text = clean_text.upper()
        
        clean_text = re.sub(r'[^\u0E00-\u0E7Fa-zA-Z0-9\s\-_]', '', clean_text)
        clean_text = re.sub(r'[\s\-]+', '_', clean_text)
        clean_text = re.sub(r'_{2,}', '_', clean_text)
        clean_text = clean_text.strip('_')
        
        return clean_text
    
    def get_prioritized_label_text(self, label_element) -> str:
        """
        Extract clean text from a label element, removing hints and other clutter.
        """
        if not label_element:
            return ''
        
        label_clone = BeautifulSoup(str(label_element), 'html.parser')
        
        for unwanted in label_clone.select('.form-label-small, .required-asterisk, i, strong.text-danger, br'):
            unwanted.decompose()
        
        main_text = label_clone.get_text(strip=True)
        return main_text if main_text else label_element.get_text(strip=True)
    
    def extract_form_fields(self, soup: BeautifulSoup) -> List[LocatorField]:
        """
        Extract form input fields (input, select, textarea) with XPath locators.
        """
        fields = []
        container_selectors = [
            'nz-form-item', 'div.form-item', 'div.form-group',
            'div.ant-row', 'div.detail-form', 'div.info-item'
        ]
        
        containers = soup.select(', '.join(container_selectors))
        
        for container in containers:
            controls = container.select('input, select, textarea, nz-select, nz-date-picker')
            
            for control in controls:
                tag_name = control.name.lower()
                elem_id = control.get('id', '').strip()
                name = control.get('name', '').strip()
                form_control_name = control.get('formcontrolname', '').strip()
                placeholder = control.get('placeholder', '').strip()
                
                control_classes = ' '.join(control.get('class', []))
                if 'ant-select-selection-search-input' in control_classes or control.get('type') == 'file':
                    continue
                
                xpath, name_source_text, is_technical_source, priority = '', '', False, 5
                
                is_desc_id = self.is_id_descriptive(elem_id)
                id_count = len(soup.select(f'{tag_name}[id="{elem_id}"]')) if elem_id else 0
                name_count = len(soup.select(f'{tag_name}[name="{name}"]')) if name else 0
                
                if elem_id and is_desc_id and id_count == 1:
                    xpath, name_source_text, is_technical_source, priority = f'//{tag_name}[@id="{elem_id}"]', elem_id, True, 1
                elif name and name_count == 1:
                    xpath, name_source_text, is_technical_source, priority = f'//{tag_name}[@name="{name}"]', name, True, 2
                elif elem_id and is_desc_id and id_count > 1 and placeholder:
                     xpath, name_source_text, is_technical_source, priority = f'//{tag_name}[@id="{elem_id}" and @placeholder="{placeholder}"]', f'{elem_id}_{placeholder}', True, 3
                elif form_control_name:
                    xpath, name_source_text, is_technical_source, priority = f'//{tag_name}[@formcontrolname="{form_control_name}"]', form_control_name, True, 4
                else:
                    label = container.select_one('label') or container.find_previous_sibling('label')
                    if label:
                        label_text = self.get_prioritized_label_text(label)
                        if label_text:
                            xpath, name_source_text, priority = f"//label[normalize-space()='{label_text}']/ancestor::nz-form-item//{tag_name}", label_text, 5
                
                if not xpath and elem_id and id_count == 1: # Fallback to non-descriptive ID
                    xpath, name_source_text, is_technical_source, priority = f'//{tag_name}[@id="{elem_id}"]', elem_id, True, 6 
                
                if xpath:
                    variable_name = self.create_variable_name(name_source_text, is_technical_source)
                    variable_name = variable_name + self.get_tag_suffix(xpath)
                    
                    if variable_name and variable_name not in self.found_identifiers:
                        fields.append(LocatorField(variable_name, xpath, priority))
                        self.found_identifiers.add(variable_name)
        
        return fields

    def extract_upload_fields(self, soup: BeautifulSoup) -> List[LocatorField]:
        """
        Extract file upload input fields, often found in custom components like 'upload-section'.
        """
        fields = []
        upload_containers = soup.select('div.upload-section')
        
        for container in upload_containers:
            file_input = container.select_one('input[type="file"]')
            if not file_input:
                continue

            elem_id = file_input.get('id')
            if not elem_id:
                continue

            xpath = f"//input[@id='{elem_id}']"
            priority = 1

            name_source_text = ''
            text_element = container.select_one('div.line1 span, div.line1')
            if text_element:
                name_source_text = self.get_prioritized_label_text(text_element)
            
            if not name_source_text:
                name_source_text = elem_id
            
            variable_name = self.create_variable_name(name_source_text)
            variable_name = variable_name + self.get_tag_suffix(xpath)
            
            if variable_name and variable_name not in self.found_identifiers:
                fields.append(LocatorField(variable_name, xpath, priority))
                self.found_identifiers.add(variable_name)
        
        return fields
    
    def extract_display_fields(self, soup: BeautifulSoup) -> List[LocatorField]:
        """
        Extract display/readonly fields, excluding table headers.
        """
        fields = []
        display_selectors = ['div.info-label', 'div.typo-body-lg-bold', 'p.info-label-total-value']
        
        labels = soup.select(', '.join(display_selectors))
        
        for label in labels:
            label_text = label.get_text(strip=True)
            variable_name = self.create_variable_name(label_text)
            
            if not label_text or variable_name in self.found_identifiers:
                continue
            
            value_xpath = ''
            value_sibling = label.find_next_sibling()
            
            if value_sibling:
                value_tag = value_sibling.name
                value_xpath = f'//{label.name}[normalize-space()="{label_text}"]/following-sibling::{value_tag}[1]'
            
            if value_xpath:
                variable_name_with_suffix = variable_name + self.get_tag_suffix(value_xpath)
                if variable_name_with_suffix not in self.found_identifiers:
                    fields.append(LocatorField(variable_name_with_suffix, value_xpath, priority=6))
                    self.found_identifiers.add(variable_name_with_suffix)
        
        return fields
    
    def extract_buttons(self, soup: BeautifulSoup) -> List[LocatorField]:
        """
        Extract button locators with robust text extraction logic.
        """
        fields = []
        buttons = soup.select('button')
        
        for button in buttons:
            button_text = self.get_menu_text(button) 
            variable_name = self.create_variable_name(button_text, is_technical_source=True)
            
            if not variable_name or len(button_text) <= 1 or variable_name in self.found_identifiers:
                continue
            
            elem_id, name = button.get('id', ''), button.get('name', '')
            is_desc_id = self.is_id_descriptive(elem_id)
            
            if elem_id and is_desc_id:
                xpath, priority = f"//button[@id='{elem_id}']", 1
            elif name:
                xpath, priority = f"//button[@name='{name}']", 2
            else:
                xpath, priority = f"//button[normalize-space()='{button_text}']", 3 
            
            if not xpath: 
                 if elem_id:
                     xpath, priority = f"//button[@id='{elem_id}']", 4
                 
            variable_name = variable_name + self.get_tag_suffix(xpath)
            
            if variable_name not in self.found_identifiers:
                fields.append(LocatorField(variable_name, xpath, priority))
                self.found_identifiers.add(variable_name)
        
        return fields

    def extract_tables(self, soup: BeautifulSoup) -> List[LocatorField]:
        """
        Extract table, thead, and tbody locators, prioritizing XPath by ID > Class > Index.
        """
        fields = []
        tables = soup.find_all('table')
        table_index = 1

        for table in tables:
            base_name, table_xpath = '', ''
            
            prev_header = table.find_previous(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if prev_header:
                base_name = self.create_variable_name(prev_header.get_text(strip=True)) + "_TABLE"
            elif table.get('id') and self.is_id_descriptive(table.get('id')):
                base_name = self.create_variable_name(table.get('id'), is_technical_source=True)
            else:
                base_name = f"TABLE_{table_index}"

            table_id = table.get('id')
            table_classes = table.get('class', [])
            significant_classes = ['ant-table-fixed', 'table-bordered', 'dataTable', 'table']
            found_class = next((cls for cls in significant_classes if cls in table_classes), None)

            if table_id and self.is_id_descriptive(table_id):
                table_xpath = f"//table[@id='{table_id}']"
            elif found_class:
                table_xpath = f"//table[contains(@class, '{found_class}')]"
            elif table_id: # Fallback to non-descriptive ID
                 table_xpath = f"//table[@id='{table_id}']"
            else:
                table_xpath = f"(//table)[{table_index}]"
            
            priority = 4

            if base_name and base_name not in self.found_identifiers:
                fields.append(LocatorField(base_name, table_xpath, priority))
                self.found_identifiers.add(base_name)
                
                if table.find('thead'):
                    thead_xpath = f"{table_xpath}/thead"
                    # --- FIX: Changed from _HEADER ---
                    thead_var = f"{base_name}_THEAD"
                    if thead_var not in self.found_identifiers:
                        fields.append(LocatorField(thead_var, thead_xpath, priority))
                        self.found_identifiers.add(thead_var)

                if table.find('tbody'):
                    tbody_xpath = f"{table_xpath}/tbody"
                    # --- FIX: Changed from _BODY ---
                    tbody_var = f"{base_name}_TBODY"
                    if tbody_var not in self.found_identifiers:
                        fields.append(LocatorField(tbody_var, tbody_xpath, priority))
                        self.found_identifiers.add(tbody_var)

            table_index += 1
            
        return fields

    def extract_menu_links(self, soup: BeautifulSoup) -> List[LocatorField]:
        """
        Extract menu <a> tags (sidebar-link, nav-link)
        Per user request, ALL links found by this function are considered menus
        and will receive the _MENU suffix.
        """
        fields = []
        links = soup.select('a.sidebar-link, a.nav-link') 

        for link in links:
            elem_id = link.get('id', '').strip()
            title = link.get('title', '').strip()
            
            menu_text_span = link.select_one('span.hide-menu')
            menu_text = menu_text_span.get_text(strip=True) if menu_text_span else ''

            if not menu_text: 
                menu_text = self.get_menu_text(link)

            if not menu_text and title:
                menu_text = title
            
            is_desc_id = self.is_id_descriptive(elem_id)
            has_text = bool(menu_text)
            has_unique_title = title and len(soup.select(f"a[title='{title}']")) == 1
            
            # --- CHANGE: is_menu logic removed, as all items here are considered _MENU ---
            # is_menu = 'has-arrow' in link.get('class', []) 
            
            xpath, priority, name_source_text, is_technical_source = '', 5, '', False

            if is_desc_id:
                xpath, priority = f"//a[@id='{elem_id}']", 1
                name_source_text = menu_text if has_text else elem_id
                is_technical_source = not has_text
            
            elif has_unique_title:
                xpath, priority = f"//a[@title='{title}']", 2
                name_source_text = title 
            
            elif has_text:
                if menu_text_span:
                    xpath, priority = f"//a[.//span[normalize-space()='{menu_text}']]", 3
                else:
                    xpath, priority = f"//a[normalize-space()='{menu_text}']", 3
                name_source_text = menu_text
            
            elif elem_id: # Fallback: ID ไม่สื่อความหมาย
                xpath, priority = f"//a[@id='{elem_id}']", 4
                name_source_text = menu_text if has_text else elem_id
                is_technical_source = not has_text

            if not xpath or not name_source_text:
                continue
                
            variable_name = self.create_variable_name(name_source_text, is_technical_source)
            
            # --- CHANGE: Hardcoded suffix to _MENU as requested ---
            suffix = '_MENU' # Was: '_MENU' if is_menu else '_LINK'
            variable_name = variable_name + suffix
            
            if variable_name and variable_name not in self.found_identifiers:
                fields.append(LocatorField(variable_name, xpath, priority))
                self.found_identifiers.add(variable_name)

        return fields

    def extract_ant_menu_items(self, soup: BeautifulSoup) -> List[LocatorField]:
        """
        Extract Ant Design (ant-menu) <li> items.
        These are direct navigation links.
        --- CHANGE: Per user request, these are now considered _MENU ---
        """
        fields = []
        menu_items = soup.select('li.ant-menu-item')

        for item in menu_items:
            if item.select_one('a.nav-link'):
                # This <li> is just a wrapper for an <a> tag
                # which is already handled by extract_menu_links.
                continue
                
            router_link = item.get('routerlink', '').strip()
            # Use get_menu_text to get clean text, e.g., "Name Screening"
            menu_text = self.get_menu_text(item) 
            
            has_text = bool(menu_text)
            has_router_link = bool(router_link)
            
            xpath, priority, name_source_text, is_technical_source = '', 5, '', False

            if has_router_link:
                xpath, priority = f"//li[@routerlink='{router_link}']", 1
                name_source_text = menu_text if has_text else router_link
                is_technical_source = not has_text
            
            elif has_text:
                # Find <li> that is a menu item and contains the specific clean text
                xpath = f"//li[contains(@class, 'ant-menu-item') and normalize-space(.)='{menu_text}']"
                priority = 3
                name_source_text = menu_text
            
            if not xpath or not name_source_text:
                continue
                
            variable_name = self.create_variable_name(name_source_text, is_technical_source)
            
            # --- THIS IS THE FIX ---
            # Changed from '_LINK' to '_MENU'
            variable_name = variable_name + '_MENU' 
            
            if variable_name and variable_name not in self.found_identifiers:
                fields.append(LocatorField(variable_name, xpath, priority))
                self.found_identifiers.add(variable_name)

        return fields

    def extract_ant_submenu_titles(self, soup: BeautifulSoup) -> List[LocatorField]:
        """
        Extract Ant Design (ant-menu) <div> titles for collapsible submenus.
        These are expandable menus, so they get _MENU.
        """
        fields = []
        submenu_titles = soup.select('li.ant-menu-submenu > div.ant-menu-submenu-title')

        for title_div in submenu_titles:
            menu_text = self.get_menu_text(title_div)
            
            if not menu_text:
                continue
            
            xpath = f"//li[contains(@class, 'ant-menu-submenu')][.//span[normalize-space()='{menu_text}']] /div[contains(@class, 'ant-menu-submenu-title')]"
            
            priority = 3
            variable_name = self.create_variable_name(menu_text)
            # --- CHANGE: Hardcode suffix to _MENU ---
            variable_name = variable_name + '_MENU'
            
            if variable_name and variable_name not in self.found_identifiers:
                fields.append(LocatorField(variable_name, xpath, priority))
                self.found_identifiers.add(variable_name)
                
        return fields

    def extract_first_row_actions(self, soup: BeautifulSoup) -> List[LocatorField]:
        """
        Extract action buttons (a, button) from the *first row* of the *first*
        data table (tbody) on the page.
        """
        fields = []
        # ค้นหา tbody แรกในหน้า
        first_tbody = soup.select_one('table tbody')
        if not first_tbody:
            return []
        
        # ค้นหาแถวแรก (tr) ใน tbody นั้น
        first_row = first_tbody.select_one('tr:first-child, tr:nth-child(1)')
        if not first_row:
            return []

        # ค้นหา <a> หรือ <button> ที่มี attribute 'title' หรือ 'nz-tooltip'
        actions = first_row.select('a[title], button[title], a[nz-tooltip], button[nz-tooltip]')

        for action in actions:
            title = (action.get('title') or action.get('nz-tooltip', '')).strip()
            if not title:
                continue
            
            tag_name = action.name.lower()
            
            # ตรวจสอบว่าปุ่มนี้ใช้ attribute ไหน (title หรือ nz-tooltip)
            attr_name = 'title' if action.get('title') else 'nz-tooltip'
            
            # สร้าง XPath ที่เจาะจงไปยัง แถวแรก ของ tbody แรก
            xpath = f"(//tbody)[1]/tr[1]//{tag_name}[@{attr_name}='{title}']"
            
            variable_name = self.create_variable_name(title)
            
            # กำหนด Suffix เอง (ง่ายกว่า)
            if tag_name == 'button':
                suffix = '_BTN'
            else: # tag_name == 'a'
                suffix = '_LINK' 
                
            variable_name += suffix
            
            if variable_name and variable_name not in self.found_identifiers:
                # ให้ Priority สูง (3)
                fields.append(LocatorField(variable_name, xpath, priority=3))
                self.found_identifiers.add(variable_name)
                
        return fields

    def parse_html(self, html_content: str) -> List[LocatorField]:
        """
        Main parsing function to extract all locators from HTML.
        """
        self.found_identifiers.clear()
        soup = BeautifulSoup(html_content, 'html.parser')
        
        all_fields = (
            self.extract_form_fields(soup) +
            self.extract_upload_fields(soup) +
            self.extract_display_fields(soup) +
            self.extract_buttons(soup) +
            self.extract_tables(soup) +
            self.extract_menu_links(soup) +
            self.extract_ant_menu_items(soup) +
            self.extract_ant_submenu_titles(soup) +
            self.extract_first_row_actions(soup)  # <--- เพิ่มฟังก์ชันใหม่
        )
        
        all_fields.sort(key=lambda f: f.priority)
        return all_fields

def generate_robot_framework_variables(fields: List[LocatorField], source_info: str = '') -> str:
    """
    Generate a formatted Robot Framework variables section string.
    """
    if not fields:
        return ''
    
    max_length = 0
    for field in fields:
        var_name = f'${{LOCATOR_{field.variable}}}'
        if len(var_name) > max_length:
            max_length = len(var_name)
    
    final_padding = max_length + 4
    
    lines = [
        '*** Variables ***',
        f'# Generated from: {source_info}',
        f'# Total Locators: {len(fields)}',
        ''
    ]
    
    for field in fields:
        var_name = f'${{LOCATOR_{field.variable}}}'
        line = var_name.ljust(final_padding) + field.xpath
        lines.append(line)
    
    return '\n'.join(lines)

# Example usage
if __name__ == '__main__':
    # --- ใส่ HTML ของคุณที่นี่เพื่อทดสอบ (ตัวอย่าง Sidebar-item) ---
    html_content = """
    <div _ngcontent-ng-c1458965376="" class="simplebar-content"><ul _ngcontent-ng-c1458965376="" id="sidebarnav"><li _ngcontent-ng-c1458965376="" class="sidebar-item"><a _ngcontent-ng-c1458965376="" target="_self" aria-expanded="false" class="sidebar-link has-arrow active" title="Configuration" href="#/mainmenu/companytype"><span _ngcontent-ng-c1458965376="" class="d-flex"><i _ngcontent-ng-c1458965376="" class="fa-cogs ti"></i></span><span _ngcontent-ng-c1458965376="" class="hide-menu">Configuration</span></a><ul _ngcontent-ng-c1458965376="" aria-expanded="false" class="collapse first-level in"><li _ngcontent-ng-c1458965376="" class="sidebar-item"><a _ngcontent-ng-c1458965376="" class="sidebar-link active" title="Company Type Management" id="sidebar-sub-menu-10" href="#/mainmenu/companytype"><div _ngcontent-ng-c1458965376="" class="round-16 d-flex align-items-center justify-content-center"><i _ngcontent-ng-c1458965376="" class="ti"></i></div><span _ngcontent-ng-c1458965376="" class="hide-menu text-wrap">Company Type Management</span></a></li><li _ngcontent-ng-c1458965376="" class="sidebar-item"><a _ngcontent-ng-c1458965376="" class="sidebar-link" title="Company Management" id="sidebar-sub-menu-4" href="#/mainmenu/company"><div _ngcontent-ng-c1458965376="" class="round-16 d-flex align-items-center justify-content-center"><i _ngcontent-ng-c1458965376="" class="ti"></i></div><span _ngcontent-ng-c1458965376="" class="hide-menu text-wrap">Company Management</span></a></li><li _ngcontent-ng-c1458965376="" class="sidebar-item"><a _ngcontent-ng-c1458965376="" class="sidebar-link" title="Group Management" id="sidebar-sub-menu-3" href="#/mainmenu/group"><div _ngcontent-ng-c1458965376="" class="round-16 d-flex align-items-center justify-content-center"><i _ngcontent-ng-c1458965376="" class="ti"></i></div><span _ngcontent-ng-c1458965376="" class="hide-menu text-wrap">Group Management</span></a></li><li _ngcontent-ng-c1458965376="" class.sidebar-item"><a _ngcontent-ng-c1458965376="" class="sidebar-link" title="User Management" id="sidebar-sub-menu-2" href="#/mainmenu/user"><div _ngcontent-ng-c1458965376="" class="round-16 d-flex align-items-center justify-content-center"><i _ngcontent-ng-c1458965376="" class="ti"></i></div><span _ngcontent-ng-c1type_management-menu text-wrap">User Management</span></a></li><li _ngcontent-ng-c1458965376="" class="sidebar-item"><a _ngcontent-ng-c1458965376="" class="sidebar-link" title="Role Management" id="sidebar-sub-menu-5" href="#/mainmenu/role"><div _ngcontent-ng-c1458965376="" class="round-16 d-flex align-items-center justify-content-center"><i _ngcontent-ng-c1458965376="" class="ti"></i></div><span _ngcontent-ng-c1458965376="" class="hide-menu text-wrap">Role Management</span></a></li><li _ngcontent-ng-c1458965376="" class="sidebar-item"><a _ngcontent-ng-c1458965376="" class="sidebar-link" title="Permission Management" id="sidebar-sub-menu-6" href="#/mainmenu/permission"><div _ngcontent-ng-c1458965376="" class="round-16 d-flex align-items-center justify-content-center"><i _ngcontent-ng-c1458965376="" class="ti"></i></div><span _ngcontent-ng-c1458965376="" class="hide-menu text-wrap">Permission Management</span></a></li><li _ngcontent-ng-c1458965376="" class="sidebar-item"><a _ngcontent-ng-c1458965376="" class="sidebar-link" title="Menu Management" id="sidebar-sub-menu-7" href="#/mainmenu/menu"><div _ngcontent-ng-c1458965376="" class="round-16 d-flex align-items-center justify-content-center"><i _ngcontent-ng-c1458965376="" class="ti"></i></div><span _ngcontent-ng-c1458965376="" class="hide-menu text-wrap">Menu Management</span></a></li></ul></li><li _ngcontent-ng-c1458965376="" class="sidebar-item"><a _ngcontent-ng-c1458965376="" target="_self" aria-expanded="false" class="sidebar-link" title="Register Management" id="sidebar-menu-8" href="#/mainmenu/register/approve"><span _ngcontent-ng-c1458965376=""><i _ngcontent-ng-c1A458965376="" class="fa-registered ti"></i></span><span _ngcontent-ng-c1458965376="" class.hide-menu">Register Management</span></a></li></ul></div>
    
    <table>
        <thead>...</thead>
        <tbody>
            <tr>
                <td>Data 1-1</td>
                <td>Data 1-2</td>
                <td>
                    <a href="#" title="Edit">Edit</a>
                    <button nz-tooltip="Delete">Delete</button>
                </td>
            </tr>
            <tr>
                <td>Data 2-1</td>
                <td>Data 2-2</td>
                <td>
                    <a href="#" title="Edit">Edit</a>
                    <button nz-tooltip="Delete">Delete</button>
                </td>
            </tr>
        </tbody>
    </table>
    """
    # -------------------------------------

    if html_content:
        parser = HTMLLocatorParser()
        fields = parser.parse_html(html_content)
        
        print(f'\n--- Running with ALL fixes ---')
        print(f'Found {len(fields)} locators:')
        for field in fields:
            print(f'  Priority {field.priority}: ${{LOCATOR_{field.variable}}} -> {field.xpath}')
        
        print('\n' + generate_robot_framework_variables(fields, 'Test All Fixes'))