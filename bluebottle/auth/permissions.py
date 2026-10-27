def can_hijack(*, hijacker, hijacked):
    """Superusers may impersonate active staff members, but not other superusers."""
    if not hijacked.is_active:
        return False
    if not hijacker.is_superuser:
        return False
    if hijacker.pk == hijacked.pk:
        return False
    if hijacked.is_superuser:
        return False
    return hijacked.is_staff
