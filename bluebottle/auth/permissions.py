def can_hijack(*, hijacker, hijacked):
    """
    OTP-verified superusers may impersonate active staff members,
    but not other superusers.
    """
    if not hijacked.is_active:
        return False
    if not hijacker.is_superuser:
        return False
    is_verified = getattr(hijacker, 'is_verified', None)
    if not is_verified or not is_verified():
        return False
    if hijacker.pk == hijacked.pk:
        return False
    if hijacked.is_superuser:
        return False
    return hijacked.is_staff
