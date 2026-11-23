"""Views for search history presentation and management."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from .models import SearchHistory


@login_required(login_url='login:login')
def history_list_view(request):
    """List the authenticated user's search history, grouped consecutively."""
    raw_entries = (
        SearchHistory.objects.filter(user=request.user)
        .select_related('search_cache')
        .order_by('-searched_at')
    )

    grouped_entries = []
    for entry in raw_entries:
        query_norm = entry.query.strip().casefold()
        if (
            grouped_entries
            and grouped_entries[-1]['query_norm'] == query_norm
            and grouped_entries[-1]['search_type'] == entry.search_type
        ):
            grouped_entries[-1]['count'] += 1
        else:
            grouped_entries.append({
                'entry': entry,
                'query': entry.query,
                'query_norm': query_norm,
                'search_type': entry.search_type,
                'search_type_display': entry.get_search_type_display(),
                'searched_at': entry.searched_at,
                'search_cache': entry.search_cache,
                'count': 1,
            })

    return render(request, 'history/history.html', {
        'history_entries': grouped_entries,
        'total_count': len(raw_entries),
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
