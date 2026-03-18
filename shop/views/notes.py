from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods

from ..repositories.note import UserNoteRepository
from ..repositories.log import LogRepository


def _require_auth(request):
    return request.session.get('user_id')


def user_notes_view(request):
    user_id = _require_auth(request)
    if not user_id:
        return redirect('login')

    notes = UserNoteRepository.get_by_user(user_id)
    return render(request, 'users/notes.html', {'notes': notes})


@require_http_methods(["POST"])
def create_note_view(request):
    user_id = _require_auth(request)
    if not user_id:
        return redirect('login')

    title = request.POST.get('title', '').strip()
    content = request.POST.get('content', '').strip()

    if not title or not content:
        messages.error(request, 'Title and content are required.')
        return redirect('user_notes')

    UserNoteRepository.create(user_id, title, content)
    LogRepository.log_action(user_id, 'NOTE_CREATED', {'title': title}, 'SUCCESS')
    messages.success(request, 'Note created.')
    return redirect('user_notes')


@require_http_methods(["POST"])
def update_note_view(request, note_id):
    user_id = _require_auth(request)
    if not user_id:
        return redirect('login')

    note = UserNoteRepository.get_by_id(note_id)
    if not note or str(note['user_id']) != user_id:
        messages.error(request, 'Access denied.')
        return redirect('user_notes')

    title = request.POST.get('title', '').strip()
    content = request.POST.get('content', '').strip()

    UserNoteRepository.update(note_id, title, content)
    LogRepository.log_action(user_id, 'NOTE_UPDATED', {'note_id': note_id}, 'SUCCESS')
    messages.success(request, 'Note updated.')
    return redirect('user_notes')


@require_http_methods(["POST"])
def delete_note_view(request, note_id):
    user_id = _require_auth(request)
    if not user_id:
        return redirect('login')

    note = UserNoteRepository.get_by_id(note_id)
    if not note or str(note['user_id']) != user_id:
        messages.error(request, 'Access denied.')
        return redirect('user_notes')

    UserNoteRepository.delete(note_id)
    LogRepository.log_action(user_id, 'NOTE_DELETED', {'note_id': note_id}, 'SUCCESS')
    messages.success(request, 'Note deleted.')
    return redirect('user_notes')
