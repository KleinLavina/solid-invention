from django.shortcuts import render

def review_work_items(request):
    return render(request, "admin/review_work_items.html")
