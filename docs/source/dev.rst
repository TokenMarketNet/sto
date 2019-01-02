Developer notes
===============

Information for package developers.

Making a release
----------------

Instructions for the future-maintainers-to-be.

First send out PyPi release:

.. code-block:: shell

    # Build and upload PyPi egg
    VERSION=0.2.0
    make release

Then push out new Docker:

.. code-block:: shell

    # Build docker image
    docker login --username=miohtama
    make publish-docker