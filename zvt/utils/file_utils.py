# -*- coding: utf-8 -*-
import os
from typing import List


def list_all_files(dir_path: str = './domain', ext: str = '.py', excludes=None, return_base_name=False) -> List[str]:
    """
    list all files with extension in specific directory recursively

    :param dir_path: the directory path
    :param ext: file extension
    :param excludes: excluding files
    :param return_base_name: return file name if True otherwise abs path
    :return:
    """
    files = []
    for entry in os.scandir(dir_path):
        if entry.is_dir():
            files += list_all_files(entry.path)
        elif entry.is_file():
            if not ext or (ext and entry.path.endswith(ext)):
                if excludes and entry.path.endswith(excludes):
                    continue
                if return_base_name:
                    files.append(os.path.basename(entry.path))
                else:
                    files.append(entry.path)
        else:
            pass
    return files
