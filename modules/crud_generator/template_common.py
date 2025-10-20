"""
Common Helper Functions for All Templates
Shared utilities used by Create, Update, Delete templates
"""
import uuid

def find_keyword(all_keywords, name):
    """
    Find keyword by exact name match
    
    Args:
        all_keywords: List of keyword definitions
        name: Exact name of the keyword to find
    
    Returns:
        Keyword dict or None
    """
    return next((kw for kw in all_keywords if kw['name'] == name), None)


def find_locator(all_locators, search_terms):
    """
    Find locator by searching for any of the given terms in locator name
    
    Args:
        all_locators: List of locator definitions
        search_terms: List of strings to search for (case-insensitive)
    
    Returns:
        First matching locator dict or None
    """
    if not all_locators:
        return None
    
    return next(
        (loc for term in search_terms 
         for loc in all_locators 
         if term.lower() in loc['name'].lower()), 
        None
    )


def create_step(keyword_name, args, step_type=None, config=None):
    """
    Create a step dictionary with proper structure
    
    Args:
        keyword_name: Name of the Robot Framework keyword
        args: Dictionary of keyword arguments
        step_type: Optional type marker (e.g., 'csv_import', 'api_call')
        config: Optional configuration dictionary
    
    Returns:
        Step dictionary with unique ID
    """
    step = {
        "id": str(uuid.uuid4()),
        "keyword": keyword_name,
        "args": args
    }
    
    if step_type:
        step['type'] = step_type
    
    if config:
        step['config'] = config
    
    return step


def get_form_locators(all_locators):
    """
    Auto-detect form input locators from the locators list
    
    Args:
        all_locators: List of all locator definitions
    
    Returns:
        List of locators that appear to be form inputs
    """
    if not all_locators:
        return []
    
    input_suffixes = ['_INPUT', '_SELECT', '_TEXTAREA', '_DATE', '_FILE']
    
    form_locators = [
        loc for loc in all_locators 
        if any(loc['name'].upper().endswith(suffix) for suffix in input_suffixes)
        and 'SEARCH' not in loc['name'].upper()
    ]
    
    return form_locators