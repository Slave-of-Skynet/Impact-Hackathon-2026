from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls import Resolver404, resolve
from django.utils.cache import add_never_cache_headers

from . import parent_session
from .authz import ACTIVE_CHILD_KEY, MODE_KEY, active_child_reader, is_child_mode, is_htmx

# authorization.md: the only routes a child-mode session may reach. Matched on view_name (namespaced),
# so admin's "admin:login" never matches; every route not listed here, including future ones, is refused.
CHILD_ALLOWED = frozenset({
    "child_home", "catalog", "book_detail", "add_to_shelf", "my_shelf", "shelf_entry", "record_progress",
    "finish_book", "rate_book", "achievements", "club_corner", "pin_gate", "logout", "offline", "manifest", "sw",
    "book_reflection", "start_reflection", "save_reflection",
    "parent_return", "parent_lock",
})
# Reachable even when the child is gone: PIN recovery, safe Lock (logout), or sign out.
ALWAYS_ALLOWED = frozenset({"pin_gate", "parent_lock", "logout"})


class ChildModeMiddleware:
    """Deny by default in child mode. Must run after AuthenticationMiddleware."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if is_child_mode(request):
            if not request.user.is_authenticated:
                # Adult session already gone: nothing left to protect, and login must stay reachable.
                request.session.pop(MODE_KEY, None)
                request.session.pop(ACTIVE_CHILD_KEY, None)
                parent_session.revoke(request)
            elif not self._allowed(request):
                if is_htmx(request):
                    return HttpResponse(status=403)
                return redirect("pin_gate")
        response = self.get_response(request)
        if getattr(request, "_parent_controls_rendered", False):
            # Preserve an already-private no-store page's established header.
            policy = response.get("Cache-Control", "")
            if "private" not in policy or "no-store" not in policy:
                add_never_cache_headers(response)
        return response

    def _allowed(self, request):
        try:
            name = resolve(request.path_info, getattr(request, "urlconf", None)).view_name
        except Resolver404:
            return False
        if name in ALWAYS_ALLOWED:
            return True
        # A deleted/foreign active child fails closed; safe Lock can only sign out.
        return name in CHILD_ALLOWED and active_child_reader(request) is not None
