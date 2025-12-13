from django.shortcuts import render

def teams(request):
    return render(request, "admin/teams.html")
