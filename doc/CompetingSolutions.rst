.. _COMPETITORS:

Competing Solutions
###################

Each feature group has competitors solving a part of its task; none of them reads workflow files, action files and
pipeline runs into one model, which a Sphinx domain and the visualizations build on.

Outside Python, :gh:`zizmor <zizmorcore/zizmor>` has typed models of workflows, actions and Dependabot files - the
Rust crate `github-actions-models <https://crates.io/crates/github-actions-models>`__ - and checks a workflow for
security problems, as a template injection or an unpinned action. :gh:`actionlint <rhysd/actionlint>`, written in Go,
checks a file's syntax and expressions, the ``needs`` of its jobs and the inputs of the reusable workflows it calls.
Both are installed from PyPI as command line tools, so a Python program gets their findings, not a model.

A pipeline run becomes a trace by the :gh:`GitHub receiver
<open-telemetry/opentelemetry-collector-contrib/tree/main/receiver/githubreceiver>` of the OpenTelemetry Collector -
fed by GitHub's webhooks, it traces runs as they happen - or by the GitHub Action
:gh:`otel-export-trace-action <inception-health/otel-export-trace-action>`, which exports a finished run to an OTLP
endpoint.


.. _COMPETITORS/Files:

Workflow and Action Files
*************************

No package on PyPI reads a workflow file or an action file into a Python object model. The packages below check a
workflow file, or write one.

.. _COMPETITORS/Files/JSONSchema:

JSON Schema
===========

Source: the schemas of `SchemaStore <https://www.schemastore.org/github-workflow.json>`__, checked by
`check-jsonschema <https://pypi.org/project/check-jsonschema/>`__, compared to :ref:`DATA/Workflow`.

.. rubric:: Disadvantages

* A file is validated against the schema. A program reading it gets nested dictionaries and lists.
* Classes generated from the schema - e.g. by
  `datamodel-code-generator <https://pypi.org/project/datamodel-code-generator/>`__ - are typed, but know neither the
  line of an element nor its parent, and don't check the ``needs`` of a job.

.. rubric:: Advantages

* The schema is used by editors too, so a file is checked the same way while it is written.

.. _COMPETITORS/Files/Generators:

Workflow Generators
===================

Source: `github-actions-cdk <https://pypi.org/project/github-actions-cdk/>`__,
`pygha <https://pypi.org/project/pygha/>`__, compared to :ref:`DATA/Workflow`.

.. rubric:: Disadvantages

* They write a workflow file from Python code, but don't read one.


.. _COMPETITORS/Runs:

Pipeline Runs
*************

The packages below are clients of the whole GitHub REST API, including the endpoints of workflow runs and jobs
:ref:`DATA/PipelineRun` reads. What they return has the shape of the REST API's payloads.

.. _COMPETITORS/Runs/PyGithub:

PyGithub
========

Source: :gh:`PyGithub <PyGithub/PyGithub>`, on PyPI as `PyGithub <https://pypi.org/project/PyGithub/>`__, compared to
:ref:`DATA/PipelineRun` and :ref:`VIS/PipelineTrace`.

.. rubric:: Disadvantages

* Five dependencies: ``pynacl``, ``requests``, ``pyjwt``, ``typing-extensions`` and ``urllib3``.
* `WorkflowRun.jobs() <https://pygithub.readthedocs.io/en/stable/github_objects/WorkflowRun.html>`__ returns a flat
  list of `WorkflowJob <https://pygithub.readthedocs.io/en/stable/github_objects/WorkflowJob.html>`__ objects. The
  called workflows and matrices a job belongs to are only part of its name - ``Caller / Build (ubuntu, 3.14)`` -, and
  a run is not converted into a trace.

.. rubric:: Advantages

* The whole REST API, including writes like re-running a job, and the authentication of a GitHub App.

.. _COMPETITORS/Runs/githubkit:

githubkit
=========

Source: :gh:`githubkit <yanyongyu/githubkit>`, on PyPI as `githubkit <https://pypi.org/project/githubkit/>`__,
compared to :ref:`DATA/PipelineRun`.

.. rubric:: Disadvantages

* Five dependencies: ``anyio``, ``httpx``, ``hishel``, ``typing-extensions`` and ``pydantic``, and the generated
  models in ``githubkit-schemas``.
* Its models are generated from GitHub's description of the REST API, so they type the payloads, but form no tree.

.. rubric:: Advantages

* Synchronous and asynchronous requests, and typed models of every payload.

.. _COMPETITORS/Runs/ghapi:

ghapi
=====

Source: :gh:`ghapi <AnswerDotAI/ghapi>`, on PyPI as `ghapi <https://pypi.org/project/ghapi/>`__, compared to
:ref:`DATA/PipelineRun`.

.. rubric:: Disadvantages

* A thin client: an answer is the payload, as a dictionary with attribute access.

.. rubric:: Advantages

* Every endpoint of the REST API, generated from its description.


.. _COMPETITORS/Domain:

Workflow Documentation
**********************

.. _COMPETITORS/Domain/sphinx-gha:

sphinx-gha
==========

Source: `sphinx-gha <https://sphinx-gha.readthedocs.io/>`__, on PyPI as
`sphinx-gha <https://pypi.org/project/sphinx-gha/>`__, compared to the :ref:`ghactions domain <GHA>`.

.. rubric:: Disadvantages

* What an action's file can't say - an example, an environment variable - is written into the YAML file, as keys
  prefixed with ``x-``.
* Its documentation names neither a graph of the jobs nor summaries of a workflow's permissions or dependencies.

.. rubric:: Advantages

* It documents actions too - the inputs, outputs and environment variables of an :file:`action.yml` -, and writes a
  usage example.
* It runs on Python 3.10 and Sphinx 7.4 or newer.

.. _COMPETITORS/Domain/github-actions-docs:

github-actions-docs
===================

Source: :gh:`github-actions-docs <rzjfr/github-actions-docs>`, on PyPI as
`github-actions-docs <https://pypi.org/project/github-actions-docs/>`__, compared to the :ref:`ghactions domain <GHA>`.

.. rubric:: Disadvantages

* A command line program writing Markdown - a :file:`README.md` next to an action, and for the reusable workflows
  below :file:`.github/workflows` -, not a part of a Sphinx build.
* It requires ``ruamel.yaml <= 0.18.0``, while this package requires ``ruamel.yaml ~= 0.19.1``.

.. rubric:: Advantages

* The :file:`README.md` is rendered by GitHub itself, next to the action.
