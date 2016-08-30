Description
=========

[![Build Status](https://travis-ci.org/Yannik/ansible-role-enable-standard-cronjobs.svg?branch=master)](https://travis-ci.org/Yannik/ansible-role-enable-standard-cronjobs)

This role removes the .disabled extension that hosting companys sometimes adds to default cronjobs to disable them and save cpu cycles. These cronjobs generally exist for a cause and should be run if there is no reason against it.

Requirements
------------

No requirements.

Role Variables
--------------

* `cronjob_enable_blacklist`: list of cronjobs that should not get enabled
* `cronjob_enable_list`: list of cronjobs that should get enabled. only change this if you need to enable more cronjobs in addition to the default ones in `defaults/main.yml`

Example Playbook
----------------

    - hosts: all
      roles:
         - Yannik.enable-standard-cronjobs

    - hosts: all
      roles:
         - { role: Yannik.enable-standard-cronjobs, cronjob_enable_blacklist: ['passwd'] }

License
-------

GPLv2

Author Information
------------------

Yannik Sembritzki
