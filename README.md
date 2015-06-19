Abbott
======

*Abbott* is a Python 3.4 implementation of a server for the Cantus API.

License
-------

*Abbott* is copyrighted according to the terms of the GNU AGPLv3+. A copy of the license is held in
the file called "LICENSE."

Install for Development
-----------------------

Clone this git repository:

    $ git clone https://github.com/CANTUS-Project/abbott.git

Create and activate a new virtualenv:

    $ pyvenv */your/path/here*
    $ source */your/path/here/bin/activate*

Install the development requirements:

    $ pip install -r requirements-devel.txt

Run the test suite (see below) and you're off!

Run the Automated Test Suite
----------------------------

The test suite uses the ``pytest`` package. To run the test suite, ensure your venv is activated,
then issue the following command from the "abbott" root directory:

    $ py.test

``pytest`` is quite clear in its output, so you should not have to guess whether the tests passed.

Install for Deployment
----------------------

As for development, but use the ``requirements-deploy.txt`` file. There isn't yet a good way to
deploy *Abbott*, but rest assured it will happen.
