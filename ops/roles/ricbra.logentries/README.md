logentries
==========

This role installs and configures the logentries.com agent.

Requirements
------------

Tested on:
- Debian wheezy, jessie
- Ubuntu trusty, precise, wily, vivid
- Centos 6, 7

Role Variables
--------------

Only thing required by this role is your logentries.com account key. But you probably want to follow one or more logs so
an average configration looks like this:

```yml
logentries_account_key: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx"

logentries_logs:
  - name: "Authentication"
    path: "/var/log/auth.log"

```

When you later on want to unfollow a log:

```yml

logentries_logs:
  - name: "Authentication"
    path: "/var/log/auth.log"
    state: absent

```

You may also specify hostname, otherwise `ansible_fqdn` will be used:
```yml
logentries_hostname: my.host.com
```

Alternatively you can specify the key of existing logentries log set:
```yml
logentries_set_key: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

Dependencies
------------

None.

Example Playbook
----------------

Small example of how to use this role in a playbook:

    - hosts: servers
      roles:
         - { role: ricbra.logentries, logentries_account_key: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxx" }

Testing
-------

In the <code>vagrant</code> folder you can test this role against a variety of Linux distros:

    $ cd vagrant && vagrant up

License
-------

MIT

Author Information
------------------

Richard van den Brand
