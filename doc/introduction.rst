.. _introduction:

************
Introduction
************

Umwelt is a package manager. Using Umwelt you can fetch and create run-time
environments configured for a given set of packages.

However, unlike in other package managers, packages are not installed into
these standalone environments (:term:`pip`, :term:`npm`) or into a central
repository (:term:`REZ`). Instead the install location of the packages on the
server stays untouched and is being managed by a :term:`registry` instead.
