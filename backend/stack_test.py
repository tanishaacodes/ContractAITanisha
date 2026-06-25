import faulthandler, signal, sys, threading, time
faulthandler.enable()
def dumper():
    time.sleep(50)
    faulthandler.dump_traceback(file=sys.stderr, all_threads=True)
    sys.stderr.flush()
threading.Thread(target=dumper, daemon=True).start()

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE","contractai.settings")
import django
print("about to call django.setup()", flush=True)
django.setup()
print("django.setup() DONE", flush=True)
