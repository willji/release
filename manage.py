#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ops.settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
    for arg in sys.argv:
                # if syncdb occurs and users don't exist, create them
                if arg.lower() == 'syncdb':
                    from django.contrib.auth.models import User
                    admin_id = 'admin'
                    admin_email = 'huamaolin@ymatou.com'
                    admin_password = 'admin'
                    user_list = User.objects.filter(username=admin_id)
                    if len(user_list) == 0:
                        print 'create superuser: ' + admin_id
                        new_admin = User.objects.create_superuser(admin_id, admin_email, admin_password)

