# -*- coding: utf-8 -*-
import subprocess


def get_git_user_name():
    try:
        return subprocess.check_output(['git', 'config', '--get', 'user.name']).decode('utf8').strip()
    except:
        return "foolcage"


def get_git_user_email():
    try:
        return subprocess.check_output(['git', 'config', '--get', 'user.email']).decode('utf8').strip()
    except:
        return ""
