from django.shortcuts import render


def page_not_found(request, exception):
    """Показывает кастомную страницу 404."""
    # Переменная exception содержит отладочную информацию;
    # выводить её в шаблон пользовательской страницы 404 мы не станем
    return render(request, 'core/404.html', {'path': request.path}, status=404)


def server_error(request):
    """Показывает кастомную страницу 500."""
    return render(request, 'core/500.html', status=500)


def permission_denied(request, exception):
    """Показывает кастомную страницу 403."""
    return render(request, 'core/403.html', status=403)


def csrf_failure(request, reason=''):
    """Показывает кастомную страницу 403 в случае ошибки csrf."""
    return render(request, 'core/403csrf.html')
