from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User

HOME_URL = reverse('posts:index')
CREATE_URL = reverse('posts:post_create')
USERNAME = 'testuser'
GROUP_TITLE = 'Тестовая группа'
GROUP_SLUG = 'test-slug'
TEXT_POST = 'Тестовый пост'


class PostsFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=TEXT_POST,
            group=cls.group,
        )

    def setUp(self):
        self.user = PostsFormsTests.user
        self.post = PostsFormsTests.post
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.group = PostsFormsTests.group
        self.post_edit = reverse('posts:post_edit', args=[self.post.id])
        self.posts_count = Post.objects.count()

    def test_valid_form_create_post_in_db(self):
        form_data = {
            'text': f'{TEXT_POST}2',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            CREATE_URL, data=form_data, follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.post.refresh_from_db()
        response = self.authorized_client.get(HOME_URL)
        test_post = (
            response.context['page_obj'].paginator.object_list
            .order_by('-id')[0]
        )
        self.assertEqual(test_post.id, Post.objects.count())

    def test_valid_form_change_post_in_db(self):
        response = self.authorized_client.get(self.post_edit)
        form = response.context['form']
        form_data = form.initial
        form_data['text'] = f'Измененный {TEXT_POST}'
        form_data['group'] = self.group.id
        response = self.authorized_client.post(
            self.post_edit, data=form_data, follow=True
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.post.refresh_from_db()
        response = self.authorized_client.get(HOME_URL)
        test_post = (
            response.context['page_obj'].paginator.object_list
            .order_by('-id')[0]
        )
        test_count = Post.objects.count()
        self.assertEqual(test_count, self.posts_count)
        self.assertEqual(test_post.id, self.post.id)
        self.assertEqual(test_post.text, self.post.text)
