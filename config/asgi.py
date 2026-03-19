"""
ASGI config for Car Detailing Workflow Management System.

It exposes the ASGI callable as a module-level variable named ``application``.
"""

import os
from channels.routing import ProtocolTypeRouter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

from django.core.asgi import get_asgi_application

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": get_asgi_application(),
})
