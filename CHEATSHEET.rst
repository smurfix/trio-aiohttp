Tips
====

To run tests
------------

* Install requirements: ``pip install -r ci/test-requirements.txt``
  (possibly in a virtualenv)

* Actually run the tests: ``pytest trio_aiohttp``


To run yapf
-----------

* Show what changes yapf wants to make: ``yapf -rpd setup.py
  trio_aiohttp``

* Apply all changes directly to the source tree: ``yapf -rpi setup.py
  trio_aiohttp``


To make a release
-----------------

* Update the version in ``trio_aiohttp/_version.py``

* Run ``towncrier`` to collect your release notes.

* Review your release notes.

* Check everything in.

* Double-check it all works, docs build, etc.

* Build your sdist and wheel: ``python setup.py sdist bdist_wheel``

* Upload to PyPI: ``twine upload dist/*``

* Use ``git tag`` to tag your version.

* Don't forget to ``git push --tags``.
