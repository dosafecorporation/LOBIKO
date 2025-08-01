
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/dashboard/$', consumers.DashboardConsumer.as_asgi()),
    re_path(r'ws/discussion/(?P<session_id>\d+)/$', consumers.DiscussionConsumer.as_asgi()),
    re_path(r'ws/discussion/(?P<session_id>\w+)/$', consumers.DiscussionConsumer.as_asgi()),
]



