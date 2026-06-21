"""Context processor to add division info to all templates."""
from core.models import Division


def division_context(request):
    """Add divisions and user division to template context."""
    context = {
        'divisions': Division.objects.all(),
    }
    if request.user.is_authenticated:
        context['user_division'] = request.user.division
    return context
