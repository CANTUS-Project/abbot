Deployment Instructions for Abbot and HolyOrders
================================================

Follow these instructions to deploy a new *Abbot* server from scratch.


The Virtual Machine
-------------------

*Abbot* is intended for deployment on CentOS 7. We recommend a minimum of 1 GB of memory and 20 GB
of persistent storage in a single partition. If you're as picky as me, you can set up with the
following partitions:

- /: 10G
- /home: 5G
- /var: 5G
- /var/log: 5G
- /var/log/audit: 2G
- /usr/local: 5G
- swap: 2G
- total: 34G


Your Own Computer
-----------------

*Abbot* uses a configuration and deployment management application called *Ansible*. While the first
several configuration steps are manual, the majority of the configuration (and indeed all of the
difficult parts) are automated.

You must install *Ansible* on your own computer, which will be the "Control Machine." Refer to
https://docs.ansible.com/ansible/intro_installation.html#installing-the-control-machine for help.

You must also install *Git*, *NodeJS*, and *NPM* in order to build and prepare the *Vitrail*
deployment bundle. (*Vitrail* is the mobile-friendly web application designed for *Abbot*). You
probably already have *Git* installed because you cloned this repository. *NodeJS* and *NPM* usually
come together, and they are available from https://nodejs.org/.

You may also need to create a new "inventory file" to tell Ansible to run on your own VMs rather
than ours. Use the "devel" and "production" inventory files in the "playbooks" directory as examples.
Note that the "production" file refers to a host that should be accessible from anywhere, but the
"devel" host is only accessible (with that IP address) on the author's home network. For more
information about inventory files: https://docs.ansible.com/ansible/intro_inventory.html


Post-Install Preparation
------------------------

You must perform a little extra preparation before running the Ansible playbooks.

1. Login as the "root" user.
1. Create a "compadmin" user with a known, secure password.
1. Grant *sudo* access to the "compadmin" user **with the NOPASSWD setting**.
::

    %wheel  ALL=(ALL)       NOPASSWD: ALL

1. Logout from the "root" account and login as "compadmin."
1. Disable root shell access:
    ``sudo /usr/bin/chsh -s /usr/sbin/nologin root``
1. Set the root password to something unknown and arbitrarily complex. The idea is that you will
    never need to access the "root" account, and a very long password makes it harder for attackers.
1. Make your own ".ssh" directory:
::

    $ mkdir ~/.ssh
    $ chmod u=rwX,g=-,o=- ~/.ssh

1. From your own computer, transfer your SSH public key to the server. The playbook disables
    password-based logins later.
::

    $ scp ~/.ssh/id_rsa_key.pub new_server:/home/compadmin/.ssh/authorized_keys

1. Finally, back on the new VM, run a full system update (``sudo yum update -y``). Note that this
    will automatically approve the CentOS package-signing key. When the update has finished, restart
    the VM (``sudo systemctl reboot``).

From this point on, all configuration is run through Ansible.


Run the SSH Playbook
--------------------

Because a failure in the SSH playbook may prevent you from reconnecting via SSH, you should keep an
active session while you run the SSH configuration for the first time. Also note that, when you run
the SSH configuration for the first time, the server will generate new host keys, so you may have to
override the SSH client settings on your own computer *the first time* you connect after running
the playbook.

For example:
::

    $ ssh compadmin@new_host
    ... then in a new terminal window...
    $ cd /path/to/ansible/playbooks
    $ ansible-playbook -i myserver abbot.yml --tags=ssh
    ... when it's done, try it out...
    $ ssh compadmin@new_host

If you can successfully connect to the new VM after the playbook has run, you can go ahead and
close the other SSH session. Remember that you should only see a warning about the SSH host key
changing after the *first* time you run the SSH playbook. After this, no matter how many times you
run the "configure_ssh.yml" playbook, any warnings about the host keys may be a sign of malicious
activity on the server.


Configuration Variables
-----------------------

You may wish to change some of the configuration variables in the ``install_solr.yml`` and
especially the ``install_abbot.yml`` files. Of particular interest are the following in
``install_abbot.yml``:

:abbot_hostname: The server's full hostname, without scheme (the "http" part) or port.
:abbot_port: The port on which the server should listen.
:abbot_drupal_path: The fully-qualified domain name of the associated Drupal installation.
:abbot_version: The git branch, tag, or "committish" object to install on this host.


Run all the Playbooks
---------------------

The rest of the setup doesn't require human intervention. In fact, you don't even have to watch!
::

    $ ansible-playbook -i myserver abbot.yml


Set Initial Data
----------------

The *HolyOrders* script will run immediately following installation, automatically populating the
Solr database with the latest available data from Drupal.

HOWEVER THIS WILL NOT WORK FOR CHANTS, AND I NEED TO FIND A BETTER SOLUTION FOR THAT.


Maintenance
-----------

The Ansible playbooks are designed to be run again, at any time, without causing harm. Ansible only
modifies the target system if it is not already in the desired state. Thus, running Abbot's
playbooks on a system that's already set up will not change the system at all, and running the
playbooks on a system that has been changed, or is in an unknown state, should correct the system
to the state specified in the playbooks.

You may update the version of *Abbot* installed on the server by changing the ``abbot_version``
variable in the ``install_abbot.yml`` playbook and rerunning that playbook. If ``abbot_version`` is
set to a branch name, the playbook will deploy the most recent commit on that branch. If a tag, the
playbook will deploy the tagged commit. In all cases, local modifications to the git repository
are destroyed before deployment.
