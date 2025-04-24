from django import template

register = template.Library()

@register.filter(name='get_start_time')
def get_start_time(d, k):
    """
    Returns the start time for a given day in the timetable.
    Usage: {{ timeTable|get_start_time:'Monday' }}
    """
    try:
        return d[k][0]
    except (KeyError, IndexError, TypeError):
        return ""

@register.filter(name='get_end_time')
def get_end_time(d, k):
    """
    Returns the end time for a given day in the timetable.
    Usage: {{ timeTable|get_end_time:'Monday' }}
    """
    try:
        return d[k][1]
    except (KeyError, IndexError, TypeError):
        return ""

@register.filter
def get_item_link(dictionary, key):
    """
    Returns the link (first item) from the assignment submission array.
    """
    try:
        if key in dictionary:
            return dictionary[key][0]  # Return the first element (link)
        return None
    except (KeyError, IndexError, TypeError):
        return None

@register.filter
def get_date(dictionary, key):
    """
    Returns the date (second item) from the assignment submission array.
    """
    try:
        if key in dictionary:
            return dictionary[key][1]  # Return the second element (date)
        return None
    except (KeyError, IndexError, TypeError):
        return None 