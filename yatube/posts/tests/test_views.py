from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from posts.app_settings import POSTS_PER_PAGE
from posts.models import Group, Post, User

HOME_URL = reverse('posts:index')
CREATE_URL = reverse('posts:post_create')
INDEX_HTML = 'posts/index.html'
GROUP_LIST_HTML = 'posts/group_list.html'
PROFILE_HTML = 'posts/profile.html'
POST_DETAIL_HTML = 'posts/post_detail.html'
POST_CREATE_HTML = 'posts/create_post.html'
USERNAME = 'testuser'
PASSWORD = 'testpassword'
GROUP_TITLE = 'Тестовая группа'
GROUP_SLUG = 'test-slug'
TEXT_POST = 'Тестовый пост'


class PostsPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
        )
        cls.group2 = Group.objects.create(
            title=GROUP_TITLE + '2',
            slug=GROUP_SLUG + '2',
        )
        for i in range(1, 14):
            cls.post = Post.objects.create(
                author=cls.user,
                text=TEXT_POST + f'{i}',
                group=cls.group,
            )

    def setUp(self):
        self.user = PostsPagesTests.user
        self.post = PostsPagesTests.post
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = PostsPagesTests.group
        self.group2 = PostsPagesTests.group2
        self.group_list = reverse('posts:group_list', args=[self.group.slug])
        self.profile = reverse('posts:profile', args=[self.user])
        self.post_detail = reverse('posts:post_detail', args=[self.post.id])
        self.post_edit = reverse('posts:post_edit', args=[self.post.id])

    def test_pages_uses_correct_template(self):
        urls_templates = {
            HOME_URL: INDEX_HTML,
            self.group_list: GROUP_LIST_HTML,
            self.profile: PROFILE_HTML,
            self.post_detail: POST_DETAIL_HTML,
            CREATE_URL: POST_CREATE_HTML,
            self.post_edit: POST_CREATE_HTML,
        }
        for reverse_name, template in urls_templates.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_correct_context_non_form_pages(self):
        reverse_names = [
            HOME_URL,
            self.group_list,
            self.profile,
            self.post_detail,
        ]
        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                if reverse_name == self.post_detail:
                    test = response.context.get('post')
                else:
                    test = (
                        response.context['page_obj'].paginator.object_list
                        .order_by('-id')[0]
                    )
                self.assertEqual(test.text, self.post.text)
                self.assertEqual(test.author.id, self.post.author.id)
                self.assertEqual(test.group.id, self.post.group.id)
                self.assertEqual(test.id, self.post.id)

    def test_create_post_show_correct_context(self):
        data = {
            'text': 'Новый тестовый текст',
            'group': self.group.id
        }
        response = self.authorized_client.post(CREATE_URL, data=data,
                                               follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.post.refresh_from_db()
        reverse_names = [
            HOME_URL,
            self.profile,
            self.group_list
        ]
        for reverse_name in reverse_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                test_post = (
                    response.context['page_obj'].paginator.object_list
                    .order_by('-id')[0]
                )
                self.assertEqual(test_post.text, data['text'])
                self.assertEqual(test_post.group.id, data['group'])

    def test_edit_post_show_correct_context(self):
        response = self.authorized_client.get(self.post_edit)
        form = response.context['form']
        data = form.initial
        data['text'] = 'Измененный тестовый текст'
        data['group'] = self.group2.id
        response = self.authorized_client.post(
            self.post_edit, data=data, follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.post.refresh_from_db()
        self.assertEqual(data['text'], self.post.text)
        self.assertEqual(data['group'], self.post.group.id)

    def test_paginator(self):
        reverse_names_templates = {
            HOME_URL: INDEX_HTML,
            self.group_list: GROUP_LIST_HTML,
            self.profile: PROFILE_HTML,
        }
        for reverse_name, template in reverse_names_templates.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                length_p1 = len(response.context['page_obj'])
                self.assertEqual(length_p1, POSTS_PER_PAGE)
                response = self.authorized_client.get(reverse_name + '?page=2')
                length_p2 = len(response.context['page_obj'])
                remains = ((length_p1 + length_p2) - POSTS_PER_PAGE)
                self.assertEqual(length_p2, remains)
