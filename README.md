# Abbot

*Abbot* is a server implementation of the Cantus API for CPython 3.4 and 3.5.

[![Requirements Status](https://img.shields.io/requires/github/CANTUS-Project/abbot.svg?style=flat-square)](https://requires.io/github/CANTUS-Project/abbot/requirements/?branch=master)
[![Build Status](https://img.shields.io/travis/CANTUS-Project/abbot.svg?style=flat-square)](https://travis-ci.org/CANTUS-Project/abbot)
[![Coverage Status](https://img.shields.io/coveralls/CANTUS-Project/abbot.svg?style=flat-square)](https://coveralls.io/github/CANTUS-Project/abbot?branch=master)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/03dab52413a34daeacb6de020a823273)](https://www.codacy.com/app/christopher/abbot)


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


## System Management and Logging

Abbot is designed for Linux operating systems with ``systemd``, and therefore uses ``journald`` for
logging. If you followed the deployment instructions, you're running Abbot on CentOS 7, so the
following instructions are for you. If you didn't follow the instructions, I don't really know what
will happen.

### Abbot

According to ``systemd``, Abbot is called ``abbot``. You can start, stop, or view the status of
Abbot with the following commands (run with superuser permissions):

```
# systemctl start abbot
# systemctl stop abbot
# systemctl status abbot
```

This is a sample output from the ``status`` command.

```
[compadmin@abbot ~]$ sudo systemctl status abbot
● abbot.service - "Abbot HTTP Server"
   Loaded: loaded (/usr/lib/systemd/system/abbot.service; enabled; vendor preset: disabled)
   Active: active (running) since Thu 2016-01-21 14:49:01 EST; 8h ago
     Docs: https://github.com/CANTUS-Project/abbot/
 Main PID: 12680 (python)
   CGroup: /system.slice/abbot.service
           └─12680 /usr/local/abbot-venv/bin/python -m abbot --options_file=/etc/abbot.conf

Jan 21 14:49:01 abbot.uwaterloo.ca systemd[1]: Started "Abbot HTTP Server".
Jan 21 14:49:01 abbot.uwaterloo.ca systemd[1]: Starting "Abbot HTTP Server"...
Jan 21 14:49:02 abbot.uwaterloo.ca abbot[12680]: Abbot Server 0.4.16 for Cantus API 0.2.3.
Jan 21 14:50:24 abbot.uwaterloo.ca abbot[12680]: 404 GET /favicon.ico/ (::ffff:198.58.167.176) 0.72ms
Jan 21 14:50:24 abbot.uwaterloo.ca abbot[12680]: 404 GET /favicon.ico/ (::ffff:198.58.167.176) 0.53ms
```

You can also view the Abbot logs:

```
# journalctl -u abbot -n 50
# journalctl -u abbot
```

The first command, with an ``n`` flag, asks ``journalctl`` to output only the most recent 50 log
messages. The ``u`` flag tells ``journalctl`` which "unit" to print data for.

The Ansible playbooks install Abbot as a socket-activated service, enabled by default. This means
that Abbot will start whenever the operating system boots. Moreover, if Abbot crashes or stops for
some reason, ``systemd`` will start Abbot if someone tries to connect to its port. Therefore, if
you wish to disable (or enable) Abbot, you must disable (or enable) two things:

```
# systemctl disable abbot.service
# systemctl disable abbot.socket
```


### HolyOrders

According to ``systemd``, HolyOrders is called ``holyorders``. Most of the commands for HolyOrders
are very similar to the commands for Abbot:

```
# systemctl start holyorders
# systemctl stop holyorders
# systemctl status holyorders
# journalctl -u holyorders -n 50
```

However, Ansible installs HolyOrders as a timer-activated service, enabled by default. This means
that HolyOrders will be started by ``systemd`` periodically (by default every hour). If you wish to
disable (or enable) HolyOrders, you must disable (or enable) two things:

```
# systemctl disable holyorders.service
# systemctl disable holyorders.timer
```
