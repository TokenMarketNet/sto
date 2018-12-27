Developer notes
===============

Information for package developers.

Making a release
----------------

Instructions for the future-maintainers-to-be.

First send out PyPi release:

.. code-block:: shell

    export bump="--new-version 0.1.1 devnum"
    make release

Then push out new Docker:

.. code-block:: shell

    VERSION=0.2.0
    docker login --username=miohtama
    docker build -t miohtama/sto:latest .

    # Test run
    docker run -p 8545:8545 -v `pwd`:`pwd` -w `pwd` miohtama/sto:latest --help

    # Push the release to hub
    docker tag miohtama/sto:latest miohtama/sto:$VERSION
    docker push miohtama/sto:$VERSION && docker push miohtama/sto:latest