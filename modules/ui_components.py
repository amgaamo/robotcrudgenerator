import streamlit as st
import base64

def render_header():
    """Render main header with enhanced description"""
    header_html = """
    <div style='text-align: center; padding: 0.5rem 0 0.1rem 0;'>
        <h1 class='app-header-title'>
            <i class='bi bi-robot'></i> Robot Framework Code Generator
        </h1>
        <p style='color: var(--text-muted); font-size: 1rem; margin: 0; line-height: 1.5;'>
            ⚡ <strong>Automate locator generation</strong> · 
            🎯 <strong>Create CRUD tests instantly</strong> · 
            🚀 <strong>Boost productivity</strong>
        </p>
        <br>
    </div>
    """
    st.markdown(header_html, unsafe_allow_html=True)

def copy_button_component(text_to_copy, button_key):
    """
    Ultimate Modern Copy Button - Original beautiful design.
    """
    text_bytes = text_to_copy.encode('utf-8')
    b64_text = base64.b64encode(text_bytes).decode()

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.3/font/bootstrap-icons.min.css">
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            html, body {{
                width: 100%; height: 100%;
                background: transparent !important;
                overflow: hidden;
                display: flex; justify-content: center; align-items: center;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            }}
            .copy-button {{
                width: 34px; height: 34px;
                padding: 0;
                background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
                border: 1.5px solid #334155;
                border-radius: 10px;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.1);
                color: #94a3b8;
                font-size: 0.9rem;
                display: flex; justify-content: center; align-items: center;
                cursor: pointer;
                transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                position: relative;
                user-select: none; -webkit-user-select: none;
            }}
            .copy-button:hover {{
                background: linear-gradient(135deg, #6366f1 0%, #4f46e5 100%);
                color: #ffffff;
                transform: translateY(-3px) scale(1.05);
                box-shadow: 0 8px 24px rgba(99, 102, 241, 0.5), 0 0 0 4px rgba(99, 102, 241, 0.2);
            }}
            .copy-button:active {{
                transform: translateY(-1px) scale(0.98);
                box-shadow: 0 4px 12px rgba(99, 102, 241, 0.4);
            }}
            .copy-button.success {{
                background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
                color: #ffffff !important;
                box-shadow: 0 0 30px rgba(16, 185, 129, 0.6), 0 0 0 4px rgba(16, 185, 129, 0.2) !important;
                animation: successPop 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            }}
            @keyframes successPop {{ 0% {{ transform: scale(1); }} 50% {{ transform: scale(1.2); }} 100% {{ transform: scale(1); }} }}
            .copy-button i {{ transition: all 0.3s ease; }}
            .copy-button:hover i {{ transform: scale(1.15) rotate(-5deg); }}
        </style>
    </head>
    <body>
        <button class="copy-button" id="{button_key}" aria-label="Copy to clipboard">
            <i class="bi bi-copy"></i>
        </button>
        <script>
            const button = document.getElementById('{button_key}');
            let isProcessing = false;
            button.onclick = async function(e) {{
                e.preventDefault();
                if (isProcessing) return;
                isProcessing = true;
                const text = atob('{b64_text}');
                try {{
                    await navigator.clipboard.writeText(text);
                    button.classList.add('success');
                    button.innerHTML = '<i class="bi bi-check-lg"></i>';
                    setTimeout(() => {{
                        button.classList.remove('success');
                        button.innerHTML = '<i class="bi bi-copy"></i>';
                        isProcessing = false;
                    }}, 1500);
                }} catch (err) {{
                    console.error('Copy failed:', err);
                }}
            }};
        </script>
    </body>
    </html>
    """
    return html