from datetime import datetime

def get_today_str() -> str:
    """Get current date in a human-readable format.
    
    Returns:
        Current date formatted as 'Day Mon DD, YYYY' (e.g., 'Mon Jan 01, 2023')
    """
    try:
        # Try Linux/Unix format first
        return datetime.now().strftime("%a %b %-d, %Y")
    except ValueError:
        # Fall back to Windows format if Linux format fails
        return datetime.now().strftime("%a %b %#d, %Y")


