.. raw:: latex

   \part{Introduction}

.. shields::
   :github:                pyTooling/pyTooling.GitHub
   :pypi:                  pyTooling.GitHub
   :codacy:                e56604e36cf04f6090e0b171e948c1fa
   :source-license:        github:LICENSE.md
   :documentation-license: CC-BY-4.0 github:doc/Doc-License.rst
   :github-action:         Pipeline.yml@main
   :documentation:         github-pages

   github, src-license, ghp-doc, doc-license
   pypi-tag, pypi-status, pypi-python
   github-action, lib-status, codacy-quality, codacy-coverage, codecov-coverage

--------------------------------------------------------------------------------

The pyTooling.GitHub Documentation
##################################

**pyTooling.GitHub** works with GitHub Actions pipelines: it reads workflow and action files into a data model,
reads the runs of a pipeline from GitHub's REST API, and converts them into traces - e.g. OpenTelemetry's OTLP/JSON
or a Gantt chart of the jobs and steps. A Sphinx domain ``gha`` documents workflows and their inputs, outputs and
secrets taken straight from the workflow files.

It builds on `pyTooling <https://GitHub.com/pyTooling/pyTooling>`__'s generic CI pipeline model and tracing, and on
`pyTooling.Sphinx <https://GitHub.com/pyTooling/pyTooling.Sphinx>`__ for its documentation extensions.


.. _CONTRIBUTORS:

Contributors
************

* :gh:`Patrick Lehmann <Paebbels>` (Maintainer)
* `and more... <https://GitHub.com/pyTooling/pyTooling.GitHub/graphs/contributors>`__


.. _LICENSE:

License
*******

.. only:: html

   This Python package (source code) is licensed under `Apache License 2.0 <License.html>`__. |br|
   The accompanying documentation is licensed under
   `Creative Commons - Attribution 4.0 (CC-BY 4.0) <Doc-License.html>`__.

.. only:: latex

   This Python package (source code) is licensed under **Apache License 2.0**. |br|
   The accompanying documentation is licensed under **Creative Commons - Attribution 4.0 (CC-BY 4.0)**.


.. toctree::
   :hidden:

   Subnamespace of pyTooling ➚ <https://pyTooling.github.io/pyTooling/>

.. toctree::
   :caption: Introduction
   :hidden:

   Installation

.. toctree::
   :caption: Features
   :hidden:

   Run
   WorkflowFile
   Tracing
   GHA/index
   CLI

.. raw:: latex

   \part{References and Reports}

.. toctree::
   :caption: References and Reports
   :hidden:

   Python Class Reference <pyTooling.GitHub/pyTooling.GitHub>

.. raw:: latex

   \part{Appendix}

.. toctree::
   :caption: Appendix
   :hidden:

   License
   Doc-License
   genindex
   Python Module Index <modindex>
