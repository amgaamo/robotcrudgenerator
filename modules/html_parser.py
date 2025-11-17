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
        
        # Regex to cover 'sidebar-sub-menu-10' etc.
        if re.match(r'^(menu|sidebar|item|link|btn|elem|sub-menu).*[\-_]\d+$',
                    elem_id, re.IGNORECASE):
            return False
        
        return True

    def get_menu_text(self, element) -> str:
        """
        Get clean text from a menu/button element, removing icons and other clutter.
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
        if '//button' in xpath_lower or "[@type='button']" in xpath_lower \
           or "[@type='submit']" in xpath_lower:
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
        
        # camelCase → camel_Case
        clean_text = re.sub(r'([a-z])([A-Z])', r'\1_\2', text)
        # ตัด * หรือ : ท้าย label
        clean_text = re.sub(r'\s*\*?[:]?$', '', clean_text)
        # / () → ช่องว่าง
        clean_text = re.sub(r'[/()]', ' ', clean_text).strip()

        # ถ้าเป็น id/name หรือมีตัวอักษรอังกฤษ → แปลงเป็น upper
        if is_technical_source or re.search(r'[a-zA-Z]', clean_text):
            clean_text = clean_text.upper()
        
        # เก็บ a-zA-Z, ตัวเลข, ไทย, space, -, _
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
        
        for unwanted in label_clone.select(
            '.form-label-small, .required-asterisk, i, strong.text-danger, br'
        ):
            unwanted.decompose()
        
        main_text = label_clone.get_text(strip=True)
        return main_text if main_text else label_element.get_text(strip=True)
    
    def extract_form_fields(self, soup: BeautifulSoup) -> List[LocatorField]:
        """
        Extract form input fields (input, select, textarea, nz-select, nz-date-picker) with XPath locators.
        - ข้าม checkbox, radio, file
        - กรณี nz-select: ถ้าใน component เดียวกันมี input ที่พิมพ์ได้ (ไม่ disabled)
          → ใช้ input แทน ไม่สร้าง nz-select ซ้ำ
        """
        fields: List[LocatorField] = []
        container_selectors = [
            'nz-form-item', 'div.form-item', 'div.form-group',
            'div.ant-row', 'div.detail-form', 'div.info-item'
        ]
        
        containers = soup.select(', '.join(container_selectors))
        
        for container in containers:
            # เตรียม mapping nz-select id -> มี input ให้พิมพ์
            selectable_ids: Set[str] = set()
            for nz_sel in container.select('nz-select[id]'):
                nz_id = nz_sel.get('id', '').strip()
                if not nz_id:
                    continue
                inner_input = nz_sel.select_one(
                    f'input[id="{nz_id}"]:not([disabled])'
                )
                if inner_input:
                    selectable_ids.add(nz_id)

            controls = container.select(
                'input, select, textarea, nz-select, nz-date-picker'
            )
            
            for control in controls:
                tag_name = control.name.lower()
                control_type = control.get('type', '').lower()

                # --- Filter out unwanted controls ---
                if control_type in ['checkbox', 'radio', 'file']:
                    continue

                # ถ้าเป็น nz-select และมี text input ใช้แทน → ข้าม nz-select
                if tag_name == 'nz-select':
                    elem_id = control.get('id', '').strip()
                    if elem_id and elem_id in selectable_ids:
                        continue  # เราจะใช้ input แทน
                # --- END filters ---

                elem_id = control.get('id', '').strip()
                name = control.get('name', '').strip()
                form_control_name = control.get('formcontrolname', '').strip()
                placeholder = control.get('placeholder', '').strip()
                
                xpath = ''
                name_source_text = ''
                is_technical_source = False
                priority = 5
                
                is_desc_id = self.is_id_descriptive(elem_id)
                id_count = len(soup.select(f'{tag_name}[id="{elem_id}"]')) \
                           if elem_id else 0
                name_count = len(soup.select(f'{tag_name}[name="{name}"]')) \
                             if name else 0
                
                if elem_id and is_desc_id and id_count == 1:
                    xpath = f'//{tag_name}[@id="{elem_id}"]'
                    name_source_text = elem_id
                    is_technical_source = True
                    priority = 1
                elif name and name_count == 1:
                    xpath = f'//{tag_name}[@name="{name}"]'
                    name_source_text = name
                    is_technical_source = True
                    priority = 2
                elif elem_id and is_desc_id and id_count > 1 and placeholder:
                    xpath = (
                        f'//{tag_name}[@id="{elem_id}" and '
                        f'@placeholder="{placeholder}"]'
                    )
                    name_source_text = f'{elem_id}_{placeholder}'
                    is_technical_source = True
                    priority = 3
                elif form_control_name:
                    xpath = f'//{tag_name}[@formcontrolname="{form_control_name}"]'
                    name_source_text = form_control_name
                    is_technical_source = True
                    priority = 4
                else:
                    label = (
                        container.select_one('label') or
                        container.find_previous_sibling('label')
                    )
                    if label:
                        label_text = self.get_prioritized_label_text(label)
                        if label_text:
                            xpath = (
                                f"//label[normalize-space()='{label_text}']"
                                f"/ancestor::nz-form-item//{tag_name}"
                            )
                            name_source_text = label_text
                            priority = 5
                
                # Fallback ใช้ id ที่ไม่ descriptive ถ้า unique
                if not xpath and elem_id and id_count == 1:
                    xpath = f'//{tag_name}[@id="{elem_id}"]'
                    name_source_text = elem_id
                    is_technical_source = True
                    priority = 6 
                
                if xpath:
                    variable_name = self.create_variable_name(
                        name_source_text, is_technical_source
                    )
                    variable_name = variable_name + self.get_tag_suffix(xpath)
                    
                    if variable_name and variable_name not in self.found_identifiers:
                        fields.append(LocatorField(variable_name, xpath, priority))
                        self.found_identifiers.add(variable_name)
        
        return fields

    def extract_upload_fields(self, soup: BeautifulSoup) -> List[LocatorField]:
        """
        Extract file upload input fields, often found in custom components like
        'upload-section'.
        """
        fields: List[LocatorField] = []
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
        fields: List[LocatorField] = []
        display_selectors = [
            'div.info-label', 'div.typo-body-lg-bold',
            'p.info-label-total-value'
        ]
        
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
                value_xpath = (
                    f'//{label.name}[normalize-space()="{label_text}"]'
                    f'/following-sibling::{value_tag}[1]'
                )
            
            if value_xpath:
                variable_name_with_suffix = (
                    variable_name + self.get_tag_suffix(value_xpath)
                )
                if variable_name_with_suffix not in self.found_identifiers:
                    fields.append(
                        LocatorField(variable_name_with_suffix,
                                     value_xpath,
                                     priority=6)
                    )
                    self.found_identifiers.add(variable_name_with_suffix)
        
        return fields
    
    def extract_buttons(self, soup: BeautifulSoup) -> List[LocatorField]:
        """
        Extract button locators (generic for all buttons).
        ใช้ id > title > text เป็นหลัก
        และไม่ผูกการกรองซ้ำกับ self.found_identifiers โดยตรง
        """
        buttons = soup.select('button')
        candidates: dict[str, LocatorField] = {}

        for idx, button in enumerate(buttons, start=1):
            elem_id = (button.get('id') or '').strip()
            title = (button.get('title') or '').strip()
            text = self.get_menu_text(button) or ''

            # ถ้าไม่มี id / title / text เลย → ข้าม
            if not elem_id and not title and not text:
                continue

            # ถ้า text มีแค่ 1 ตัวอักษรและไม่มี title → มักเป็นปุ่มไอคอน
            if (not title) and len(text.strip()) == 1:
                continue

            # ---- เลือก source สำหรับชื่อแปร ----
            name_source_text = title or text or elem_id

            variable_name_base = self.create_variable_name(
                name_source_text,
                is_technical_source=False
            )
            if not variable_name_base and elem_id:
                variable_name_base = self.create_variable_name(
                    elem_id,
                    is_technical_source=True
                )

            if not variable_name_base:
                continue

            # ---- เลือก XPath ----
            xpath = ''
            priority = 5

            if elem_id:
                xpath = f"//button[@id='{elem_id}']"
                priority = 1
            elif title:
                xpath = f"//button[@title=\"{title}\"]"
                priority = 2
            elif text.strip():
                xpath = f"//button[normalize-space()='{text.strip()}']"
                priority = 3

            if not xpath:
                continue

            variable_name_full = variable_name_base + self.get_tag_suffix(xpath)

            lf = LocatorField(variable_name_full, xpath, priority)

            existing = candidates.get(variable_name_full)
            if existing is None or lf.priority < existing.priority:
                candidates[variable_name_full] = lf

        fields: List[LocatorField] = list(candidates.values())
        for f in fields:
            self.found_identifiers.add(f.variable)

        return fields


    def extract_tables(self, soup: BeautifulSoup) -> List[LocatorField]:
        """
        Extract table, thead, and tbody locators, prioritizing XPath by
        ID > Class > Index.
        """
        fields: List[LocatorField] = []
        tables = soup.find_all('table')
        table_index = 1

        for table in tables:
            base_name, table_xpath = '', ''
            
            prev_header = table.find_previous(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            if prev_header:
                base_name = (
                    self.create_variable_name(
                        prev_header.get_text(strip=True)
                    ) + "_TABLE"
                )
            elif table.get('id') and self.is_id_descriptive(table.get('id')):
                base_name = self.create_variable_name(
                    table.get('id'), is_technical_source=True
                )
            else:
                base_name = f"TABLE_{table_index}"

            table_id = table.get('id')
            table_classes = table.get('class', [])
            significant_classes = [
                'ant-table-fixed', 'table-bordered', 'dataTable', 'table'
            ]
            found_class = next(
                (cls for cls in significant_classes if cls in table_classes),
                None
            )

            if table_id and self.is_id_descriptive(table_id):
                table_xpath = f"//table[@id='{table_id}']"
            elif found_class:
                table_xpath = f"//table[contains(@class, '{found_class}')]"
            elif table_id:  # Fallback to non-descriptive ID
                table_xpath = f"//table[@id='{table_id}']"
            else:
                table_xpath = f"(//table)[{table_index}]"
            
            priority = 4

            if base_name and base_name not in self.found_identifiers:
                fields.append(
                    LocatorField(base_name, table_xpath, priority)
                )
                self.found_identifiers.add(base_name)
                
                if table.find('thead'):
                    thead_xpath = f"{table_xpath}/thead"
                    thead_var = f"{base_name}_THEAD"
                    if thead_var not in self.found_identifiers:
                        fields.append(
                            LocatorField(thead_var, thead_xpath, priority)
                        )
                        self.found_identifiers.add(thead_var)

                if table.find('tbody'):
                    tbody_xpath = f"{table_xpath}/tbody"
                    tbody_var = f"{base_name}_TBODY"
                    if tbody_var not in self.found_identifiers:
                        fields.append(
                            LocatorField(tbody_var, tbody_xpath, priority)
                        )
                        self.found_identifiers.add(tbody_var)

            table_index += 1
            
        return fields

    def extract_menu_links(self, soup: BeautifulSoup) -> List[LocatorField]:
        """
        Extract menu <a> tags (sidebar-link, nav-link)
        Per user request, ALL links found by this function are considered menus
        and will receive the _MENU suffix.
        """
        fields: List[LocatorField] = []
        links = soup.select('a.sidebar-link, a.nav-link') 

        for link in links:
            elem_id = link.get('id', '').strip()
            title = link.get('title', '').strip()
            
            menu_text_span = link.select_one('span.hide-menu')
            menu_text = (
                menu_text_span.get_text(strip=True)
                if menu_text_span else ''
            )

            if not menu_text: 
                menu_text = self.get_menu_text(link)

            if not menu_text and title:
                menu_text = title
            
            is_desc_id = self.is_id_descriptive(elem_id)
            has_text = bool(menu_text)
            has_unique_title = title and \
                len(soup.select(f"a[title='{title}']")) == 1
            
            xpath = ''
            priority = 5
            name_source_text = ''
            is_technical_source = False

            if is_desc_id:
                xpath, priority = f"//a[@id='{elem_id}']", 1
                name_source_text = menu_text if has_text else elem_id
                is_technical_source = not has_text
            
            elif has_unique_title:
                xpath, priority = f"//a[@title='{title}']", 2
                name_source_text = title 
            
            elif has_text:
                if menu_text_span:
                    xpath, priority = (
                        f"//a[.//span[normalize-space()='{menu_text}']]",
                        3
                    )
                else:
                    xpath, priority = (
                        f"//a[normalize-space()='{menu_text}']",
                        3
                    )
                name_source_text = menu_text
            
            elif elem_id:  # Fallback: ID ไม่สื่อความหมาย
                xpath, priority = f"//a[@id='{elem_id}']", 4
                name_source_text = menu_text if has_text else elem_id
                is_technical_source = not has_text

            if not xpath or not name_source_text:
                continue
                
            variable_name = self.create_variable_name(
                name_source_text, is_technical_source
            )
            variable_name = variable_name + '_MENU'
            
            if variable_name and variable_name not in self.found_identifiers:
                fields.append(LocatorField(variable_name, xpath, priority))
                self.found_identifiers.add(variable_name)

        return fields

    def extract_ant_menu_items(self, soup: BeautifulSoup) -> List[LocatorField]:
        """
        Extract Ant Design (ant-menu) <li> items.
        These are direct navigation links.
        --- CHANGE: considered _MENU ---
        """
        fields: List[LocatorField] = []
        menu_items = soup.select('li.ant-menu-item')

        for item in menu_items:
            if item.select_one('a.nav-link'):
                continue
                
            router_link = item.get('routerlink', '').strip()
            menu_text = self.get_menu_text(item) 
            
            has_text = bool(menu_text)
            has_router_link = bool(router_link)
            
            xpath = ''
            priority = 5
            name_source_text = ''
            is_technical_source = False

            if has_router_link:
                xpath, priority = (
                    f"//li[@routerlink='{router_link}']", 1
                )
                name_source_text = menu_text if has_text else router_link
                is_technical_source = not has_text
            
            elif has_text:
                xpath = (
                    "//li[contains(@class, 'ant-menu-item') and "
                    f"normalize-space(.)='{menu_text}']"
                )
                priority = 3
                name_source_text = menu_text
            
            if not xpath or not name_source_text:
                continue
                
            variable_name = self.create_variable_name(
                name_source_text, is_technical_source
            )
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
        fields: List[LocatorField] = []
        submenu_titles = soup.select(
            'li.ant-menu-submenu > div.ant-menu-submenu-title'
        )

        for title_div in submenu_titles:
            menu_text = self.get_menu_text(title_div)
            
            if not menu_text:
                continue
            
            xpath = (
                "//li[contains(@class, 'ant-menu-submenu')]"
                f"[.//span[normalize-space()='{menu_text}']]"
                "/div[contains(@class, 'ant-menu-submenu-title')]"
            )
            
            priority = 3
            variable_name = self.create_variable_name(menu_text)
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
        fields: List[LocatorField] = []
        first_tbody = soup.select_one('table tbody')
        if not first_tbody:
            return []
        
        first_row = first_tbody.select_one('tr:first-child, tr:nth-child(1)')
        if not first_row:
            return []

        actions = first_row.select(
            'a[title], button[title], a[nz-tooltip], button[nz-tooltip]'
        )

        for action in actions:
            title = (
                action.get('title') or action.get('nz-tooltip', '')
            ).strip()
            if not title:
                continue
            
            tag_name = action.name.lower()
            attr_name = 'title' if action.get('title') else 'nz-tooltip'
            xpath = (
                f"(//tbody)[1]/tr[1]//{tag_name}[@{attr_name}='{title}']"
            )
            
            variable_name = self.create_variable_name(title)
            
            if tag_name == 'button':
                suffix = '_BTN'
            else:
                suffix = '_LINK' 
                
            variable_name += suffix
            
            if variable_name and variable_name not in self.found_identifiers:
                fields.append(LocatorField(variable_name, xpath, priority=3))
                self.found_identifiers.add(variable_name)
                
        return fields


    def extract_checkboxes(self, soup: BeautifulSoup) -> List[LocatorField]:
        """
        Extract checkboxes using label text (generic for all checkbox types).
        Works with any checkbox that has an associated label.
        
        Strategy: Analyze structure and choose appropriate XPath pattern
        """
        fields: List[LocatorField] = []
        
        # Find all checkboxes
        checkboxes = soup.select('input[type="checkbox"]')
        
        for checkbox in checkboxes:
            checkbox_id = checkbox.get('id', '').strip()
            
            # Try to find associated label
            label = None
            pattern_type = None
            
            # Strategy 1: label with 'for' attribute matching checkbox id
            if checkbox_id:
                label = soup.select_one(f'label[for="{checkbox_id}"]')
                if label:
                    pattern_type = 'for_attr'
            
            # Strategy 2: checkbox in label (parent)
            if not label:
                label = checkbox.find_parent('label')
                if label:
                    pattern_type = 'parent'
            
            # Strategy 3: label as next sibling
            if not label:
                sibling = checkbox.next_sibling
                while sibling:
                    if hasattr(sibling, 'name') and sibling.name == 'label':
                        label = sibling
                        pattern_type = 'following_sibling'
                        break
                    sibling = sibling.next_sibling
            
            # Strategy 4: label as previous sibling
            if not label:
                sibling = checkbox.previous_sibling
                while sibling:
                    if hasattr(sibling, 'name') and sibling.name == 'label':
                        label = sibling
                        pattern_type = 'preceding_sibling'
                        break
                    sibling = sibling.previous_sibling
            
            if not label:
                continue
            
            # Get clean label text
            label_text = label.get_text(strip=True)
            if not label_text:
                continue
            
            # Create variable name from label text
            variable_name = self.create_variable_name(label_text, is_technical_source=False)
            
            if not variable_name or variable_name in self.found_identifiers:
                continue
            
            # Build XPath based on pattern type
            label_text_escaped = label_text.replace("'", "\\'")
            
            if pattern_type == 'parent':
                # Checkbox inside label
                xpath = (
                    f"//label[contains(normalize-space(), '{label_text_escaped}')]"
                    "//input[@type='checkbox']"
                )
            elif pattern_type == 'following_sibling':
                # Label after checkbox (most reliable with immediate sibling)
                xpath = (
                    f"//input[@type='checkbox']"
                    f"[following-sibling::label[1][contains(normalize-space(), '{label_text_escaped}')]]"
                )
            elif pattern_type == 'preceding_sibling':
                # Label before checkbox
                xpath = (
                    f"//label[contains(normalize-space(), '{label_text_escaped}')]"
                    "/following-sibling::input[@type='checkbox']"
                )
            else:
                # Default: label after checkbox (most common)
                xpath = (
                    f"//input[@type='checkbox']"
                    f"[following-sibling::label[1][contains(normalize-space(), '{label_text_escaped}')]]"
                )
            
            # Add suffix
            variable_name = variable_name + '_CHECKBOX'
            
            if variable_name not in self.found_identifiers:
                fields.append(LocatorField(variable_name, xpath, priority=2))
                self.found_identifiers.add(variable_name)
        
        return fields
    def parse_html(self, html_content: str) -> List[LocatorField]:
        """
        Main parsing function to extract all locators from HTML.
        """
        self.found_identifiers.clear()
        soup = BeautifulSoup(html_content, 'html.parser')
        

        all_fields = (
            (self.extract_form_fields(soup) or []) +
            (self.extract_upload_fields(soup) or []) +
            (self.extract_display_fields(soup) or []) +
            (self.extract_buttons(soup) or []) +
            (self.extract_tables(soup) or []) +
            (self.extract_menu_links(soup) or []) +
            (self.extract_ant_menu_items(soup) or []) +
            (self.extract_ant_submenu_titles(soup) or []) +
            (self.extract_first_row_actions(soup) or []) +
            (self.extract_checkboxes(soup) or [])
        )
        
        # Post-process: ถ้ามี *_INPUT และ *_SELECT พร้อมกัน ให้เก็บ *_INPUT อย่างเดียว
        preferred: dict[str, tuple[int, LocatorField]] = {}
        suffix_rank = {'_INPUT': 1, '_SELECT': 2}

        for f in all_fields:
            m = re.match(r'^(.*)_(INPUT|SELECT)$', f.variable)
            if m:
                base = m.group(1)
                suf = '_' + m.group(2)
                key = base
                rank = suffix_rank.get(suf, 99)
            else:
                key = f.variable
                rank = 99

            if key not in preferred:
                preferred[key] = (rank, f)
            else:
                old_rank, old_field = preferred[key]
                if rank < old_rank or (rank == old_rank and
                                       f.priority < old_field.priority):
                    preferred[key] = (rank, f)

        unique_fields = [t[1] for t in preferred.values()]
        unique_fields.sort(key=lambda f: f.priority)
        return unique_fields


def generate_robot_framework_variables(
    fields: List[LocatorField], source_info: str = ''
) -> str:
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