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


.. attention::

   pyTooling.GitHub requires **Python 3.11 or newer**. The Sphinx domain ``gha`` requires pyTooling.Sphinx, and thus
   Python 3.12 or newer.

The package is installed from PyPI, with the extras ``diagram`` (matplotlib, for Gantt charts) and ``sphinx``
(pyTooling.Sphinx, for the domain ``gha``):

.. code-block:: bash

   pip install pyTooling.GitHub[diagram,sphinx]

The domain is enabled in :file:`conf.py`; it sets up pyTooling.Sphinx itself:

.. code-block:: Python

   # doc/conf.py
   extensions = [
     ...,
     "pyTooling.GitHub.Sphinx",
   ]


.. _HIGHLIGHTS:

Features
********

.. rubric:: Data models

:ref:`Workflow runs <DATA/Run>`
  |rarr| A GitHub Actions workflow run - pipeline, workflows, matrices, jobs and steps with their times and outcomes -
  read from the GitHub REST API's payloads.
:ref:`Workflow files <DATA/Workflow>`
  |rarr| A workflow file: triggers, inputs, outputs, secrets, permissions and jobs with their dependencies, read with
  line numbers, and converted into a pipeline graph.

.. rubric:: Traces

:ref:`GitHub Actions trace reader <TRACING/CI/GitHub>`
  |rarr| Reads a workflow run through the GitHub REST API into a trace, written as OpenTelemetry's OTLP/JSON.

.. rubric:: Sphinx domain ``gha``

:ref:`Workflows and their parameters <GHA/Workflow>`
  |rarr| ``gha:workflow``, ``gha:input``, ``gha:output``, ``gha:secret`` and ``gha:autoinputs``, taken straight from
  the workflow file; roles to reference them.
:ref:`Tables and listings <GHA/ParameterTable>`
  |rarr| ``gha:parameter-table``, ``gha:interface``, ``gha:dependencies`` and ``gha:yaml``.
:ref:`Pipeline graph <GHA/PipelineGraph>`
  |rarr| ``gha:pipeline-graph`` draws the jobs of a workflow and their ``needs`` as a Graphviz graph, with the
  reusable workflows it calls expanded.

.. rubric:: Program

:ref:`pytooling-github <CLI>`
  |rarr| The command ``pipeline`` reads a pipeline run into a trace, writes it, and draws it as a Gantt chart.


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
