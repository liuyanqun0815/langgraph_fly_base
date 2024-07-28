"""
URL configuration for fly_base project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path

from sale_app.chat_api.api import to_chat
from sale_app.chat_api.kb_api import upload_file, create_index, search, create_collection_api, upload_and_read_excel, \
    hybrid_search

urlpatterns = [
    # path("admin/", admin.site.urls),
    path("api/chat", to_chat),
    path('kb/upload', upload_file),
    path('kb/create_index', create_index),
    path('kb/search', search),
    path('kb/create_collection', create_collection_api),
    path('kb/upload_and_read_excel', upload_and_read_excel),
    path('kb/hybrid_search', hybrid_search),
]
