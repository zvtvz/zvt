.. _install:

Installation of zvt
========================

This part of the documentation covers the installation of zvt.
The first step to using any software package is getting it properly installed.


Python version support
----------------------

Officially Python 3.7, and 3.8.


$ python -m pip install -U zvt
--------------------------------

To install zvt, simply run this simple command in your terminal of choice::

    $ python -m pip install -U zvt


Get the Source Code
-------------------

zvt is actively developed on GitHub, where the code is
`always available <https://github.com/zvtvz/zvt>`_.

You can clone the public repository::

    $ git clone git://github.com/zvtvz/zvt.git

Once you have a copy of the source, you can embed it in your own Python
package, or install it into your site-packages easily::

    $ cd zvt
    $ python -m pip install .
