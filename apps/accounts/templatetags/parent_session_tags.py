from django import template

from apps.accounts import parent_session
from apps.accounts.authz import ACTIVE_CHILD_KEY, is_child_mode

register = template.Library()


@register.simple_tag(takes_context=True)
def parent_session_status(context):
    request = context.get("request")
    if request is None or not getattr(request, "user", None) or not request.user.is_authenticated:
        return {}
    children = list(request.user.children.order_by("created_at", "pk"))
    child_mode = is_child_mode(request)
    until = parent_session.verified_until(request)
    active = any(str(child.public_id) == request.session.get(ACTIVE_CHILD_KEY) for child in children)
    if child_mode and not active:
        parent_session.revoke(request)
        until = None
    if not children and not child_mode and until is None:
        return {}
    # Shared layouts also render on public URLs. Personal controls must not cache.
    request._parent_controls_rendered = True
    return {"show": True, "trusted": until is not None, "until": until,
            "child_mode": child_mode, "can_return": child_mode and active and until is not None,
            "children": children}
