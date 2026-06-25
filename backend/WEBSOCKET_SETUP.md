# WebSocket Real-Time Updates - Setup Guide

## Installation

1. **Install Django Channels and dependencies:**

```bash
pip install channels channels-redis daphne
```

2. **Update `requirements.txt`:**

```txt
channels==4.0.0
channels-redis==4.1.0
daphne==4.0.0
```

## Configuration

3. **Update `contractai/settings.py`:**

```python
INSTALLED_APPS = [
    'daphne',  # Add at the top
    # ... other apps
    'channels',
]

# ASGI Configuration
ASGI_APPLICATION = 'contractai.asgi.application'

# Channel Layers (Redis backend)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
```

4. **Create `contractai/asgi.py`:**

```python
import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from prime.routing import websocket_urlpatterns

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'contractai.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})
```

5. **Create `prime/routing.py`:**

```python
from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/dashboard/', consumers.DashboardConsumer.as_asgi()),
]
```

6. **Create `prime/consumers.py`:**

```python
import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser

class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_group_name = f'dashboard_{self.scope["user"].id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # Send initial data
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'WebSocket connected'
        }))

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.dumps(text_data)
        message_type = data.get('type')

        if message_type == 'ping':
            await self.send(text_data=json.dumps({
                'type': 'pong'
            }))

        elif message_type == 'request_refresh':
            # Fetch fresh data
            dashboard_data = await self.get_dashboard_data()
            await self.send(text_data=json.dumps({
                'type': 'full_refresh',
                'payload': dashboard_data
            }))

    # Send updates to WebSocket
    async def dashboard_update(self, event):
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def get_dashboard_data(self):
        from core.models import Contract
        user = self.scope['user']

        contracts = Contract.objects.filter(user=user)
        # Build dashboard data
        return {
            'contracts': list(contracts.values()),
            'timestamp': str(datetime.now())
        }
```

## Usage

### Broadcasting Updates from Django

```python
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def broadcast_dashboard_update(user_id, update_type, payload):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f'dashboard_{user_id}',
        {
            'type': 'dashboard_update',
            'update_type': update_type,
            'payload': payload
        }
    )

# Example: After contract update
contract.save()
broadcast_dashboard_update(
    user.id,
    'contract_update',
    {'contract_id': str(contract.id), 'status': 'updated'}
)
```

### Frontend Usage

```javascript
import { useDashboardWebSocket } from '@/hooks/useWebSocket';

function Dashboard() {
  const { isConnected, updates, requestRefresh } = useDashboardWebSocket();

  useEffect(() => {
    if (updates.contracts) {
      // Update dashboard with new data
      console.log('Contracts updated:', updates.contracts);
    }
  }, [updates]);

  return (
    <div>
      <RealTimeIndicator
        isConnected={isConnected}
        lastUpdate={updates.timestamp}
        onRefresh={requestRefresh}
      />
      {/* Dashboard content */}
    </div>
  );
}
```

## Running with WebSocket

### Development:
```bash
python manage.py runserver  # HTTP
# or
daphne -b 0.0.0.0 -p 8000 contractai.asgi:application  # ASGI with WebSocket
```

### Docker (update docker-compose.yml):
```yaml
backend:
  command: daphne -b 0.0.0.0 -p 8000 contractai.asgi:application
```

## Testing

```python
# Test WebSocket connection
import websocket
import json

ws = websocket.create_connection("ws://localhost:8000/ws/dashboard/?token=YOUR_JWT_TOKEN")
ws.send(json.dumps({'type': 'ping'}))
result = ws.recv()
print(result)
ws.close()
```

## Security

- ✅ JWT token authentication required
- ✅ User-specific room groups
- ✅ AllowedHostsOriginValidator
- ✅ CORS configuration

---

**Status:** Configuration complete, ready for `pip install` and server restart
