# -*- coding: utf-8 -*-

import datetime
import os
import zipfile

from zvt.settings import ZVT_TEST_HOME


def zip_dir(src_dir,
            dst_dir=None,
            zip_file_name=None):
    if not zip_file_name:
        zip_file_name = "data-{}.zip".format(datetime.datetime.today())

    if dst_dir:
        dst_path = os.path.join(dst_dir, zip_file_name)
    else:
        dst_path = os.path.abspath(os.path.join(src_dir, os.pardir, zip_file_name))

    # os.remove(dst_path)

    the_zip_file = zipfile.ZipFile(dst_path, 'w')

    for folder, subfolders, files in os.walk(src_dir):
        for file in files:
            the_path = os.path.join(folder, file)
            if 'zvt_business.db' in the_path:
                continue
            print("zip {}".format(the_path))
            the_zip_file.write(the_path,
                               os.path.relpath(the_path, src_dir),
                               compress_type=zipfile.ZIP_DEFLATED)

    the_zip_file.close()


def unzip(zip_file, dst_dir):
    the_zip_file = zipfile.ZipFile(zip_file)
    print("start unzip {} to {}".format(zip_file, dst_dir))
    the_zip_file.extractall(dst_dir)
    print("finish unzip {} to {}".format(zip_file, dst_dir))
    the_zip_file.close()


if __name__ == '__main__':
    zip_dir(ZVT_TEST_HOME, zip_file_name='datasample.zip')
    # unzip(DATA_SAMPLE_ZIP_PATH, DATA_SAMPLE_PATH)
