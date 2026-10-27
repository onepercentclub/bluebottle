def can_hijack(*, hijacker, hijacked):
    if not hijacker or not hijacked:
        return False
    if not hijacked.is_active:
        return False
    if not hijacker.is_superuser:
        return False
    if hijacker.pk == hijacked.pk:
        return False
    if hijacked.is_superuser:
        return False
    return hijacked.is_staff
