from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import BlogPost

# View for listing all blog posts
def blog_list(request):
    posts = BlogPost.objects.all().order_by('-created_at')
    paginator = Paginator(posts, 9) 
    page_number = request.GET.get('page') 
    page_obj = paginator.get_page(page_number)

    context = {
        'posts': page_obj
    }

    return render(request, 'blog/blog_list.html', context)

# View for a single blog post
def blog_detail(request, category_slug, post_slug):
    # Get the blog post by category and slug
    post = get_object_or_404(BlogPost, category__slug=category_slug, slug=post_slug)
    return render(request, 'blog/blog_detail.html', {'post': post})