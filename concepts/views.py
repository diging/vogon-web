from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from django.template import loader
from guardian.shortcuts import get_objects_for_user


def list_concept_types(request):
    """
    List all of the concept types
    """
    template = loader.get_template('concepts/list_types.html')

    text_list = get_objects_for_user(request.user, 'annotations.view_text')

    order_by = request.GET.get('order_by', 'title')
    text_list = text_list.order_by(order_by)

    paginator = Paginator(text_list, 15)

    page = request.GET.get('page')
    try:
        texts = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        texts = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        texts = paginator.page(paginator.num_pages)

    context = {
        'types': texts,
        'order_by': order_by,
        'user': request.user,
    }
    return HttpResponse(template.render(context))


def type(request, type_id):
    pass


# Create your views here.
# def home(request):
#     """
#
#     Provides a landing page containing information about the application
#     for user who are not authenticated
#
#     LoggedIn users are redirected to the dashboard view
#     ----------
#     request : HTTPRequest
#         The request for application landing page.
#     Returns
#     ----------
#     :template:
#         Renders landing page for non-loggedin user and
#         dashboard view for loggedin users.
#     """
#     template = loader.get_template('annotations/home.html')
#     user_count = VogonUser.objects.filter(is_active=True).count()
#     text_count = Text.objects.all().count()
#     relation_count = Relation.objects.count()
#     context = RequestContext(request, {
#         'user_count': user_count,
#         'text_count': text_count,
#         'relation_count': relation_count
#     })
#     return HttpResponse(template.render(context))
