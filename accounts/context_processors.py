def organization(request):
    """Inject the caller's organization into every template context."""
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        return {"org": getattr(user, "organization", None)}
    return {}
