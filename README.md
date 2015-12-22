# Abbot

*Abbot* is a Python 3.4 implementation of a server for the Cantus API.

[![Requirements Status](https://img.shields.io/requires/github/CANTUS-Project/abbot.svg?style=flat-square)](https://requires.io/github/CANTUS-Project/abbot/requirements/?branch=master)
[![Build Status](https://img.shields.io/travis/CANTUS-Project/abbot.svg?style=flat-square)](https://travis-ci.org/CANTUS-Project/abbot)
[![Coverage Status](https://img.shields.io/coveralls/CANTUS-Project/abbot.svg?style=flat-square)](https://coveralls.io/github/CANTUS-Project/abbot?branch=master)
[![Code Issues](https://www.quantifiedcode.com/api/v1/project/2260402ae289418daf4b186b71ec14c4/badge.svg)](https://www.quantifiedcode.com/app/project/2260402ae289418daf4b186b71ec14c4)


## License

*Abbot* is copyrighted according to the terms of the GNU AGPLv3+. A copy of the license is held in
the file called "LICENSE."


## Repository Layout

- ``abbot``: this directory contains program code for the Cantus API server.
- ``holy_orders``: a program that updates *Abbot*'s Solr server.
- ``scripts``: Python scripts (and tests) used to convert between various XML formats. These are
    primarily used by *HolyOrders* to move data exported from Drupal into Solr.
- ``tests``: unit and integration tests for *Abbot* and *HolyOrders*.
- ``packaging``: deployment scripts for *Abbot* and *HolyOrders*.


## Install for Development

1. Clone this git repository:

    ```bash
    $ git clone https://github.com/CANTUS-Project/abbot.git
    ```

1. Create and activate a new virtualenv:

    ```bash
    $ pyvenv */your/path/here*
    $ source */your/path/here/bin/activate*
    ```

1. Install the Python packages:

    ```bash
    $ pip install -r requirements.txt
    ```

1. The test suite uses the ``pytest`` package. To run the test suite, ensure your venv is activated,
   then issue the following command from the "abbot" root directory:

    ```bash
    $ py.test
    ```

1. ``pytest`` is quite clear in its output, so you should not have to guess whether the tests passed.
   To run a test instance of *Abbot*, run this command:

   ```bash
   $ python -m abbot
   ```


## Install for Deployment

Use the [Ansible](http://www.ansible.com/) playbooks, according to the instructions in the
``packaging/deployment_instructions.rst`` document.
