"""Promotions views."""

from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from apps.promotions.models import Promotion


def promotions_list(request):
    now = timezone.now()
    promotions = (
        Promotion.objects.filter(is_active=True, start_date__lte=now)
        .order_by('-is_featured', '-priority')
    )
    context = {
        'promotions': promotions,
        'page_title': 'Promotions & Offers',
    }
    return render(request, 'promotions/list.html', context)


def promotion_detail(request, slug):
    promotion = get_object_or_404(Promotion, slug=slug, is_active=True)
    context = {
        'promotion': promotion,
        'page_title': promotion.title,
    }
    return render(request, 'promotions/detail.html', context)
