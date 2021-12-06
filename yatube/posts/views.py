from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .app_settings import POSTS_PER_PAGE
from .forms import PostForm
from .models import Group, Post, User


def pagination(obj_list, request):
    paginator = Paginator(obj_list, POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return {'page_obj': page_obj}


def index(request):
    template = 'posts/index.html'
    context = pagination(Post.objects.all(), request)
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    template = 'posts/group_list.html'
    context = {'group': group}
    context.update(pagination(group.posts.all(), request))
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    posts_count = post_list.count()
    template = 'posts/profile.html'
    context = {
        'author': author,
        'post_list': post_list,
        'post_count': posts_count,
    }
    context.update(pagination(post_list, request))
    return render(request, template, context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    posts_count = post.author.posts.count()
    template = 'posts/post_detail.html'
    context = {
        'post': post,
        'posts_count': posts_count,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None)
    if not form.is_valid():
        return render(request, template, {'form': form})
    new_post = form.save(commit=False)
    new_post.author = request.user
    new_post.save()
    return redirect('posts:profile', request.user)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(request.POST or None, instance=post)
    template = 'posts/create_post.html'
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'form': form,
        'is_edit': True,
        'post': post,
    }
    return render(request, template, context)
