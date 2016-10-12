

# Access to the pledge payment method is restricted to members
# who have the can_pledge option.
def method_access_handler(member, *args, **kwargs):
    try:
        return member.can_pledge
    except AttributeError:
        return False
