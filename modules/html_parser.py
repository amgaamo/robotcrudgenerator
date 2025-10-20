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
        
        # Table elements
        elif '//table' in xpath_lower:
            if '//thead' in xpath_lower or '/thead' in xpath_lower:
                return '_THEADER'
            elif '//tbody' in xpath_lower or '/tbody' in xpath_lower:
                return '_TBODY'
            else:
                return '_TABLE'
        
        # Label elements
        elif '//label' in xpath_lower:
            return '_LABEL'
        
        # Common containers - only if they seem to be value containers
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
                
                id_count = len(soup.select(f'{tag_name}[id="{elem_id}"]')) if elem_id else 0
                name_count = len(soup.select(f'{tag_name}[name="{name}"]')) if name else 0
                
                if elem_id and id_count == 1:
                    xpath, name_source_text, is_technical_source, priority = f'//{tag_name}[@id="{elem_id}"]', elem_id, True, 1
                elif name and name_count == 1:
                    xpath, name_source_text, is_technical_source, priority = f'//{tag_name}[@name="{name}"]', name, True, 2
                elif elem_id and id_count > 1 and placeholder:
                    xpath, name_source_text, is_technical_source, priority = f'//{tag_name}[@id="{elem_id}" and @placeholder="{placeholder}"]', f'{elem_id}_{placeholder}', True, 3
                elif form_control_name:
                    xpath, name_source_text, is_technical_source, priority = f'//{tag_name}[@formcontrolname="{form_control_name}"]', form_control_name, True, 4
                else:
                    label = container.select_one('label') or container.find_previous_sibling('label')
                    if label:
                        label_text = self.get_prioritized_label_text(label)
                        if label_text:
                            xpath, name_source_text, priority = f"//label[normalize-space()='{label_text}']/ancestor::nz-form-item//{tag_name}", label_text, 5
                
                if xpath:
                    variable_name = self.create_variable_name(name_source_text, is_technical_source)
                    # เพิ่ม suffix ตาม tag type
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
        # ค้นหา container หลักของส่วนอัปโหลด
        upload_containers = soup.select('div.upload-section')
        
        for container in upload_containers:
            # ค้นหา input type="file" ที่อยู่ข้างใน
            file_input = container.select_one('input[type="file"]')
            if not file_input:
                continue

            # ใช้ id เป็น locator หลักเพราะมีความเสถียรสูงสุด
            elem_id = file_input.get('id')
            if not elem_id:
                continue

            xpath = f"//input[@id='{elem_id}']"
            priority = 1  # ให้ความสำคัญสูงสุด

            # พยายามหาข้อความที่สื่อความหมายที่สุดมาสร้างเป็นชื่อตัวแปร
            name_source_text = ''
            text_element = container.select_one('div.line1 span, div.line1')
            if text_element:
                # ใช้ฟังก์ชันเดิมในการตัดคำที่ไม่ต้องการออก เช่น *
                name_source_text = self.get_prioritized_label_text(text_element)
            
            # ถ้าหาข้อความไม่ได้จริงๆ ให้ใช้ id แทน
            if not name_source_text:
                name_source_text = elem_id
            
            variable_name = self.create_variable_name(name_source_text)
            # เพิ่ม suffix สำหรับ file upload
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
                # เพิ่ม suffix ตาม tag
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
            button_text = ''
            
            span = button.find('span')
            if span:
                span_text = ''.join(s for s in span.find_all(string=True, recursive=False)).strip()
                if span_text:
                    button_text = span_text

            if not button_text:
                direct_texts = [s.strip() for s in button.find_all(string=True, recursive=False)]
                direct_text = ' '.join(filter(None, direct_texts)).strip()
                if direct_text:
                    button_text = direct_text

            if not button_text:
                title = button.get('title')
                if title:
                    button_text = title.strip()
            
            if not button_text:
                button_text = button.get_text(strip=True)

            variable_name = self.create_variable_name(button_text, is_technical_source=True)
            
            if not variable_name or len(button_text) <= 1 or variable_name in self.found_identifiers:
                continue
            
            elem_id, name = button.get('id', ''), button.get('name', '')
            
            if elem_id:
                xpath, priority = f"//button[@id='{elem_id}']", 1
            elif name:
                xpath, priority = f"//button[@name='{name}']", 2
            else:
                xpath, priority = f"//button[contains(.,'{button_text}')]", 3
            
            # เพิ่ม _BTN suffix
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
            elif table.get('id'):
                base_name = self.create_variable_name(table.get('id'), is_technical_source=True)
            else:
                base_name = f"TABLE_{table_index}"

            table_id = table.get('id')
            table_classes = table.get('class', [])
            significant_classes = ['ant-table-fixed', 'table-bordered', 'dataTable', 'table']
            found_class = next((cls for cls in significant_classes if cls in table_classes), None)

            if table_id:
                table_xpath = f"//table[@id='{table_id}']"
            elif found_class:
                table_xpath = f"//table[contains(@class, '{found_class}')]"
            else:
                table_xpath = f"(//table)[{table_index}]"
            
            priority = 4

            if base_name and base_name not in self.found_identifiers:
                fields.append(LocatorField(base_name, table_xpath, priority))
                self.found_identifiers.add(base_name)
                
                if table.find('thead'):
                    thead_xpath = f"{table_xpath}/thead"
                    thead_var = f"{base_name}_HEADER"
                    if thead_var not in self.found_identifiers:
                        fields.append(LocatorField(thead_var, thead_xpath, priority))
                        self.found_identifiers.add(thead_var)

                if table.find('tbody'):
                    tbody_xpath = f"{table_xpath}/tbody"
                    tbody_var = f"{base_name}_BODY"
                    if tbody_var not in self.found_identifiers:
                        fields.append(LocatorField(tbody_var, tbody_xpath, priority))
                        self.found_identifiers.add(tbody_var)

            table_index += 1
            
        return fields

    def parse_html(self, html_content: str) -> List[LocatorField]:
        """
        Main parsing function to extract all locators from HTML.
        """
        self.found_identifiers.clear()
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Combine results from all extractor methods
        all_fields = (
            self.extract_form_fields(soup) +
            self.extract_upload_fields(soup) +
            self.extract_display_fields(soup) +
            self.extract_buttons(soup) +
            self.extract_tables(soup)
        )
        
        # Sort all found locators by their assigned priority
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
    html_file_path = 'D:\\NETbay\\gitproject\\frameworkproject-std-helper\\modules\\__htmlsample__.txt'

    html_content = ''
    try:
        with open(html_file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        print(f"✅ Successfully read HTML content from: {html_file_path}")

    except FileNotFoundError:
        print(f"❌ ERROR: File not found at the specified path: {html_file_path}")
        print("👉 Please update the 'html_file_path' variable with the correct path to your file.")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")

    if html_content:
        parser = HTMLLocatorParser()
        fields = parser.parse_html(html_content)
        
        print(f'\nFound {len(fields)} locators:')
        for field in fields:
            print(f'  Priority {field.priority}: ${{LOCATOR_{field.variable}}} -> {field.xpath}')
        
        print('\n' + generate_robot_framework_variables(fields, f'file: {html_file_path}'))