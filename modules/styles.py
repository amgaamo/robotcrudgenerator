def get_css():
    """Return GitHub Dark Premium CSS styling"""
    return """
    <style>
        /* ==================== ROOT VARIABLES ==================== */
        :root {
            /* GitHub Dark Color Palette */
            --primary-color: #58a6ff;
            --primary-hover: #79c0ff;
            --primary-active: #1f6feb;
            --success-color: #3fb950;
            --success-hover: #56d364;
            --warning-color: #d29922;
            --warning-hover: #e3b341;
            --danger-color: #f85149;
            --danger-hover: #ff7b72;
            --info-color: #58a6ff;
            
            /* GitHub Dark Backgrounds */
            --bg-canvas: #0d1117;
            --bg-default: #161b22;
            --bg-overlay: #1c2128;
            --bg-inset: #010409;
            --bg-subtle: #21262d;
            
            /* GitHub Text Colors */
            --text-primary: #e6edf3;
            --text-secondary: #7d8590;
            --text-tertiary: #6e7681;
            --text-link: #58a6ff;
            --text-muted: #848d97;
            
            /* GitHub Borders */
            --border-default: #30363d;
            --border-muted: #21262d;
            --border-subtle: #161b22;
            
            /* Premium Shadows */
            --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.3);
            --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(88, 166, 255, 0.1);
            --shadow-lg: 0 12px 40px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(88, 166, 255, 0.15);
            --shadow-inset: inset 0 1px 2px rgba(0, 0, 0, 0.3);
            --shadow-glow: 0 0 20px rgba(88, 166, 255, 0.3);
            
            /* Spacing */
            --spacing-xs: 0.25rem;
            --spacing-sm: 0.5rem;
            --spacing-md: 1rem;
            --spacing-lg: 1.5rem;
            --spacing-xl: 2rem;
            
            /* Border Radius */
            --radius-sm: 4px;
            --radius-md: 8px;
            --radius-lg: 12px;
            --radius-xl: 16px;
            
            /* Transitions */
            --transition-fast: 150ms cubic-bezier(0.4, 0, 0.2, 1);
            --transition-normal: 250ms cubic-bezier(0.4, 0, 0.2, 1);
            --transition-smooth: 350ms cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        
        /* ==================== ANIMATIONS ==================== */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }
        
        @keyframes glow {
            0%, 100% { box-shadow: 0 0 20px rgba(88, 166, 255, 0.3); }
            50% { box-shadow: 0 0 30px rgba(88, 166, 255, 0.5); }
        }
        
        @keyframes shimmer {
            0% { background-position: -200% center; }
            100% { background-position: 200% center; }
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        @keyframes checkPop {
            0% { opacity: 0; transform: scale(0) rotate(-180deg); }
            70% { transform: scale(1.2) rotate(10deg); }
            100% { opacity: 1; transform: scale(1) rotate(0); }
        }
        
        @keyframes dropdownSlide {
            from {
                opacity: 0;
                transform: translateY(-16px) scale(0.95);
            }
            to {
                opacity: 1;
                transform: translateY(0) scale(1);
            }
        }
        
        /* ==================== BACKGROUND ==================== */
        .main {
            background: linear-gradient(180deg, var(--bg-canvas) 0%, #0a0e14 100%);
            padding: var(--spacing-xl);
            max-width: 1600px;
            margin: 0 auto;
            min-height: 100vh;
            position: relative;
        }
        
        .main::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 300px;
            background: radial-gradient(ellipse at top, rgba(88, 166, 255, 0.08) 0%, transparent 70%);
            pointer-events: none;
            z-index: 0;
        }
        
        .block-container {
            padding-top: var(--spacing-lg);
            padding-bottom: var(--spacing-xl);
            position: relative;
            z-index: 1;
        }
        
        /* ==================== TYPOGRAPHY ==================== */
        .main h1 {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--text-primary) 0%, var(--primary-hover) 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            letter-spacing: -0.02em;
            margin-bottom: var(--spacing-lg);
            padding-bottom: var(--spacing-md);
            border-bottom: 2px solid transparent;
            border-image: linear-gradient(90deg, var(--primary-color) 0%, transparent 100%);
            border-image-slice: 1;
            animation: fadeIn 0.6s ease-out;
        }
        
        .main h2 {
            font-size: 1.75rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: var(--spacing-md);
            padding-bottom: var(--spacing-sm);
            border-bottom: 1px solid var(--border-muted);
            position: relative;
            animation: slideIn 0.6s ease-out;
        }
        
        .main h2::before {
            content: '';
            position: absolute;
            bottom: -1px;
            left: 0;
            width: 60px;
            height: 2px;
            background: linear-gradient(90deg, var(--primary-color), var(--primary-hover));
            border-radius: 2px;
        }
        
        .main h3 {
            font-size: 1.35rem;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: var(--spacing-sm);
        }
        
        .main p, .main label {
            color: var(--text-secondary);
            line-height: 1.7;
        }
        
        /* ==================== PREMIUM BUTTONS (Refactored to be smaller) ==================== */
        .stButton > button {
            background: var(--bg-subtle);
            border: 1px solid var(--border-default);
            border-radius: var(--radius-sm); /* REFACTOR: Smaller radius (4px) */
            color: var(--text-primary);
            padding: 0 14px; /* REFACTOR: Smaller padding */
            height: 32px; /* REFACTOR: Explicit height */
            min-height: 32px; /* REFACTOR: Explicit height */
            font-weight: 600;
            font-size: 13px; /* REFACTOR: Smaller font */
            transition: all var(--transition-normal);
            box-shadow: var(--shadow-sm);
            position: relative;
            overflow: hidden;
            /* REFACTOR: Add flex properties for alignment */
            display: flex;
            align-items: center;
            justify-content: center;
            line-height: 1; 
        }
        
        .stButton > button::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.05), transparent);
            transition: left 0.5s;
        }
        
        .stButton > button:hover {
            background: var(--bg-overlay);
            border-color: var(--primary-color);
            transform: none; /* REFACTOR: Remove Y transform for small buttons */
            filter: brightness(1.1); /* REFACTOR: Add subtle hover */
            box-shadow: var(--shadow-md);
        }
        
        .stButton > button:hover::before {
            left: 100%;
        }
        
        .stButton > button:active {
            transform: scale(0.98); /* REFACTOR: Change active effect */
            filter: brightness(0.95);
            box-shadow: var(--shadow-inset);
        }
        
        /* Primary button inherits new smaller size */
        .stButton > button[kind="primary"] {
            background: var(--primary-active);
            border-color: var(--primary-active);
            color: white;
            box-shadow: var(--shadow-sm);
        }
        
        .stButton > button[kind="primary"]:hover {
            background: var(--primary-color);
            border-color: var(--primary-color);
            box-shadow: var(--shadow-md);
            transform: none; /* REFACTOR: Remove Y transform */
            filter: brightness(1.1);
        }
        
        /* ==================== PREMIUM INPUTS ==================== */
        .stTextInput > div > div > input,
        .stNumberInput > div > div > input {
            background: var(--bg-default);
            border: 1px solid var(--border-default);
            border-radius: var(--radius-md);
            color: var(--text-primary);
            padding: 10px 14px;
            font-size: 14px;
            line-height: 1.5;
            transition: all var(--transition-normal);
            box-shadow: var(--shadow-inset);
        }
        
        .stTextInput > div > div > input:hover,
        .stNumberInput > div > div > input:hover {
            border-color: var(--primary-color);
            box-shadow: var(--shadow-inset), 0 0 0 3px rgba(88, 166, 255, 0.1);
        }
        
        .stTextInput > div > div > input:focus,
        .stNumberInput > div > div > input:focus {
            background: var(--bg-canvas);
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.25);
            outline: none;
        }
        
        /* ==================== PREMIUM TEXTAREA ==================== */
        .stTextArea > div > div > textarea {
            min-height: 300px;
            font-family: ui-monospace, SFMono-Regular, SF Mono, Menlo, Consolas, monospace;
            font-size: 13px;
            line-height: 1.6;
            background: var(--bg-default);
            color: var(--text-primary);
            border: 1px solid var(--border-default);
            border-radius: var(--radius-md);
            padding: 12px 16px;
            box-shadow: var(--shadow-inset);
            transition: all var(--transition-normal);
        }
        
        .stTextArea > div > div > textarea:hover {
            border-color: var(--primary-color);
            box-shadow: var(--shadow-inset), 0 0 0 3px rgba(88, 166, 255, 0.1);
        }
        
        .stTextArea > div > div > textarea:focus {
            background: var(--bg-canvas);
            border-color: var(--primary-color);
            box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.25);
            outline: none;
        }
        
        /* ==================== PREMIUM TABS ==================== */
        .stTabs [data-baseweb="tab-list"] {
            background: var(--bg-default);
            border-bottom: 2px solid var(--border-default);
            padding: 0 var(--spacing-sm);
            gap: var(--spacing-xs);
            border-radius: var(--radius-md) var(--radius-md) 0 0;
        }
        
        .stTabs [data-baseweb="tab"] {
            background: transparent;
            border: none;
            border-bottom: 3px solid transparent;
            border-radius: var(--radius-sm) var(--radius-sm) 0 0;
            color: var(--text-secondary);
            font-weight: 500;
            font-size: 18px;
            padding: 14px 22px;
            margin-bottom: -2px;
            transition: all var(--transition-normal);
            position: relative;
        }
        
        .stTabs [data-baseweb="tab"]:hover {
            color: var(--text-primary);
            background: var(--bg-subtle);
        }
        
        .stTabs [data-baseweb="tab"][aria-selected="true"] {
            color: var(--primary-hover);
            background: var(--bg-subtle);
            border-bottom-color: var(--primary-color);
            font-weight: 600;
        }
        
        /* ==================== PREMIUM SELECTBOX ==================== */
        .stSelectbox [data-baseweb="select"] > div {
            background: var(--bg-default) !important;
            border: 1px solid var(--border-default) !important;
            border-radius: var(--radius-md) !important;
            padding: 0 14px !important;
            min-height: 42px !important;
            transition: all var(--transition-normal);
            box-shadow: var(--shadow-inset);
            overflow: visible !important;
            display: flex !important;
            align-items: center !important;
            position: relative;
            cursor: pointer !important;
            outline: none !important;
        }
        
        .stSelectbox [data-baseweb="select"] > div:hover {
            border-color: var(--primary-color) !important;
            box-shadow: var(--shadow-inset), 0 0 0 3px rgba(88, 166, 255, 0.1);
            transform: translateY(-1px);
        }
        
        .stSelectbox [data-baseweb="select"] > div:focus-within {
            border-color: var(--primary-color) !important;
            box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.25);
            transform: translateY(-1px);
            outline: none !important;
        }
        
        /* Fix cursor for selectbox inner elements */
        .stSelectbox [data-baseweb="select"] * {
            cursor: pointer !important;
            outline: none !important;
        }
        
        /* Remove outline from all select elements */
        .stSelectbox [data-baseweb="select"] input,
        .stSelectbox [data-baseweb="select"] div[role="button"] {
            outline: none !important;
        }
        
        /* Dropdown menu */
        [data-baseweb="popover"] {
            z-index: 999999 !important;
            position: fixed !important;
        }
        
        [data-baseweb="popover"] > div {
            background: var(--bg-overlay) !important;
            border: 1px solid var(--border-default) !important;
            border-radius: var(--radius-lg) !important;
            box-shadow: var(--shadow-lg) !important;
            margin-top: 8px !important;
            max-height: 340px !important;
            overflow-y: auto !important;
            padding: 8px !important;
            animation: dropdownSlide 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
        }
        
        [data-baseweb="popover"] > div::-webkit-scrollbar {
            width: 10px;
        }
        
        [data-baseweb="popover"] > div::-webkit-scrollbar-track {
            background: transparent;
            margin: 8px 0;
        }
        
        [data-baseweb="popover"] > div::-webkit-scrollbar-thumb {
            background: var(--bg-subtle);
            border-radius: 5px;
            border: 2px solid transparent;
            background-clip: padding-box;
        }
        
        [data-baseweb="popover"] [role="option"] {
            background: transparent !important;
            color: var(--text-secondary) !important;
            padding: 12px 16px !important;
            margin: 2px 0 !important;
            font-size: 14px !important;
            font-weight: 500 !important;
            border-radius: var(--radius-md) !important;
            transition: all var(--transition-normal);
            display: flex !important;
            align-items: center !important;
            position: relative;
            cursor: pointer;
        }
        
        [data-baseweb="popover"] [role="option"]::before {
            content: '';
            position: absolute;
            left: 0;
            top: 50%;
            transform: translateY(-50%);
            width: 4px;
            height: 0;
            background: var(--primary-color);
            border-radius: 0 3px 3px 0;
            transition: height var(--transition-normal);
        }
        
        [data-baseweb="popover"] [role="option"]:hover {
            background: var(--bg-subtle) !important;
            color: var(--text-primary) !important;
            transform: translateX(6px);
            padding-left: 22px !important;
        }
        
        [data-baseweb="popover"] [role="option"]:hover::before {
            height: 70%;
        }
        
        [data-baseweb="popover"] [role="option"][aria-selected="true"] {
            background: rgba(88, 166, 255, 0.15) !important;
            color: var(--primary-hover) !important;
            font-weight: 600 !important;
            border: 1px solid rgba(88, 166, 255, 0.3);
        }
        
        [data-baseweb="popover"] [role="option"][aria-selected="true"]::after {
            content: '✓';
            margin-left: auto;
            font-weight: 700;
            font-size: 16px;
            color: var(--primary-color);
            animation: checkPop 0.4s cubic-bezier(0.68, -0.55, 0.265, 1.55);
        }
        
        /* ==================== PREMIUM MULTISELECT ==================== */
        .stMultiSelect [data-baseweb="select"] > div {
            background: var(--bg-default) !important;
            border: 1px solid var(--border-default) !important;
            border-radius: var(--radius-md) !important;
            transition: all var(--transition-normal);
            box-shadow: var(--shadow-inset);
        }
        
        .stMultiSelect [data-baseweb="tag"] {
            background: rgba(88, 166, 255, 0.15) !important;
            border: 1px solid rgba(88, 166, 255, 0.3) !important;
            color: var(--primary-hover) !important;
            border-radius: var(--radius-sm) !important;
            padding: 4px 10px !important;
            font-weight: 600;
            font-size: 12px;
            transition: all var(--transition-fast);
        }
        
        .stMultiSelect [data-baseweb="tag"]:hover {
            background: rgba(88, 166, 255, 0.25) !important;
            transform: translateY(-1px);
        }
        
        /* ==================== PREMIUM CONTAINERS ==================== */
        [data-testid="stContainer"] {
            background: linear-gradient(135deg, var(--bg-default) 0%, var(--bg-overlay) 100%);
            border: 1px solid var(--border-default);
            border-radius: var(--radius-lg);
            padding: var(--spacing-lg);
            box-shadow: var(--shadow-md);
            position: relative;
            overflow: visible !important;
            transition: all var(--transition-normal);
        }
        
        [data-testid="stContainer"]::before {
            content: '';
            position: absolute;
            inset: 0;
            border-radius: var(--radius-lg);
            padding: 1px;
            background: linear-gradient(135deg, rgba(88, 166, 255, 0.3), transparent);
            -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
            mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
            -webkit-mask-composite: xor;
            mask-composite: exclude;
            opacity: 0;
            transition: opacity var(--transition-normal);
        }
        
        [data-testid="stContainer"]:hover {
            box-shadow: var(--shadow-lg);
            transform: translateY(-2px);
        }
        
        [data-testid="stContainer"]:hover::before {
            opacity: 1;
        }
        
        /* ==================== PREMIUM EXPANDER ==================== */
        [data-testid="stExpander"] .streamlit-expanderContent {
            max-height: 0;
            overflow: hidden;
            opacity: 0;
            transition: all 0.3s ease-in-out;
        }

        [data-testid="stExpander"][open] .streamlit-expanderContent {
            max-height: 5000px; /* ตั้งให้มากกว่า content จริงๆ */
            opacity: 1;
        }
        
        /* ==================== PREMIUM SIDEBAR ==================== */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, var(--bg-default) 0%, var(--bg-inset) 100%);
            border-right: 1px solid var(--border-default);
            padding: var(--spacing-lg);
            box-shadow: 4px 0 24px rgba(0, 0, 0, 0.3);
        }
        
        /* ==================== PREMIUM CODE BLOCKS ==================== */
        .stCodeBlock {
            background: linear-gradient(135deg, var(--bg-inset) 0%, #000000 100%) !important;
            border-radius: var(--radius-lg);
            border: 1px solid var(--border-default);
            padding: var(--spacing-lg);
            box-shadow: var(--shadow-md);
            position: relative;
            overflow: hidden;
        }
        
        .stCodeBlock::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 1px;
            background: linear-gradient(90deg, transparent, var(--primary-color), transparent);
        }
        
        .main code {
            background: rgba(88, 166, 255, 0.15);
            border: 1px solid rgba(88, 166, 255, 0.3);
            padding: 0.2em 0.6em;
            border-radius: var(--radius-sm);
            color: var(--primary-hover);
            font-size: 85%;
            font-family: ui-monospace, SFMono-Regular, monospace;
            box-shadow: 0 2px 4px rgba(88, 166, 255, 0.1);
        }
        
        /* ==================== PREMIUM METRICS ==================== */
        [data-testid="stMetricValue"] {
            background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 28px;
            font-weight: 700;
        }
        
        [data-testid="stMetricLabel"] {
            color: var(--text-secondary);
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
        }
        
        /* ==================== PREMIUM ALERTS ==================== */
        .stAlert {
            border-radius: var(--radius-lg);
            padding: 16px 20px;
            border-left: 4px solid;
            background: var(--bg-default);
            border: 1px solid;
            box-shadow: var(--shadow-sm);
            position: relative;
            overflow: hidden;
        }
        
        .stAlert::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            bottom: 0;
            width: 4px;
            opacity: 0.5;
        }
        
        .stSuccess {
            border-left-color: var(--success-color);
            border-color: rgba(63, 185, 80, 0.3);
            background: linear-gradient(90deg, rgba(63, 185, 80, 0.15), rgba(63, 185, 80, 0.05));
            color: var(--success-hover);
        }
        
        .stSuccess::before {
            background: linear-gradient(180deg, var(--success-color), var(--success-hover));
        }
        
        .stInfo {
            border-left-color: var(--info-color);
            border-color: rgba(88, 166, 255, 0.3);
            background: linear-gradient(90deg, rgba(88, 166, 255, 0.15), rgba(88, 166, 255, 0.05));
            color: var(--primary-hover);
        }
        
        .stInfo::before {
            background: linear-gradient(180deg, var(--info-color), var(--primary-hover));
        }
        
        .stWarning {
            border-left-color: var(--warning-color);
            border-color: rgba(210, 153, 34, 0.3);
            background: linear-gradient(90deg, rgba(210, 153, 34, 0.15), rgba(210, 153, 34, 0.05));
            color: var(--warning-hover);
        }
        
        .stWarning::before {
            background: linear-gradient(180deg, var(--warning-color), var(--warning-hover));
        }
        
        .stError {
            border-left-color: var(--danger-color);
            border-color: rgba(248, 81, 73, 0.3);
            background: linear-gradient(90deg, rgba(248, 81, 73, 0.15), rgba(248, 81, 73, 0.05));
            color: var(--danger-hover);
        }
        
        .stError::before {
            background: linear-gradient(180deg, var(--danger-color), var(--danger-hover));
        }
        
        /* ==================== PREMIUM SCROLLBAR ==================== */
        ::-webkit-scrollbar {
            width: 12px;
            height: 12px;
        }
        
        ::-webkit-scrollbar-track {
            background: var(--bg-canvas);
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(180deg, var(--bg-subtle), var(--text-tertiary));
            border-radius: 6px;
            border: 3px solid var(--bg-canvas);
            transition: background var(--transition-fast);
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(180deg, var(--text-tertiary), var(--primary-color));
        }
        
        /* ==================== PREMIUM DELETE BUTTON (Refactored to 32x32px) ==================== */
        /* This now matches the size of the new .ds-row-container delete button */
        button[data-testid*="stButton-key-loc_del_"] {
            background: transparent !important;
            border: 1px solid transparent !important;
            box-shadow: none !important;
            color: var(--text-tertiary) !important;
            transition: all var(--transition-normal);
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            width: 32px !important; /* REFACTOR: Standardized size */
            height: 32px !important; /* REFACTOR: Standardized size */
            padding: 0 !important;
            border-radius: var(--radius-sm) !important; /* REFACTOR: Standardized radius */
        }
        
        /* REFACTOR: Standardized hover to match .ds-row-container delete button */
        button[data-testid*="stButton-key-loc_del_"]:hover {
            color: var(--danger-hover) !important;
            background: rgba(248, 81, 73, 0.15) !important;
            border-color: rgba(248, 81, 73, 0.3) !important;
            box-shadow: var(--shadow-sm) !important;
            transform: scale(1.05); 
        }
        
        button[data-testid*="stButton-key-loc_del_"]:active {
            transform: scale(0.98);
            filter: brightness(0.9);
        }
        
        /* ==================== PREMIUM SPINNER ==================== */
        .stSpinner > div {
            border-color: var(--primary-color) transparent transparent transparent;
            animation: spin 0.8s linear infinite;
        }
        
        /* ==================== PREMIUM DOWNLOAD BUTTON (Kept as large CTA) ==================== */
        /* This button inherits the *base* .stButton style, so it's now 32px height by default */
        /* We override it here to make it a large CTA button again */
        .stDownloadButton > button {
            background: linear-gradient(135deg, var(--success-color), #2ea043);
            border: 1px solid rgba(86, 211, 100, 0.3);
            color: white;
            box-shadow: var(--shadow-sm), 0 0 20px rgba(63, 185, 80, 0.3);
            font-weight: 600;
            transition: all var(--transition-normal);
            
            /* REFACTOR: Restore larger size for this specific button */
            height: auto;
            min-height: 38px;
            font-size: 14px;
            padding: 8px 20px; 
            border-radius: var(--radius-md); /* Restore original radius */
        }
        
        .stDownloadButton > button:hover {
            background: linear-gradient(135deg, var(--success-hover), var(--success-color));
            border-color: var(--success-hover);
            box-shadow: var(--shadow-md), 0 0 30px rgba(63, 185, 80, 0.4);
            transform: translateY(-2px); /* Restore Y transform for large button */
            filter: none; /* Disable base filter */
        }
        
        .stDownloadButton > button:active {
            transform: translateY(0);
            filter: none;
        }
        
        /* ==================== PREMIUM COLUMNS ==================== */
        div[data-testid="column"] {
            padding: var(--spacing-sm);
        }
        
        div[data-testid="column"]:first-child,
        div[data-testid="column"]:last-child {
            background: linear-gradient(135deg, var(--bg-default) 0%, var(--bg-overlay) 100%);
            border-radius: var(--radius-lg);
            padding: var(--spacing-lg);
            border: 1px solid var(--border-default);
            box-shadow: var(--shadow-sm);
            transition: all var(--transition-normal);
            position: relative;
        }
        
        div[data-testid="column"]:hover {
            box-shadow: var(--shadow-md);
            transform: translateY(-2px);
        }
        
        /* ==================== PREMIUM DATAFRAME ==================== */
        [data-testid="stDataFrame"] {
            border-radius: var(--radius-lg);
            overflow: hidden;
            box-shadow: var(--shadow-md);
            border: 1px solid var(--border-default);
        }
        
        [data-testid="stDataFrame"] table {
            background: var(--bg-default);
        }
        
        [data-testid="stDataFrame"] thead {
            background: linear-gradient(180deg, var(--bg-subtle), var(--bg-overlay));
            border-bottom: 2px solid var(--primary-color);
        }
        
        [data-testid="stDataFrame"] th {
            color: var(--text-primary);
            font-weight: 600;
            padding: 12px 16px;
            border-right: 1px solid var(--border-muted);
        }
        
        [data-testid="stDataFrame"] td {
            color: var(--text-secondary);
            padding: 10px 16px;
            border-right: 1px solid var(--border-muted);
            border-bottom: 1px solid var(--border-muted);
        }
        
        [data-testid="stDataFrame"] tbody tr:hover {
            background: rgba(88, 166, 255, 0.08);
        }
        
        /* ==================== PREMIUM SLIDER ==================== */
        .stSlider [data-baseweb="slider"] {
            padding: var(--spacing-md) 0;
        }
        
        .stSlider [data-baseweb="slider"] [role="slider"] {
            background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
            width: 20px;
            height: 20px;
            border: 3px solid var(--bg-canvas);
            box-shadow: var(--shadow-md), 0 0 20px rgba(88, 166, 255, 0.4);
            transition: all var(--transition-normal);
        }
        
        .stSlider [data-baseweb="slider"] [role="slider"]:hover {
            transform: scale(1.2);
            box-shadow: var(--shadow-lg), 0 0 30px rgba(88, 166, 255, 0.6);
        }
        
        .stSlider [data-baseweb="slider"] [role="slider"]:active {
            transform: scale(1.1);
        }
        
        .stSlider [data-baseweb="slider"] [data-testid="stTickBar"] > div {
            background: linear-gradient(90deg, var(--primary-color), var(--primary-hover));
            height: 6px;
            border-radius: 3px;
        }
        
        .stSlider [data-baseweb="slider"] [data-testid="stTickBar"] > div > div {
            background: var(--bg-subtle);
            height: 6px;
            border-radius: 3px;
        }
        
        /* ==================== PREMIUM CHECKBOX & RADIO ==================== */
        .stCheckbox, .stRadio {
            color: var(--text-secondary);
        }
        
        .stCheckbox input[type="checkbox"],
        .stRadio input[type="radio"] {
            width: 20px;
            height: 20px;
            border: 2px solid var(--border-default);
            background: var(--bg-default);
            transition: all var(--transition-normal);
        }
        
        .stCheckbox input[type="checkbox"]:checked,
        .stRadio input[type="radio"]:checked {
            background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
            border-color: var(--primary-color);
            box-shadow: 0 0 16px rgba(88, 166, 255, 0.4);
        }
        
        .stCheckbox input[type="checkbox"]:hover,
        .stRadio input[type="radio"]:hover {
            border-color: var(--primary-color);
            box-shadow: 0 0 0 4px rgba(88, 166, 255, 0.15);
        }
        
        /* ==================== PREMIUM FILE UPLOADER (Kept as large CTA) ==================== */
        [data-testid="stFileUploader"] {
            background: linear-gradient(135deg, var(--bg-default) 0%, var(--bg-overlay) 100%);
            border: 2px dashed var(--border-default);
            border-radius: var(--radius-lg);
            padding: var(--spacing-xl);
            transition: all var(--transition-normal);
            text-align: center;
        }
        
        [data-testid="stFileUploader"]:hover {
            border-color: var(--primary-color);
            background: linear-gradient(135deg, var(--bg-overlay) 0%, var(--bg-default) 100%);
            box-shadow: 0 0 0 4px rgba(88, 166, 255, 0.1), var(--shadow-md);
        }
        
        [data-testid="stFileUploader"] button {
            background: linear-gradient(135deg, var(--primary-active), #1a5bc9);
            border: none;
            color: white;
            padding: 12px 24px;
            border-radius: var(--radius-md);
            font-weight: 600;
            box-shadow: var(--shadow-sm), 0 0 20px rgba(88, 166, 255, 0.3);
            transition: all var(--transition-normal);
        }
        
        [data-testid="stFileUploader"] button:hover {
            background: linear-gradient(135deg, var(--primary-color), var(--primary-active));
            transform: translateY(-2px);
            box-shadow: var(--shadow-md), 0 0 30px rgba(88, 166, 255, 0.4);
        }
        
        /* ==================== PREMIUM PROGRESS BAR ==================== */
        .stProgress > div > div {
            background: var(--bg-subtle);
            border-radius: 10px;
            height: 12px;
            overflow: hidden;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .stProgress > div > div > div {
            background: linear-gradient(90deg, var(--primary-color), var(--primary-hover), var(--primary-color));
            background-size: 200% 100%;
            animation: shimmer 2s linear infinite;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(88, 166, 255, 0.5);
        }
        
        /* ==================== PREMIUM DIVIDER ==================== */
        hr {
            border: none;
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--border-default), transparent);
            margin: var(--spacing-lg) 0;
            position: relative;
        }
        
        hr::before {
            content: '';
            position: absolute;
            top: -1px;
            left: 50%;
            transform: translateX(-50%);
            width: 60px;
            height: 4px;
            background: linear-gradient(90deg, var(--primary-color), var(--primary-hover));
            border-radius: 2px;
            box-shadow: 0 0 20px rgba(88, 166, 255, 0.5);
        }
        
        /* ==================== FIX OVERFLOW ==================== */
        [data-testid="stVerticalBlock"],
        [data-testid="stHorizontalBlock"],
        div[data-testid="column"],
        [data-testid="stContainer"],
        .main,
        .block-container,
        [data-testid="stForm"],
        .element-container,
        .stSelectbox > div,
        .stMultiSelect > div,
        [data-testid="stExpander"],
        [data-testid="stExpander"] details,
        [data-testid="stExpander"] .streamlit-expanderContent {
            overflow: visible !important;
        }
        
        /* ==================== FOCUS STATES ==================== */
        *:focus-visible {
            outline: none !important;
        }
        
        *:focus {
            outline: none !important;
        }
        
        /* Custom focus for interactive elements */
        .stButton > button:focus-visible,
        .stTextInput input:focus-visible,
        .stTextArea textarea:focus-visible {
            outline: none !important;
        }
        
        /* ==================== PREMIUM LINKS ==================== */
        a {
            color: var(--text-link);
            text-decoration: none;
            position: relative;
            transition: color var(--transition-fast);
        }
        
        a::after {
            content: '';
            position: absolute;
            bottom: -2px;
            left: 0;
            width: 0;
            height: 2px;
            background: linear-gradient(90deg, var(--primary-color), var(--primary-hover));
            transition: width var(--transition-normal);
        }
        
        a:hover {
            color: var(--primary-hover);
        }
        
        a:hover::after {
            width: 100%;
        }
        
        /* ==================== PREMIUM TOOLTIPS ==================== */
        [data-testid="stTooltipIcon"] {
            color: var(--text-tertiary);
            transition: all var(--transition-fast);
        }
        
        [data-testid="stTooltipIcon"]:hover {
            color: var(--primary-color);
            transform: scale(1.1);
        }
        
        /* ==================== MARKDOWN CONTAINERS ==================== */
        .main .stMarkdownContainer {
            animation: fadeIn 0.5s ease-out;
        }
        
        /* ==================== RESPONSIVE DESIGN ==================== */
        @media (max-width: 768px) {
            .main {
                padding: var(--spacing-md);
            }
            
            .main h1 { font-size: 2.5rem; }
            .main h2 { font-size: 1.5rem; }
            .main h3 { font-size: 1.25rem; }
            
            div[data-testid="column"] {
                margin-bottom: var(--spacing-md);
            }
        }
        
        /* ==================== HIDE STREAMLIT BRANDING ==================== */
        footer {visibility: hidden;}
        
        /* ==================== PREMIUM BADGE STYLE ==================== */
        .stMarkdown span[style*="background"] {
            background: linear-gradient(135deg, rgba(88, 166, 255, 0.2), rgba(88, 166, 255, 0.1)) !important;
            border: 1px solid rgba(88, 166, 255, 0.3);
            padding: 4px 12px;
            border-radius: var(--radius-sm);
            font-weight: 600;
            font-size: 12px;
            box-shadow: 0 2px 8px rgba(88, 166, 255, 0.2);
        }
        
        /* ==================== LOADING OVERLAY ==================== */
        .stSpinner {
            position: relative;
        }
        
        .stSpinner::before {
            content: '';
            position: fixed;
            inset: 0;
            background: rgba(13, 17, 23, 0.8);
            backdrop-filter: blur(4px);
            z-index: 9999;
            animation: fadeIn 0.3s ease-out;
        }
        
        /* ==================== GLASS MORPHISM EFFECT ==================== */
        .glass-effect {
            background: rgba(22, 27, 34, 0.7) !important;
            backdrop-filter: blur(12px) saturate(180%);
            border: 1px solid rgba(48, 54, 61, 0.5);
            box-shadow: 
                0 8px 32px rgba(0, 0, 0, 0.4),
                inset 0 1px 0 rgba(255, 255, 255, 0.05);
        }
        
        /* ==================== HOVER GLOW EFFECT ==================== */
        .glow-on-hover:hover {
            box-shadow: 
                0 0 20px rgba(88, 166, 255, 0.4),
                0 0 40px rgba(88, 166, 255, 0.2),
                0 0 60px rgba(88, 166, 255, 0.1);
        }

        /* ==================== ALWAYS SHOW SIDEBAR COLLAPSE BTN ==================== */
        /* Target the button inside the sidebar header */
        [data-testid="stSidebar"] button[kind="header"] {
            opacity: 1 !important; /* Make it always visible */
            transition: background-color 0.2s ease-in-out, color 0.2s ease-in-out !important; /* Smooth transition for hover */
            background-color: var(--bg-subtle); /* Give it a subtle background */
            color: var(--text-secondary); /* Set initial color */
            border: 1px solid var(--border-default); /* Add a border */
            border-radius: var(--radius-sm); /* Slightly rounded corners */
            margin-right: 5px; /* Add some space */
        }

        /* Optional: Add hover effect for better feedback */
        [data-testid="stSidebar"] button[kind="header"]:hover {
            background-color: var(--primary-color); /* Change background on hover */
            color: white; /* Change icon color on hover */
            border-color: var(--primary-hover);
        }

        /* Ensure icon inside is also always visible if needed */
        [data-testid="stSidebar"] button[kind="header"] svg {
            opacity: 1 !important;
        }
        
        /* ==================== PREMIUM FORM (Kept as large CTA) ==================== */
        [data-testid="stForm"] {
            background: linear-gradient(135deg, var(--bg-default) 0%, var(--bg-overlay) 100%);
            border: 1px solid var(--border-default);
            border-radius: var(--radius-lg);
            padding: var(--spacing-lg);
            box-shadow: var(--shadow-md);
        }
        
        [data-testid="stForm"] button[type="submit"] {
            background: linear-gradient(135deg, var(--primary-active), #1a5bc9);
            border: none;
            color: white;
            width: 100%;
            padding: 14px;
            font-weight: 600;
            font-size: 15px;
            box-shadow: var(--shadow-sm), 0 0 20px rgba(88, 166, 255, 0.3);
            transition: all var(--transition-normal);
            border-radius: var(--radius-md); /* Use standard radius */
        }
        
        [data-testid="stForm"] button[type="submit"]:hover {
            background: linear-gradient(135deg, var(--primary-color), var(--primary-active));
            transform: translateY(-2px);
            box-shadow: var(--shadow-md), 0 0 30px rgba(88, 166, 255, 0.4);
            filter: none;
        }
        

        /* ==================== DATA SOURCE TABLE - ENHANCED VISIBILITY ==================== */
        /* Font Awesome for Icons */
        @import url('https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css');
        
        /* Table Container */
        .ds-table-wrapper {
            background: var(--bg-overlay, #1c2128);
            border: 1px solid rgba(88, 166, 255, 0.2);
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: var(--spacing-md, 1rem);
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
        }
        
        /* Table Header - Highly Visible */
        .ds-table-header {
            background: linear-gradient(135deg, #2d3748 0%, #1e293b 100%);
            border-bottom: 2px solid var(--primary-color, #58a6ff);
            padding: 1rem 1.5rem;
            display: grid;
            grid-template-columns: 2.5fr 2.5fr 2fr 1.5fr 0.5fr;
            gap: 1rem;
            align-items: center;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
        }
        
        .ds-header-item {
            color: var(--primary-hover, #79c0ff);
            font-weight: 700;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.1em;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
        }
        
        .ds-header-item i {
            color: var(--primary-color, #58a6ff);
            font-size: 1.1rem;
            filter: drop-shadow(0 0 4px rgba(88, 166, 255, 0.4));
        }
        
        .ds-header-item:last-child {
            justify-content: center;
        }

        /* Row Wrapper - Better Separation */
        .ds-row-wrapper {
            padding: 0.85rem 1.5rem;
            border-bottom: 1px solid rgba(48, 54, 61, 0.5);
            transition: all 0.2s ease;
            background: var(--bg-default, #161b22);
        }
        
        .ds-row-wrapper:hover {
            background: linear-gradient(90deg, rgba(88, 166, 255, 0.08) 0%, rgba(88, 166, 255, 0.04) 100%);
            border-bottom-color: rgba(88, 166, 255, 0.3);
            box-shadow: inset 0 0 20px rgba(88, 166, 255, 0.05);
        }
        
        .ds-row-wrapper:last-child {
            border-bottom: none;
        }

        /* Imported Data Boxes - High Contrast */
        .imported-data-box {
            background: linear-gradient(135deg, #2d3748 0%, #1e293b 100%);
            border: 1px solid rgba(88, 166, 255, 0.3);
            border-left: 3px solid var(--primary-color, #58a6ff);
            padding: 0.6rem 1rem;
            border-radius: 6px;
            color: var(--text-primary, #e6edf3);
            font-family: 'SFMono-Regular', 'Consolas', 'Monaco', monospace;
            font-size: 0.9rem;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05);
        }
        
        .imported-status-box {
            background: linear-gradient(135deg, rgba(88, 166, 255, 0.2), rgba(88, 166, 255, 0.1));
            border: 1px solid rgba(88, 166, 255, 0.4);
            padding: 0.6rem 1rem;
            border-radius: 6px;
            color: var(--primary-hover, #79c0ff);
            font-size: 0.85rem;
            font-style: italic;
            text-align: center;
            font-weight: 600;
            box-shadow: 0 2px 8px rgba(88, 166, 255, 0.2);
        }

        /* Input Fields - High Contrast & Visibility */
        .ds-row-wrapper .stTextInput input,
        .ds-row-wrapper .stSelectbox > div > div {
            background: linear-gradient(135deg, #2d3748, #1e293b) !important;
            border: 1.5px solid rgba(88, 166, 255, 0.25) !important;
            border-radius: 6px !important;
            color: var(--text-primary, #e6edf3) !important;
            font-size: 0.9rem !important;
            padding: 0.6rem 1rem !important;
            transition: all 0.2s ease !important;
            height: 38px !important;
            min-height: 38px !important;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
            font-weight: 500 !important;
        }
        
        .ds-row-wrapper .stTextInput input:hover,
        .ds-row-wrapper .stSelectbox > div > div:hover {
            border-color: var(--primary-color, #58a6ff) !important;
            box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.15), 0 2px 8px rgba(0, 0, 0, 0.3) !important;
            background: linear-gradient(135deg, #334155, #1e293b) !important;
        }
        
        .ds-row-wrapper .stTextInput input:focus,
        .ds-row-wrapper .stSelectbox > div > div:focus-within {
            background: linear-gradient(135deg, #334155, #2d3748) !important;
            border-color: var(--primary-hover, #79c0ff) !important;
            box-shadow: 0 0 0 3px rgba(88, 166, 255, 0.25), 0 4px 12px rgba(88, 166, 255, 0.3) !important;
            outline: none !important;
        }

        /* * REFACTOR: The following button styles for .ds-row-wrapper were removed
         * as they are now superseded by the .ds-row-container styles below.
         *
         * .ds-row-wrapper .stButton > button { ... }
         * .ds-row-wrapper .stButton > button:hover { ... }
         * .ds-row-wrapper .stButton > button[kind="secondary"] { ... }
         * .ds-row-wrapper .stButton > button[kind="secondary"]:hover { ... }
         */

        /* Spacing & Layout */
        .ds-row-wrapper div[data-testid="stHorizontalBlock"] {
            gap: 1rem !important;
        }
        
        .ds-row-wrapper div[data-testid="stHorizontalBlock"] > div {
            padding: 0 !important;
        }
        
        /* Section Headings */
        .ds-section-title {
            font-size: 1.3rem;
            color: var(--text-primary, #e6edf3);
            margin-bottom: 1rem;
            font-weight: 700;
            letter-spacing: -0.02em;
        }
        
        .ds-section-subtitle {
            font-size: 1.05rem;
            color: var(--primary-color, #58a6ff);
            margin-bottom: 1rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        /* Row Animation */
        .ds-row-wrapper {
            animation: slideIn 0.3s ease-out;
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateX(-20px);
            }
            to {
                opacity: 1;
                transform: translateX(0);
            }
        }
        
        /* Placeholder Styling */
        .ds-row-wrapper .stTextInput input::placeholder {
            color: rgba(139, 148, 158, 0.6) !important;
            font-style: italic;
        }
        
        /* Selectbox Icon */
        .ds-row-wrapper .stSelectbox [data-baseweb="select"] svg {
            color: var(--primary-color, #58a6ff) !important;
            filter: drop-shadow(0 0 2px rgba(88, 166, 255, 0.3));
        }
        
        /* Fix: Prevent duplicate headers */
        .ds-row-wrapper .ds-table-header {
            display: none !important;
        }

        /* New Row Highlight - When just added */
        .ds-row-wrapper:last-of-type {
            animation: highlightNew 2s ease-out;
        }
        
        @keyframes highlightNew {
            0% {
                background: rgba(88, 166, 255, 0.2);
                box-shadow: inset 0 0 20px rgba(88, 166, 255, 0.3);
            }
            100% {
                background: transparent;
                box-shadow: none;
            }
        }
        
        /* Disabled Export Button Style */
        .ds-row-wrapper [style*="cursor: not-allowed"] {
            opacity: 0.6;
            transition: all 0.3s ease;
        }
        
        .ds-row-wrapper [style*="cursor: not-allowed"]:hover {
            opacity: 0.8;
        }
        
        /* Required Field Warning */
        .ds-row-wrapper div[style*="color: #d29922"] {
            animation: fadeIn 0.3s ease-out;
        }
        
        /* Better Placeholder Styling */
        .ds-row-wrapper .stTextInput input:not(:focus)::placeholder {
            color: rgba(139, 148, 158, 0.4) !important;
        }
        
        .ds-row-wrapper .stTextInput input:focus::placeholder {
            color: rgba(139, 148, 158, 0.6) !important;
            transform: translateY(-2px);
            transition: all 0.3s ease;
        }
        
        /* Empty Input Visual Cue */
        .ds-row-wrapper .stTextInput input:placeholder-shown {
            border-left: 3px solid rgba(210, 153, 34, 0.3) !important;
        }
        
        .ds-row-wrapper .stTextInput input:not(:placeholder-shown) {
            border-left: 3px solid rgba(88, 166, 255, 0.5) !important;
        }
        

    /* ==================== DATA SOURCE ROW BUTTONS (Kept as is - Good minimal style) ==================== */
        /* Base style for ALL buttons within the row container - MINIMAL */
        .ds-row-container .stButton button {
             background: none !important;
             border: 1px solid transparent !important; /* Keep border transparent */
             color: var(--text-tertiary) !important; /* Dim color */
             width: auto !important;
             height: 32px !important;  /* Slightly smaller height */
             min-height: 32px !important;
             padding: 0 0.5rem !important; /* Consistent padding */
             font-size: 0.9rem !important;
             border-radius: var(--radius-sm) !important;
             transition: all 0.15s ease-in-out !important;
             display: flex;
             justify-content: center;
             align-items: center;
             box-shadow: none !important;
             line-height: 1 !important;
        }

        /* Hover effect for ALL buttons */
        .ds-row-container .stButton button:hover {
             transform: scale(1.05); /* Slight scale */
             border: 1px solid var(--border-default) !important; /* Add subtle border */
             box-shadow: var(--shadow-sm) !important; /* Add subtle shadow */
        }

        /* Active state for ALL buttons */
         .ds-row-container .stButton button:active {
             transform: scale(0.98);
             filter: brightness(0.9); /* Slightly darken on click */
         }

        /* --- Specific Hover Styles --- */
        /* Export Button Hover */
        .ds-row-container .stButton button[help="Generate/Export Code"]:hover {
             background: rgba(88, 166, 255, 0.15) !important; /* Blue background */
             color: var(--primary-hover) !important; /* Brighter blue text/icon */
             border-color: rgba(88, 166, 255, 0.3) !important;
        }

        /* Delete Button Hover */
        .ds-row-container .stButton button[help="Delete Link"]:hover {
             background: rgba(248, 81, 73, 0.15) !important; /* Red background */
             color: var(--danger-hover) !important; /* Brighter red icon */
             border-color: rgba(248, 81, 73, 0.3) !important;
        }

        /* --- Specific Width for Icon-Only Button --- */
        .ds-row-container .stButton button[help="Delete Link"] {
             min-width: 32px !important; /* Ensure minimum width for the icon */
             width: 32px !important; /* Fixed width for icon button */
             padding: 0 !important; /* No padding for icon button */
             font-size: 1rem !important; /* Reset icon size if needed */
        }
    /* ==================== END DATA SOURCE ROW BUTTONS ==================== */


/* ==================== TEST FLOW TOOLBAR BUTTONS (Boxed Style - High Specificity) ==================== */
        /* Wrapper */
        .step-card-toolbar {
            display: flex;
            justify-content: flex-end;
            align-items: center;
            gap: 0.4rem !important;
            padding: 0 !important;
            margin: 0 !important;
        }

        /* Target the button container more specifically */
        .step-card-toolbar div[data-testid="stVerticalBlock"] div[data-testid="stHorizontalBlock"] div[data-testid="column"] .stButton {
            width: 32px !important;
            height: 32px !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        /* Target the button itself with high specificity */
        .step-card-toolbar div[data-testid="stVerticalBlock"] div[data-testid="stHorizontalBlock"] div[data-testid="column"] .stButton button {
            width: 32px !important;
            height: 32px !important;
            min-width: 32px !important;
            min-height: 32px !important;
            padding: 0 !important;
            margin: 0 !important;
            font-size: 0.9rem !important;
            line-height: 1 !important;
            border-radius: 6px !important; /* Rounded corners */
            
            /* Boxed appearance */
            background: var(--bg-subtle) !important; /* Dark background */
            border: 1px solid var(--border-default) !important; /* Visible border */
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
            
            color: var(--text-secondary) !important;
            display: flex !important;
            justify-content: center !important;
            align-items: center !important;
            overflow: hidden;
            transition: all 0.2s ease !important;
        }

        /* Hover effects */
        .step-card-toolbar div[data-testid="stVerticalBlock"] div[data-testid="stHorizontalBlock"] div[data-testid="column"] .stButton button:hover {
            background: var(--bg-overlay) !important;
            border-color: var(--primary-color) !important;
            color: var(--primary-hover) !important;
            box-shadow: 0 2px 8px rgba(88, 166, 255, 0.3), inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
            transform: translateY(-1px);
        }

        /* Active state */
        .step-card-toolbar div[data-testid="stVerticalBlock"] div[data-testid="stHorizontalBlock"] div[data-testid="column"] .stButton button:active {
            transform: translateY(0) scale(0.98);
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3) !important;
        }

        /* Icon sizing */
        .step-card-toolbar div[data-testid="stVerticalBlock"] div[data-testid="stHorizontalBlock"] div[data-testid="column"] .stButton button i,
        .step-card-toolbar div[data-testid="stVerticalBlock"] div[data-testid="stHorizontalBlock"] div[data-testid="column"] .stButton button svg {
            font-size: inherit !important;
            width: 1em;
            height: 1em;
        }
/* ==================== END TEST FLOW TOOLBAR BUTTONS ==================== */

/* --- Clean up unnecessary column styles ONLY FOR TOOLBAR --- */
/* (Keep FORCE KILL block for other potential issues if needed, but clean it for toolbar) */

        .step-card-toolbar [data-testid="column"],
        .step-card-toolbar div[class*="e8vg11g"],
        .step-card-toolbar div[class*="st-emotion-cache"] {
            background: none !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            margin: 0 !important;
            /* Explicitly set column width for toolbar context */
            min-width: 0 !important;
            width: auto !important; /* Allow flexbox to manage width based on button */
            flex: 0 0 auto !important; /* Don't grow or shrink, take minimum space */
        }

        .step-card-toolbar [data-testid="column"]:hover,
        .step-card-toolbar div[class*="e8vg11g"]:hover,
        .step-card-toolbar div[class*="st-emotion-cache"]:hover {
            background: none !important;
            border: none !important;
            box-shadow: none !important;
            transform: none !important;
        }

        .step-card-toolbar [data-testid="column"] > div,
        .step-card-toolbar div[class*="e8vg11g"] > div {
            background: none !important;
            border: none !important;
            box-shadow: none !important;
            padding: 0 !important;
            /* Ensure inner div doesn't force width */
            width: auto !important;
            height: auto !important;
        }
        
        /* ===== STEP CARD CAPTION FIX ===== */
        /* ✅ เพิ่มส่วนนี้เข้ามาเพื่อแก้ไขสีของ arguments */
        .step-card .stCaption,
        .step-card .stCaption *,
        div[data-testid="stVerticalBlock"] .step-card .stCaption,
        div[data-testid="stVerticalBlock"] .step-card .stCaption * {
            color: #58a6ff !important;
            font-size: 0.8rem !important;
            font-family: 'SF Mono', Monaco, 'Courier New', monospace !important;
        }
    </style>
    """