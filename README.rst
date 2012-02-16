Welcome to Kiki's documentation!
================================

Kiki is envisioned as a Django-based mailing list manager which can replace Mailman.

Why replace Mailman?
++++++++++++++++++++

Mailman is a grand old thing. However, there are some major sticking points, which Kiki tries to resolve.

+--------------------------------------+--------------------------------------+
| Mailman                              | Kiki                                 |
+======================================+======================================+
| Install requires root access and     | Django package. Can be installed     |
| a build step.                        | simply and locally.                  |
+--------------------------------------+--------------------------------------+
| Includes C modules.                  | Pure Python.                         |
+--------------------------------------+--------------------------------------+
| Only accessible through its own web  | Integrates with the ``django`` admin |
| interface, and authentication is     | and provides default urls, views,    |
| baked in.                            | and templates.                       |
+--------------------------------------+--------------------------------------+
| Uses a private database for Users.   | Integrates with the Users already    |
|                                      | on your site.                        |
+--------------------------------------+--------------------------------------+
| Documents are wiki-based or not      | Sphinx documentation is in a         |
| easily buildable.                    | separate directory from the code.    |
|                                      | You can also find the docs           |
|                                      | `on readthedocs.org`_.               |
+--------------------------------------+--------------------------------------+
| Message queueing baked in.           | Uses ``django-celery`` for queues.   |
+--------------------------------------+--------------------------------------+

.. _on readthedocs.org: http://readthedocs.org/docs/kiki