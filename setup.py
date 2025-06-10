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
    version="0.13.2",
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
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="quant stock finance fintech big-data zvt technical-analysis trading-platform pandas fundamental-analysis",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.9, <4",
    include_package_data=True,
    install_requires=[
        "requests==2.32.4",
        "SQLAlchemy==2.0.36",
        "pandas==2.2.3",
        "pydantic==2.6.4",
        "arrow==1.2.3",
        "openpyxl==3.1.1",
        "demjson3==3.0.6",
        "plotly==5.13.0",
        "dash==2.18.2",
        "jqdatapy==0.1.8",
        "dash-bootstrap-components==1.3.1",
        "dash_daq==0.5.0",
        "scikit-learn==1.5.2",
        "fastapi==0.110.0",
        "fastapi-pagination==0.12.23",
        "apscheduler==3.10.4",
        "eastmoneypy==0.1.9",
        "orjson==3.10.3",
        "numpy==2.1.3",
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
            "zvt_server = zvt.zvt_server:main",
            "zvt_export = zvt.plugin:export",
        ],
    },
    license_file="LICENSE",
)
