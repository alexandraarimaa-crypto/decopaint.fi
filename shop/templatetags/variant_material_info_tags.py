from django import template

register = template.Library()


@register.simple_tag
def variant_info_page_url(request, key, page):
    query = request.GET.copy()
    query[key] = str(page)
    return '?' + query.urlencode() + '#variants-group'
