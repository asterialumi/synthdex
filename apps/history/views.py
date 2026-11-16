"""Views for search history presentation and management."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .models import SearchHistory


@login_required(login_url='login:login')
def history_list_view(request):
    """List the authenticated user's search history, ordered newest first."""
    history_entries = (
        SearchHistory.objects.filter(user=request.user)
        .select_related('search_cache')
        .order_by('-searched_at')
    )

    return render(request, 'history/history.html', {
        'history_entries': history_entries,
    })


@login_required(login_url='login:login')
@require_POST
def clear_history_view(request):
    """Clear all search history entries for the authenticated user."""
    deleted_count, _ = SearchHistory.objects.filter(user=request.user).delete()
    if deleted_count > 0:
        messages.success(request, 'Your search history has been cleared.')
    else:
        messages.info(request, 'Your search history is already empty.')

    return redirect('history:list')
