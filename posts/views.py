from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .models import Post, Categoria
from taggit.models import Tag

from .forms import AddPostForm

# complex lookups (for searching)
from django.db.models import Q

from django.urls import reverse_lazy

# class based views
from django.views.generic.edit import CreateView, DeleteView, UpdateView, FormView

from django.views import View
from django.utils.decorators import method_decorator

from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.base import TemplateView

from django.views.generic.dates import YearArchiveView, MonthArchiveView, DayArchiveView

from django.contrib.auth.mixins import (
    LoginRequiredMixin,
    UserPassesTestMixin,
    PermissionRequiredMixin,
)

from django.db import transaction


class CategoriaDatesMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categorias"] = Categoria.objects.all()
        # get queryset of datetime objects for all published posts
        context["dates"] = Post.objects.filter(status="PUBLISHED").datetimes(
            field_name="published_date", kind="month", order="DESC"
        )
        context["recent_posts"] = Post.objects.filter(status="PUBLISHED").order_by(
            "-published_date"
        )[:3]
        return context


class ListarPosts(CategoriaDatesMixin, ListView):
    model = Post
    template_name = "posts/index.html"
    context_object_name = "posts"
    ordering = ("-published_date",)
    paginate_by = 5


class ListarPorAutor(CategoriaDatesMixin, ListView):
    model = Post
    context_object_name = "posts"
    template_name = "posts/post_por_autor.html"
    paginate_by = 5
    ordering = ("-published_date",)

    def get_queryset(self):
        autor = self.kwargs.get("autor", None)
        results = []
        if autor:
            results = Post.objects.filter(author__username=autor)
        return results

    def get_context_data(self, **kwargs):
        """
        Passando o nome do autor para o context
        """
        context = super().get_context_data(**kwargs)
        context["autor"] = self.kwargs.get("autor", None)
        return context


class ListarPorTag(CategoriaDatesMixin, ListView):
    model = Post
    context_object_name = "posts"
    template_name = "posts/post_por_tag.html"
    paginate_by = 5
    ordering = ("-published_date",)

    def get_queryset(self):
        tag = self.kwargs.get("tag", None)
        results = []
        if tag:
            results = Post.objects.filter(tags__name=tag)
        return results

    def get_context_data(self, **kwargs):
        """
        Pass tag name to the context
        """
        context = super().get_context_data(**kwargs)
        context["tag"] = self.kwargs.get("tag", None)
        return context


class ListarPorCategoria(CategoriaDatesMixin, ListView):
    model = Post
    context_object_name = "posts"
    template_name = "posts/post_by_Categoria.html"
    paginate_by = 5
    ordering = ("-published_date",)

    def get_queryset(self):
        categoria = self.kwargs.get("name", None)
        results = []
        if categoria:
            results = Post.objects.filter(Categoria__name=categoria)
        return results

    def get_context_data(self, **kwargs):
        """
        Passando o nome da categoria para o context
        """
        context = super().get_context_data(**kwargs)
        context["categoria"] = self.kwargs.get("name", None)
        return context


class DetailsPost(CategoriaDatesMixin, DetailView):
    model = Post
    template_name = "posts/post_detalhe.html"


# Post archive views
class ArchiveMixin:
    model = Post
    date_field = "published_date"
    allow_future = False
    context_object_name = "posts"


class PostYearArchive(CategoriaDatesMixin, ArchiveMixin, YearArchiveView):
    make_object_list = True


class PostYearMonthArchive(CategoriaDatesMixin, ArchiveMixin, MonthArchiveView):
    pass


# Create, delete and update post views
class AdicionarPost(
    CategoriaDatesMixin, PermissionRequiredMixin, LoginRequiredMixin, CreateView
):
    form_class = AddPostForm
    permission_required = "posts.add_post"
    template_name = "posts/post_form.html"

    # to process request.user in the form
    def form_valid(self, form):
        form.save(commit=False)
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """
        To use AddPostForm with 'Update' instead of 'Add' text in update view
        """
        context = super().get_context_data(**kwargs)
        context["update"] = False
        return context


class PostDraftsList(
    CategoriaDatesMixin, PermissionRequiredMixin, LoginRequiredMixin, ListView
):
    template_name = "posts/list_drafts.html"
    permission_required = "posts.add_post"
    context_object_name = "posts"

    def get_queryset(self):
        return Post.objects.filter(
            status="DRAFT", author__username=self.request.user.username
        )


class DeletarPost(
    CategoriaDatesMixin, LoginRequiredMixin, UserPassesTestMixin, DeleteView
):
    model = Post
    success_url = reverse_lazy("posts:index")

    def test_func(self):
        """
        Only let the user delete object if they own the object being deleted
        """
        return self.get_object().author.username == self.request.user.username


class AtualizarPost(
    CategoriaDatesMixin, LoginRequiredMixin, UserPassesTestMixin, UpdateView
):
    model = Post
    form_class = AddPostForm

    def test_func(self):
        """
        Only let the user update object if they own the object being updated

        """
        return self.get_object().author.username == self.request.user.username

    def get_context_data(self, **kwargs):
        """
        To use AddPostForm with 'Update' instead of 'Add' text in update view
        """
        context = super().get_context_data(**kwargs)
        context["update"] = True
        return context


class BuscarPosts(CategoriaDatesMixin, ListView):
    context_object_name = "posts"
    template_name = "posts/post_buscar.html"
    paginate_by = 5
    ordering = ("-published_date",)

    def get_queryset(self):
        search_query = self.request.GET.get("q", None)
        results = []
        if search_query:
            results = Post.objects.filter(
                Q(Categoria__name__icontains=search_query)
                | Q(author__username__icontains=search_query)
                | Q(title__icontains=search_query)
                | Q(content__icontains=search_query)
            ).distinct()
        return results
