#!/usr/bin/env python
import os
import sys
from pathlib import Path

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

    ####################################
    # To attach debugger to docker container:
    from django.conf import settings

    if settings.DEBUG:
        if os.environ.get("RUN_MAIN") or os.environ.get("WERKZEUG_RUN_MAIN"):
            import debugpy

            debugpy.listen(("0.0.0.0", 8012))
            print("Attached!")
    ####################################

    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django  # noqa
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )

        raise

    # This allows easy placement of apps within the interior
    # rard directory.
    current_path = Path(__file__).parent.resolve()
    sys.path.append(str(current_path / "rard"))

    execute_from_command_line(sys.argv)
