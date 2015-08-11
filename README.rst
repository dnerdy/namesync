namesync |build-status| |python-versions|
==============================================

Sync DNS records stored in a flat file format to your DNS provider. Cloudflare support currently provided.

.. |build-status| image:: https://secure.travis-ci.org/dnerdy/namesync.svg?branch=master
    :alt: Build Status
    :target: http://travis-ci.org/dnerdy/namesync

.. |python-versions| image:: https://img.shields.io/badge/python-2.7_3.4-blue.svg
    :alt: Python Versions

Installation |pypi-version|
---------------------------

::

    $ pip install namesync

.. |pypi-version| image:: https://img.shields.io/pypi/v/namesync.svg
    :alt: PyPI Version
    :target: http://pypi.python.org/pypi/namesync

Quick Guide
-----------

Create a file with the name of your domain::
    
    $ touch example.com

Or, if you have existing records, you can export them::

    $ namesync --get example.com

Enter one record per line with the following format::
   
   <record-type> <name> <value> <ttl:optional>

For example::

    A       *       10.10.10.10         # You can even use comments
    A       .       10.10.10.10         # . references the domain itself, example.com
    A       test    10.10.10.11
    A       example 10.10.10.12 86400
    CNAME   mail    ghs.googlehosted.com
    MX      .       aspmx.l.google.com

MX records allow you to specify a priority::

   MX <name> <value> <priority:optional> <ttl:optional>

Like this::

    MX      .       alt1.aspmx.l.google.com 20
    MX      .       aspmx3.googlemail.com 30 86400

If the value contains spaces, quote it::

    TXT     .       "v=spf1 a include:amazonses.com include:_spf.google.com ~all"

Then sync your records::

   $ namesync example.com

You will be given a chance to review your changes before they are synced::

   The following changes will be made:
   ADD    A     *       10.10.10.10
   ADD    A     example 10.10.10.12 86400
   ADD    A     test    10.10.10.11
   ADD    CNAME mail    ghs.googlehosted.com
   ADD    MX    .       aspmx.l.google.com
   UPDATE A     .       10.10.10.10
   REMOVE A     old     10.10.10.13
   Do you want to continue? [y/N] 

Usage
-----

::

    usage: namesync [-h] [-g] [-z ZONE] [-y] [-d DATA_DIR] [-t] RECORDS

    positional arguments:
      RECORDS               file containing DNS records, one per line. The zone is
                            derived from the basename of this file. For example,
                            if "dns/example.com" is used then the zone is assumed
                            to be "example.com" unless the --zone option is used

    optional arguments:
      -h, --help            show this help message and exit
      -g, --get             save existing DNS records to RECORDS
      -z ZONE, --zone ZONE  specify the zone instead of using the RECORDS filename
      -y, --yes             sync records without prompting before making changes
      -d DATA_DIR, --data-dir DATA_DIR
                            the directory where namesync.conf and other cache data
                            is stored. [default: ~/.namesync]
      -t, --dry-run         print actions and exit without making any changes
