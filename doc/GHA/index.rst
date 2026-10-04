.. _GHA:

Overview
########

The Sphinx domain ``gha`` documents **GitHub Actions workflows** - above all reusable workflows, whose inputs, outputs
and secrets are the interface a caller uses. What the workflow file states - an input's type, whether it is required,
its default - is read from the file with :mod:`pyTooling.GitHub.WorkflowFile`, so a page doesn't copy it and can't
drift from it. What the file can't say stays hand-written, as the content of a directive.

The domain is the Sphinx extension :mod:`pyTooling.GitHub.Sphinx`. It builds on
`pyTooling.Sphinx <https://pyTooling.github.io/pyTooling.Sphinx/Extension.html>`__, which it sets up itself, and is
installed with the extra ``sphinx``: ``pyTooling.GitHub[sphinx]``.

.. code-block:: Python

   # doc/conf.py
   extensions = [
     ...,
     "pyTooling.GitHub.Sphinx",
   ]

The domain's directives are described on three pages:

:ref:`GHA/Workflow`
  |rarr| ``gha:workflow`` and the entries of its inputs, outputs and secrets, and the roles referring to them.
:ref:`GHA/Summaries`
  |rarr| Tables, the interface, the dependencies and YAML excerpts of a workflow.
:ref:`VIS/PipelineGraph`
  |rarr| ``gha:pipeline-graph`` draws a workflow's jobs and their ``needs``.

.. contents:: Contents of this page
   :local:
   :depth: 1


.. _GHA/Config:

Configuration
*************

.. code-block:: Python

   # doc/conf.py
   gha_repository =         "pyTooling/Actions"      # the documented repository
   gha_workflow_directory = "../.github/workflows"   # relative to the Sphinx source directory
   gha_ref =                "r8"                     # the ref the documentation describes

.. confval:: gha_workflow_directory

   The directory holding the workflow files, relative to the Sphinx source directory. A ``gha:workflow`` without
   ``:file:`` reads ``<name>.yml`` from it. Default: ``None``.

.. confval:: gha_repository

   The documented repository, as ``owner/repo``. A job calling ``owner/repo/.github/workflows/X.yml@<ref>`` is resolved
   to ``X.yml`` in :confval:`gha_workflow_directory`, whatever the ref. Default: ``None``.

.. confval:: gha_ref

   The ref - a branch or tag - of the documented repository the documentation describes, as ``r8``. A job calling a
   workflow of the documented repository at another ref is a warning. ``None`` checks nothing. Default: ``None``.

.. confval:: gha_server

   The URL of the GitHub server the links of :rst:dir:`gha:yaml`, :rst:dir:`gha:interface` and
   :rst:dir:`gha:dependencies` point to: ``https://github.com``, or a GitHub Enterprise Server's, as
   ``https://github.example.com``. Default: ``"https://github.com"``.

.. confval:: gha_label_prefix

   The root of the ``:ref:`` labels the directives register besides their targets - see
   :ref:`GHA/Labels`. ``None`` registers none. Default: ``"JOBTMPL"``.


.. _GHA/Labels:

Labels of Existing Pages
************************

Besides its target, each directive registers the ``:ref:`` label a page would have declared by hand, so existing
references keep working when a page is converted - :confval:`gha_label_prefix` is their root:

.. code-block:: text

   JOBTMPL/Parameters                          .. gha:workflow:: Parameters
   JOBTMPL/Parameters/Input/package_name       .. gha:input:: package_name
   JOBTMPL/Parameters/Output/python_jobs       .. gha:output:: python_jobs
   JOBTMPL/PublishOnPyPI/Secret/PYPI_TOKEN     .. gha:secret:: PYPI_TOKEN

A parameter's section carries the anchor of its label, and the anchor docutils derives from its title, so a link into
the hand-written page lands on the same entry. A label still declared by hand next to the directive is a duplicate.


.. _GHA/Warnings:

Warnings
********

The page and the workflow file are compared while the page is read. A difference is a warning of type
``gha.drift``, so ``-W`` fails the build, and ``suppress_warnings = ["gha.drift"]`` silences it. Where the problem is
in the file, the warning names the place in the file, as ``Package.yml:8``.

* An input is required and has a default, which is never used - named in the workflow file.
* A ``gha:input``, ``gha:output`` or ``gha:secret`` names a parameter the workflow doesn't have.
* A hand-written *Type*, *Required* or *Default Value* of an input or a secret repeats a fact of the workflow file.
  It is not shown; the file's value is.
* An input has no entry in the document - neither a ``gha:input`` nor a ``gha:autoinputs`` - reported at the
  ``gha:workflow`` when the whole document was read.
* A ``gha:yaml`` names a job the workflow doesn't have, or a section the workflow has nothing in.

A workflow file that can't be found or read is a warning of type ``gha.workflow``, as is a ``gha:input`` or a summary
directive without a preceding ``gha:workflow``.


.. _GHA/API:

Extending the Domain
********************

A directive of another module reaches the domain with ``self.env.get_domain("gha")``, a
:class:`~pyTooling.GitHub.Sphinx.GitHubActionsDomain`:

* :meth:`~pyTooling.GitHub.Sphinx.GitHubActionsDomain.GetCurrentWorkflow` returns the model of
  the document's current workflow, a :class:`pyTooling.GitHub.WorkflowFile.Workflow`;
* :attr:`~pyTooling.GitHub.Sphinx.GitHubActionsDomain.Resolver` reads the workflows a job calls,
  every file once;
* :meth:`~pyTooling.GitHub.Sphinx.GitHubActionsDomain.ResolveWorkflow` says where a workflow is
  documented;
* :meth:`ParameterDirective.CreateEntry <pyTooling.GitHub.Sphinx.ParameterDirective.CreateEntry>`
  creates a parameter's entry and registers it, as ``gha:autoinputs`` does.

A directive is added to the domain with
:meth:`Sphinx.add_directive_to_domain <sphinx.application.Sphinx.add_directive_to_domain>`.
