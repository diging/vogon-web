# VogonWeb documentation

The latest version of the documentation is online at
http://diging.github.io/vogon-web .

To build the documentation yourself, you will need
[Sphinx](http://sphinx-doc.org/). You can install Sphinx from PyPI. We use the
Alabaster theme, which you should also install.

.. code-block:: shell

   $ pip install sphinx alabaster

You can then build the documentation with:

.. code-block:: shell

   $ make html

The resulting HTML docs should be in ``_build/html/``.
