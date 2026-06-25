import time
t=time.time()
import django
print(f"django module import: {time.time()-t:.1f}s", flush=True)
t=time.time()
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE","contractai.settings")
django.setup()
print(f"django.setup(): {time.time()-t:.1f}s", flush=True)
