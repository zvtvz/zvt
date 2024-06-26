# -*- coding: utf-8 -*-
import importlib
import json
import logging
import os
import pkgutil
import pprint
import shutil
from logging.handlers import RotatingFileHandler
from typing import List

import pandas as pd
import pkg_resources
from pkg_resources import get_distribution, DistributionNotFound

from zvt.consts import DATA_SAMPLE_ZIP_PATH, ZVT_TEST_HOME, ZVT_HOME, ZVT_TEST_DATA_PATH, ZVT_TEST_ZIP_DATA_PATH

try:
    dist_name = __name__
    __version__ = get_distribution(dist_name).version
except DistributionNotFound:
    __version__ = "unknown"
finally:
    del get_distribution, DistributionNotFound

logger = logging.getLogger(__name__)


def init_log(file_name="zvt.log", log_dir=None, simple_formatter=True):
    if not log_dir:
        log_dir = zvt_env["log_path"]

    root_logger = logging.getLogger()

    # reset the handlers
    root_logger.handlers = []

    root_logger.setLevel(logging.INFO)

    file_name = os.path.join(log_dir, file_name)

    file_log_handler = RotatingFileHandler(file_name, maxBytes=524288000, backupCount=10)

    file_log_handler.setLevel(logging.INFO)

    console_log_handler = logging.StreamHandler()
    console_log_handler.setLevel(logging.INFO)

    # create formatter and add it to the handlers
    if simple_formatter:
        formatter = logging.Formatter("%(asctime)s  %(levelname)s  %(threadName)s  %(message)s")
    else:
        formatter = logging.Formatter(
            "%(asctime)s  %(levelname)s  %(threadName)s  %(name)s:%(filename)s:%(lineno)s  %(funcName)s  %(message)s"
        )
    file_log_handler.setFormatter(formatter)
    console_log_handler.setFormatter(formatter)

    # add the handlers to the logger
    root_logger.addHandler(file_log_handler)
    root_logger.addHandler(console_log_handler)


os.environ.setdefault("SQLALCHEMY_WARN_20", "1")
pd.set_option("expand_frame_repr", False)
pd.set_option("mode.chained_assignment", "raise")
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)

zvt_env = {}

zvt_config = {}

_plugins = {}


def init_env(zvt_home: str, **kwargs) -> dict:
    """
    init env

    :param zvt_home: home path for zvt
    """
    data_path = os.path.join(zvt_home, "data")
    resource_path = os.path.join(zvt_home, "resources")
    tmp_path = os.path.join(zvt_home, "tmp")
    if not os.path.exists(data_path):
        os.makedirs(data_path)

    if not os.path.exists(resource_path):
        os.makedirs(resource_path)

    if not os.path.exists(tmp_path):
        os.makedirs(tmp_path)

    zvt_env["zvt_home"] = zvt_home
    zvt_env["data_path"] = data_path
    zvt_env["resource_path"] = resource_path
    zvt_env["tmp_path"] = tmp_path

    # path for storing ui results
    zvt_env["ui_path"] = os.path.join(zvt_home, "ui")
    if not os.path.exists(zvt_env["ui_path"]):
        os.makedirs(zvt_env["ui_path"])

    # path for storing logs
    zvt_env["log_path"] = os.path.join(zvt_home, "logs")
    if not os.path.exists(zvt_env["log_path"]):
        os.makedirs(zvt_env["log_path"])

    init_log()

    pprint.pprint(zvt_env)

    init_resources(resource_path=resource_path)
    # init config
    init_config(current_config=zvt_config, **kwargs)
    # init plugin
    # init_plugins()

    return zvt_env


def init_resources(resource_path):
    package_name = "zvt"
    package_dir = pkg_resources.resource_filename(package_name, "resources")
    from zvt.utils.file_utils import list_all_files

    files: List[str] = list_all_files(package_dir, ext=None)
    for source_file in files:
        dst_file = os.path.join(resource_path, source_file[len(package_dir) + 1 :])
        if not os.path.exists(dst_file):
            shutil.copyfile(source_file, dst_file)


def init_config(pkg_name: str = None, current_config: dict = None, **kwargs) -> dict:
    """
    init config
    """

    # create default config.json if not exist
    if pkg_name:
        config_file = f"{pkg_name}_config.json"
    else:
        pkg_name = "zvt"
        config_file = "config.json"

    logger.info(f"init config for {pkg_name}, current_config:{current_config}")

    config_path = os.path.join(zvt_env["zvt_home"], config_file)
    if not os.path.exists(config_path):
        try:
            sample_config = pkg_resources.resource_filename(pkg_name, "config.json")
            if os.path.exists(sample_config):
                shutil.copyfile(sample_config, config_path)
        except Exception as e:
            logger.warning(f"could not load config.json from package {pkg_name}")

    if os.path.exists(config_path):
        with open(config_path) as f:
            config_json = json.load(f)
            for k in config_json:
                current_config[k] = config_json[k]

    # set and save the config
    for k in kwargs:
        current_config[k] = kwargs[k]
        with open(config_path, "w+") as outfile:
            json.dump(current_config, outfile)

    pprint.pprint(current_config)
    logger.info(f"current_config:{current_config}")

    return current_config


def init_plugins():
    for finder, name, ispkg in pkgutil.iter_modules():
        if name.startswith("zvt_"):
            try:
                _plugins[name] = importlib.import_module(name)
            except Exception as e:
                logger.warning(f"failed to load plugin {name}", e)
    logger.info(f"loaded plugins:{_plugins}")


def old_db_to_provider_dir(data_path):
    files = os.listdir(data_path)
    for file in files:
        if file.endswith(".db"):
            # Split the file name to extract the provider
            provider = file.split("_")[0]

            # Define the destination directory
            destination_dir = os.path.join(data_path, provider)

            # Create the destination directory if it doesn't exist
            if not os.path.exists(destination_dir):
                os.makedirs(destination_dir)

            # Define the source and destination paths
            source_path = os.path.join(data_path, file)
            destination_path = os.path.join(destination_dir, file)

            # Move the file to the destination directory
            if not os.path.exists(destination_path):
                shutil.move(source_path, destination_path)
                logger.info(f"Moved {file} to {destination_dir}")


if os.getenv("TESTING_ZVT"):
    init_env(zvt_home=ZVT_TEST_HOME)

    # init the sample data if need
    same = False
    if os.path.exists(ZVT_TEST_ZIP_DATA_PATH):
        import filecmp

        same = filecmp.cmp(ZVT_TEST_ZIP_DATA_PATH, DATA_SAMPLE_ZIP_PATH)

    if not same:
        from zvt.contract import *
        from zvt.utils.zip_utils import unzip

        shutil.copyfile(DATA_SAMPLE_ZIP_PATH, ZVT_TEST_ZIP_DATA_PATH)
        unzip(ZVT_TEST_ZIP_DATA_PATH, ZVT_TEST_DATA_PATH)
else:
    init_env(zvt_home=ZVT_HOME)

old_db_to_provider_dir(zvt_env["data_path"])

# register to meta
import zvt.contract as zvt_contract
import zvt.recorders as zvt_recorders
import zvt.factors as zvt_factors

import platform

if platform.system() == "Windows":
    try:
        import zvt.recorders.qmt.quotes.qmt_kdata_recorder as qmt_kdata_recorde
    except Exception as e:
        logger.error("QMT not work", e)
else:
    logger.warning("QMT need run in Windows!")


__all__ = ["zvt_env", "zvt_config", "init_log", "init_env", "init_config", "__version__"]
