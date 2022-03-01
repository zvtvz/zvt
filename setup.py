#!/usr/bin/env python

# To use a consistent encoding
from codecs import open
from os import path

# Always prefer setuptools over distutils
from setuptools import setup, find_packages

here = path.abspath(path.dirname(__file__))

# Get the long description from the README file
with open(path.join(here, "README.md"), encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="zvt",
    version="0.9.16",
    description="unified,modular quant framework for human beings ",
    long_description=long_description,
    url="https://github.com/zvtvz/zvt",
    author="foolcage",
    author_email="5533061@qq.com",
    classifiers=[  # Optional
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Customer Service",
        "Intended Audience :: Education",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    keywords="quant stock finance fintech big-data zvt technical-analysis trading-platform pandas fundamental-analysis",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.7, <4",
    include_package_data=True,
    install_requires=[
        "requests == 2.20.1",
        "SQLAlchemy == 1.4.20",
        "pandas == 1.1.4",
        "arrow == 1.2.1",
        "xlrd == 1.2.0",
        "demjson3 == 3.0.5",
        "marshmallow-sqlalchemy == 0.23.1",
        "marshmallow == 3.2.2",
        "plotly==4.12.0",
        "dash==1.17.0",
        "simplejson==3.16.0",
        "jqdatapy==0.1.6",
        "dash-bootstrap-components==0.11.0",
        "dash_daq==0.5.0",
        "scikit-learn==1.0.1",
    ],
    project_urls={  # Optional
        "Bug Reports": "https://github.com/zvtvz/zvt/issues",
        "Funding": "https://www.foolcage.com/zvt",
        "Say Thanks!": "https://saythanks.io/to/foolcage",
        "Source": "https://github.com/zvtvz/zvt",
    },
    long_description_content_type="text/markdown",
    entry_points={
        "console_scripts": [
            "zvt = zvt.main:main",
            "zvt_plugin = zvt.plugin:main",
            "zvt_export = zvt.plugin:export",
        ],
    },
    license_file="LICENSE",
)
