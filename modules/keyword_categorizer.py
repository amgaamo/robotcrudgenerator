"""
modules/keyword_categorizer.py
Robot Framework Keyword Categorizer Module - Exact Mapping Version
Version: 2.0 - Using exact keyword name mapping
"""

def get_exact_keyword_mappings():
    """
    Returns exact keyword name mappings based on commonkeywords.resource
    """
    mappings = mappings = {
        # ============================================================
        # 1. System & Session - เริ่มต้นและปิดระบบ
        # ============================================================
        "⚙️ System & Session": [
            
            'Initialize System and Go to Login Page',
            'Open Browser and Go to website',
            'Login System',
            'Logout System',
            'Close All Active Browsers',
        ],
        
        # ============================================================
        # 2. Navigation & Menu - การนำทาง เมนู หน้า แท็บ
        # ============================================================
        "🧭 Navigation & Menu": [
            'Get MAIN pageids for switch page',
            'Get Information New Page Open',
            'Switch Another Open Page',
            'Go to MENU name',
            'Go to SUBMENU name',
            'Verify Page Name is correct',
            'Verify Welcome page',
            'Verify Login Page'
        ],
        
        # ============================================================
        # 3. Form & Input - การกรอกและลบข้อมูลในฟอร์ม
        # ============================================================
        "📝 Form & Input": [
            'Fill in search field',
            'Fill in data form',
            'Clear field data form'
        ],
        
        # ============================================================
        # 4. Form Verification - ตรวจสอบฟอร์มและฟิลด์
        # ============================================================
        "✅ Form Verification": [
            'Verify data form',
            'Verify Warning message field',
            'Verify Field State',
            'Verify Button State',
        ],
        
        # ============================================================
        # 5. Modal & Alert Verification - ตรวจสอบ Modal และ Alert
        # ============================================================
        "💬 Modal & Alert": [
            'Click Modal Button',
            'Verify Modal Title message',
            'Verify Modal Content message',
            'Verify Modal should Hidden'
        ],
        
        # ============================================================
        # 6. Table & List Verification - ตรวจสอบตาราง
        # ============================================================
        "📊 Table & List Verification": [
            'Verify Result of data table',
            'Verify data table result is No Record Found',
            'Verify Result of Data Card',
        ],
        
        # ============================================================
        # 7. Button Actions - การคลิกปุ่มต่างๆ
        # ============================================================
        "🎯 Button Actions": [
            'Click Login Button',
            'Click button on list page',
            'Click button on detail page'
        ],
        
        # ============================================================
        # 8. File Operations - การจัดการไฟล์
        # ============================================================
        "📁 File Operations": [
            'Choose file to upload',
            'Download data and save file to download folder',
            'Clear Directory download file',
            'Click Upload Button'
        ],
        
        # ============================================================
        # 9. Utilities - เครื่องมือช่วยเหลือทั่วไป
        # ============================================================
        "🛠️ Utilities": [
            'Wait Loading progress',
            'Extract Value from JSON data',
            'Convert Data to lower or upper case',
            'Convert Number To Decimal Format',
            'Set Data Variable',
            'Get Data Current Date',
            'Generate Random Values',
            'Perform ZAP Scan And Report',
            'Setup ZAP And Browser'
        ]
    }
    
    return mappings


def categorize_keywords(all_keywords):
    """
    Categorizes keywords using exact name matching.
    ใช้การ match แบบตรงตัวเท่านั้น (case-insensitive)
    """
    mappings = get_exact_keyword_mappings()
    
    # สร้าง lookup dictionary สำหรับการค้นหาที่เร็วขึ้น
    keyword_to_category = {}
    for category, keyword_names in mappings.items():
        for kw_name in keyword_names:
            keyword_to_category[kw_name.lower()] = category
    
    # Initialize result dictionary
    categorized = {cat: [] for cat in mappings.keys()}
    categorized["🧩 Others"] = []
    
    # Categorize each keyword
    for kw in all_keywords:
        kw_name_lower = kw['name'].lower()
        
        if kw_name_lower in keyword_to_category:
            category = keyword_to_category[kw_name_lower]
            categorized[category].append(kw)
        else:
            categorized["🧩 Others"].append(kw)
    
    # Remove empty categories (except Others)
    categorized = {
        k: v for k, v in categorized.items() 
        if v or k == "🧩 Others"
    }
    
    return categorized


def get_expansion_config():
    """
    Returns recommended expansion configuration for UI.
    กำหนดว่ากลุ่มไหนควรเปิดอัตโนมัติ (expanded=True)
    """
    return {
        "⚙️ System & Session": False,      
        "🧭 Navigation & Menu": False,     
        "📝 Form & Input": False,          
        "✅ Form Verification": False,     
        "💬 Modal & Alert": False,         
        "📊 Table & List Verification": False,         
        "🎯 Button Actions": False,        
        "📁 File Operations": False,      
        "🛠️ Utilities": False,           
        "🧩 Others": False                
    }


def get_category_stats(categorized_keywords):
    """
    Gets comprehensive statistics about categorized keywords.
    """
    category_counts = {
        cat: len(kws) 
        for cat, kws in categorized_keywords.items() 
        if kws
    }
    
    non_others_counts = {
        cat: count 
        for cat, count in category_counts.items() 
        if cat != "🧩 Others" and count > 0
    }
    
    stats = {
        'total_keywords': sum(len(kws) for kws in categorized_keywords.values()),
        'total_categories': len([k for k, v in categorized_keywords.items() 
                                if v and k != "🧩 Others"]),
        'uncategorized': len(categorized_keywords.get("🧩 Others", [])),
        'category_counts': category_counts,
        'largest_category': max(non_others_counts.items(), 
                              key=lambda x: x[1]) if non_others_counts else (None, 0),
        'smallest_category': min(non_others_counts.items(), 
                               key=lambda x: x[1]) if non_others_counts else (None, 0)
    }
    
    return stats


def get_category_priority(category_name):
    """
    Returns priority level for each category (1 = highest, 9 = lowest).
    Used for sorting categories in UI.
    """
    priorities = {
        "⚙️ System & Session": 1,
        "🧭 Navigation & Menu": 2,
        "📝 Form & Input": 3,
        "✅ Form Verification": 4,
        "📊 Table & List Verification": 5,
        "🎯 Button Actions": 6,
        "💬 Modal & Alert": 7,        
        "📁 File Operations": 8,
        "🛠️ Utilities": 9,
        "🧩 Others": 99  # Always last
    }
    return priorities.get(category_name, 100)


def search_keywords_by_name(all_keywords, search_term):
    """
    Searches keywords by name (case-insensitive).
    """
    if not search_term:
        return all_keywords
    
    search_lower = search_term.lower()
    return [kw for kw in all_keywords if search_lower in kw['name'].lower()]


def get_keywords_by_category(categorized_keywords, category_name):
    """
    Gets all keywords in a specific category.
    """
    return categorized_keywords.get(category_name, [])


def get_category_description(category_name):
    """
    Returns a helpful description for each category in Thai language.
    """
    descriptions = {
        "⚙️ System & Session": "เริ่มต้นระบบ, เปิดเบราว์เซอร์, Login/Logout",
        "🧭 Navigation & Menu": "เปิดเมนู, เปลี่ยนหน้า, สลับแท็บ/หน้าต่าง",
        "📝 Form & Input": "กรอกข้อมูล, ค้นหา, ล้างฟอร์ม",
        "✅ Form Verification": "ตรวจสอบฟอร์ม, ฟิลด์, ปุ่ม, ข้อความเตือน",
        "💬 Modal & Alert": "ตรวจสอบ Modal, Dialog, Alert, Notification",
        "📊 Table & List Verification": "ตรวจสอบตาราง, รายการ, ข้อมูลในหน้า List",
        "🎯 Button Actions": "คลิกปุ่มต่างๆ ในหน้า List/Detail",
        "📁 File Operations": "เลือกไฟล์, Upload, Download, ลบไฟล์",
        "🛠️ Utilities": "รอการโหลด, สร้างข้อมูล, แปลงค่า, ดึงข้อมูล",
        "🧩 Others": "Keywords อื่นๆ ที่ไม่อยู่ในหมวดหมู่"
    }
    return descriptions.get(category_name, "")


def get_category_icon_color(category_name):
    """
    Returns color scheme for each category (for future UI enhancement).
    """
    colors = {
        "⚙️ System & Session": "#4CAF50",      # Green
        "🧭 Navigation & Menu": "#2196F3",     # Blue
        "📝 Form & Input": "#FF9800",          # Orange
        "✅ Form Verification": "#4CAF50",     # Green
        "💬 Modal & Alert": "#9C27B0",         # Purple
        "📊 Table & List Verification": "#00BCD4",  # Cyan
        "🎯 Button Actions": "#E91E63",        # Pink
        "📁 File Operations": "#795548",       # Brown
        "🛠️ Utilities": "#607D8B",            # Blue Grey
        "🧩 Others": "#9E9E9E"                 # Grey
    }
    return colors.get(category_name, "#666666")


def sort_categories_by_priority(categorized_keywords):
    """
    Sorts categories by their priority level.
    """
    return sorted(
        categorized_keywords.items(),
        key=lambda x: get_category_priority(x[0])
    )


def export_categorization_summary(categorized_keywords, output_file=None):
    """
    Exports categorization summary to a text file or returns as string.
    """
    stats = get_category_stats(categorized_keywords)
    
    summary = []
    summary.append("=" * 80)
    summary.append("ROBOT FRAMEWORK KEYWORDS CATEGORIZATION SUMMARY")
    summary.append("=" * 80)
    summary.append(f"\n📊 Total Keywords: {stats['total_keywords']}")
    summary.append(f"📁 Total Categories: {stats['total_categories']}")
    summary.append(f"🧩 Uncategorized: {stats['uncategorized']}")
    
    if stats['largest_category'][0]:
        summary.append(f"\n📈 Largest Category: {stats['largest_category'][0]} "
                      f"({stats['largest_category'][1]} keywords)")
    if stats['smallest_category'][0]:
        summary.append(f"📉 Smallest Category: {stats['smallest_category'][0]} "
                      f"({stats['smallest_category'][1]} keywords)")
    
    summary.append("\n" + "=" * 80)
    summary.append("CATEGORIES BREAKDOWN")
    summary.append("=" * 80)
    
    for category, keywords in sort_categories_by_priority(categorized_keywords):
        if keywords:
            desc = get_category_description(category)
            summary.append(f"\n{category} ({len(keywords)} keywords)")
            summary.append(f"  📝 {desc}")
            for kw in sorted(keywords, key=lambda x: x['name']):
                summary.append(f"     ├─ {kw['name']}")
    
    summary.append("\n" + "=" * 80)
    
    summary_text = "\n".join(summary)
    
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(summary_text)
        return f"Summary exported to: {output_file}"
    else:
        return summary_text
