---
title: Patterns - Client
---

# Client Initialization

## Sync Client

```python
from evergis_api import Client

# By token
client = Client(base_url="https://api.example.com", sb_token="your_token")

# By login/password
client = Client(base_url="https://api.example.com")
client.account.login(username="user", password="pass")
```

## Async Client

```python
from evergis_api import AsyncClient

async_client = AsyncClient(base_url="https://api.example.com", sb_token="your_token")
```

## Environment Variables

```ini
# .env file
EVERGIS_HOST=https://api.example.com
EVERGIS_SB_TOKEN=your_token
EVERGIS_USERNAME=your_username
```

```python
from dotenv import load_dotenv
import os

load_dotenv()
client = Client(base_url=os.getenv("EVERGIS_HOST"), sb_token=os.getenv("EVERGIS_SB_TOKEN"))
```
