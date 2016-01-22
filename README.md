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
- ``drupal_export_scripts``: PHP scripts used to export resources from Drupal. Each script here is
  loaded in Drupal as a "view."
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
    $ cd abbot
    $ pip install -r requirements.txt
    ```

1. The test suite uses the ``pytest`` package. To run the test suite, use the ``py.test`` command.
    The output is quite clear, so you should not have to guess whether the tests passed.

1. Modify the ``packaging/server_configuration.py`` file as required for your testing machine. In
    particular, you must set the ``solr_url``, which means you must also be running a CANTUS-ready
    Solr server locally. That's a bit of a pain, and I'm not going to tell you about it at all.

1. Okay, I'll give you a little help. You have to download and install Solr yourself, but when you
    go to run it, use the ``solr.home`` directory in
    [this repository](https://github.com/CANTUS-Project/abbot_solr_home). The command to start Solr
    will look something like this:

    ```bash
    /path/to/solr/bin/solr start -s /path/to/abbot_solr_home
    ```

    And you can stop Solr with a command like this:

    ```bash
    /path/to/solr/bin/solr stop all
    ```

1. Run a development instance of *Abbot*:

   ```bash
   $ python -m abbot --options-file packaging/server_configuration.py
   ```


## Install for Deployment

Use the [Ansible](http://www.ansible.com/) playbooks, according to the instructions in the
``packaging/deployment_instructions.rst`` document. Note that you **must** follow the instructions
when initially setting up an Abbot server.  If you don't follow the instructions, Ansible will fail.

Ansible is a tool that helps set up, install, and configure your servers. Ansible can handle very
complicated situations, but it also works well for Abbot and HolyOrders. Although there are a few
manual steps required, the Ansible playbooks in this repository handle the most complicated and
difficult tasks for you.

A "playbook" is a list of steps for Ansible to follow in order to bring your server to the desired
configuration. When Ansible runs a playbook, it follows all the instructions in that playbook, and
in "included" playbooks, in the order they are specified. Therefore, running the playbook called
"abbot.yml" will configure SSH, *then* install Solr after its dependencies, *then* install Abbot
after its dependencies.
