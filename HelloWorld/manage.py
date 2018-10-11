#!/usr/bin/env python
import os
import sys
from tshare import dbtools



if __name__ == '__main__':
    dbtools.user_proxy("http://cn-proxy.jp.oracle.com:80")

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'HelloWorld.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)
