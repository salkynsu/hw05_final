from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, User, Follow
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page


TEXT: str = 'Последние обновления на сайте'
FOLLOW_TEXT: str = 'Лента'
POSTS_QUANTITY: int = 10
TIMEOUT: int = 20


@cache_page(TIMEOUT)
def index(request):
    """Показывает главную страницу со всеми постами всех авторов."""
    template_name = 'posts/index.html'
    post_list = Post.objects.select_related('author', 'group').all()
    paginator = Paginator(post_list, POSTS_QUANTITY)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'text': TEXT,
        'page_obj': page_obj,
    }
    return render(request, template_name, context)


def gpoup_list(request, slug):
    """Показывает посты выбранной группы."""
    template_name = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    description = group.description
    post_list = group.posts.select_related("author")
    paginator = Paginator(post_list, POSTS_QUANTITY)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'text': f'Записи сообщества {group.__str__()}',
        'description': description,
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template_name, context)


def profile(request, username):
    """Показывает посты выбранного автора."""
    template_name = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    user=request.user
    if (
        user.is_authenticated
        and author != user
        and Follow.objects.filter(user=user, author=author).exists()
    ):
        following = True
    else:
        following = False
    post_list = author.posts.select_related('group')
    paginator = Paginator(post_list, POSTS_QUANTITY)
    count = paginator.count
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'count': count,
        'author': author,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, template_name, context)


def post_detail(request, post_id):
    """Показывает страницу с детальной информацией о посте."""
    template_name = 'posts/post_detail.html'
    post = get_object_or_404(Post, id=post_id)
    post_list = Post.objects.filter(author_id=post.author).all()
    comments = post.comments.all()
    form = CommentForm(request.POST or None)
    count = post_list.count()
    context = {
        'count': count,
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, template_name, context)


@login_required
def post_create(request):
    """Создать новый пост."""
    template_name = 'posts/create_post.html'
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        username = post.author.username
        return redirect('posts:profile', username)
    return render(request, template_name, {'form': form})


def post_edit(request, post_id):
    """Редактировать уже существующий пост."""
    template_name = 'posts/create_post.html'
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if post.author == request.user:
        if form.is_valid():
            post = form.save()
            return redirect('posts:post_detail', post_id)
        return render(request, template_name, {'form': form, 'is_edit': True})
    return redirect('posts:post_detail', post_id)


@login_required
def add_comment(request, post_id):
    """Добавить комментарий к посту."""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Показывает посты авторов, на которых подписан пользователь."""
    # информация о текущем пользователе доступна в переменной request.user
    template_name = 'posts/follow.html'
    authors = Follow.objects.filter(user=request.user).values('author')
    post_list = Post.objects.filter(author__in=authors).all()
    paginator = Paginator(post_list, POSTS_QUANTITY)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'text': FOLLOW_TEXT,
        'following': True,
        'page_obj': page_obj,
    }
    return render(request, template_name, context)


@login_required
def profile_follow(request, username):
    """Подписаться на выбранного автора."""
    author = get_object_or_404(User, username=username)
    user = request.user
    if (
        author != user
        and not Follow.objects.filter(author=author, user=user).exists()
    ):
        Follow.objects.create(author=author, user=user)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    """Отписаться от выбранного автора."""
    author = get_object_or_404(User, username=username)
    user = request.user
    if (
        author != user
        and Follow.objects.filter(author=author, user=user).exists()
    ):
        follow = Follow.objects.get(author=author, user=user)
        follow.delete()
    return redirect('posts:profile', username)
