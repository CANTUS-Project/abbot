Abbott
======

*Abbott* is a Python 3.4 implementation of a server for the Cantus API.

License
-------

*Abbott* is copyrighted according to the terms of the GNU AGPLv3+. A copy of the license is held in
the file called "LICENSE."

Repository Layout
-----------------

The ``abbott`` directory contains program code. The simplest way to run *Abbott* is to execute this
directory as a Python module.

The ``scripts`` directory contains scripts used to convert between various formats, and tests for
those scripts. These are primarily for moving data from the Drupal to the Solr servers.

The ``tests`` directory contains unit and integration tests for the program code.

The ``test_client`` directory contains a simple HTML Web page to use when testing *Abbott*.

The ``packaging`` directory contains files relevant to deploying *Abbott*, such as a sample
configuration file, *systemd* unit files, and an alternative startup script.

Install for Development
-----------------------

Clone this git repository:

    $ git clone https://github.com/CANTUS-Project/abbott.git

Create and activate a new virtualenv:

    $ pyvenv */your/path/here*
    $ source */your/path/here/bin/activate*

Install the development requirements:

    $ pip install -r requirements-devel.txt

Install ``abbott`` itself. This ensure the ``abbott`` module is importable in the interpreter.

    $ pip install -e .

The test suite uses the ``pytest`` package. To run the test suite, ensure your venv is activated,
then issue the following command from the "abbott" root directory:

    $ py.test

``pytest`` is quite clear in its output, so you should not have to guess whether the tests passed.
To run a test instance of *Abbott*, run this command from the "abbott" root directory:

    $ python abbott

Install for Deployment
----------------------

As for development, but use the ``requirements-deploy.txt`` file. There isn't yet a good way to
deploy *Abbott*, but rest assured it will happen.

After you install *Abbott*, you may wish to test its functionality:

    $ python setup.py test
