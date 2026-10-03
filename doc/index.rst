.. include:: shields.inc

.. image:: _static/logo.png
   :height: 90 px
   :align: center
   :target: https://GitHub.com/pyTooling/pyTooling.GitHub

.. raw:: html

    <br>

.. raw:: latex

   \part{Introduction}

.. only:: html

   |  |SHIELD:svg:GitHub-github| |SHIELD:svg:GitHub-src-license| |SHIELD:svg:GitHub-ghp-doc| |SHIELD:svg:GitHub-doc-license|
   |  |SHIELD:svg:GitHub-pypi-tag| |SHIELD:svg:GitHub-pypi-status| |SHIELD:svg:GitHub-pypi-python|
   |  |SHIELD:svg:GitHub-gha-test| |SHIELD:svg:GitHub-lib-status| |SHIELD:svg:GitHub-codecov-coverage|

.. only:: latex

   |SHIELD:png:GitHub-github| |SHIELD:png:GitHub-src-license| |SHIELD:png:GitHub-ghp-doc| |SHIELD:png:GitHub-doc-license|
   |SHIELD:png:GitHub-pypi-tag| |SHIELD:png:GitHub-pypi-status| |SHIELD:png:GitHub-pypi-python|
   |SHIELD:png:GitHub-gha-test| |SHIELD:png:GitHub-lib-status| |SHIELD:png:GitHub-codecov-coverage|

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

   Used as a layer of pyTooling ➚ <https://pyTooling.github.io/pyTooling/>

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
   Sphinx
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
