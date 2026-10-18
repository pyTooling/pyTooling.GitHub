.. _GLOSSARY:

Glossary
########

.. glossary::

   Action
     A unit of work a :term:`step` runs with ``uses``, described by its file :file:`action.yml` - see GitHub's
     `metadata syntax <https://docs.github.com/en/actions/reference/workflows-and-actions/metadata-syntax>`__. It runs
     JavaScript, a Docker container, or steps of its own (:term:`composite action`). See :ref:`DATA/Action`.

   Composite Action
     An :term:`action` running :term:`steps <step>` of its own - ``runs.using: composite``. See GitHub's
     `custom actions <https://docs.github.com/en/actions/concepts/workflows-and-actions/custom-actions>`__.

   Domain
     A `Sphinx domain <https://www.sphinx-doc.org/en/master/usage/domains/index.html>`__ groups the directives and roles
     describing objects of one kind, under a name like ``py`` or ``ghactions``. See :ref:`GHA`.

   DOT
     The `graph description language <https://graphviz.org/doc/info/lang.html>`__ of Graphviz, which the
     :ref:`pipeline graph <VIS/PipelineGraph>` is written in.

   Gantt Chart
     A bar chart of timespans on a time axis, a row per task. See :ref:`VIS/PipelineTrace/Gantt`.

     Wikipedia: :wiki:`Gantt chart <Gantt_chart>`

   GITHUB_TOKEN
     The token GitHub creates for every workflow run, with the
     `permissions <https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#permissions>`__
     the workflow and its jobs declare. See GitHub's
     `GITHUB_TOKEN <https://docs.github.com/en/actions/concepts/security/github_token>`__.

   Job
     A set of :term:`steps <step>` running on one :term:`runner`, or a call of a :term:`reusable workflow`. Jobs run in
     parallel unless they :term:`need <needs>` each other. See GitHub's
     `workflow syntax <https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax>`__.

   Matrix
     A job's ``strategy.matrix``: the job runs once per combination of the matrix' dimensions. See GitHub's
     `job variations
     <https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/run-job-variations>`__.

   Needs
     The jobs a :term:`job` depends on, which have to complete before it starts. See GitHub's
     `jobs.<job_id>.needs
     <https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax#jobsjob_idneeds>`__.

   OTLP
     The `OpenTelemetry Protocol <https://opentelemetry.io/docs/specs/otlp/>`__, which carries :term:`traces <trace>`
     to a collector or viewer; its JSON encoding is OTLP/JSON. See :ref:`VIS/PipelineTrace`.

   Pipeline
   Workflow Run
     One run of a :term:`workflow`, with the jobs it ran, read from GitHub's REST API - its
     `workflow runs <https://docs.github.com/en/rest/actions/workflow-runs>`__ and
     `workflow jobs <https://docs.github.com/en/rest/actions/workflow-jobs>`__. See :ref:`DATA/PipelineRun`.

   Reusable Workflow
     A :term:`workflow` triggered by ``on.workflow_call``, which a :term:`job` of another workflow calls with ``uses``,
     passing inputs and secrets. See GitHub's
     `reusable workflows <https://docs.github.com/en/actions/concepts/workflows-and-actions/reusable-workflows>`__.

   Runner
     The machine a :term:`job` runs on, requested by the labels in ``runs-on``. See GitHub's
     `runners <https://docs.github.com/en/actions/concepts/runners>`__.

   Span
     A timespan of a :term:`trace`, with a name, a begin and an end, attributes, and the spans below it. See
     OpenTelemetry's `traces <https://opentelemetry.io/docs/concepts/signals/traces/>`__.

   Step
     A task of a :term:`job` or a :term:`composite action`: a script in ``run``, or an :term:`action` in ``uses``.

   Trace
     A tree of :term:`spans <span>` recording where time went. The trace of a :term:`pipeline` has a span for every
     called workflow, matrix, job and step, with the attributes of OpenTelemetry's
     `semantic conventions for CI/CD <https://opentelemetry.io/docs/specs/semconv/registry/attributes/cicd/>`__.
     See :ref:`VIS/PipelineTrace`.

   Workflow
     A YAML file below :file:`.github/workflows` describing what runs when it is triggered: its jobs, and the
     :term:`steps <step>` of each. See GitHub's
     `workflows <https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows>`__ and
     :ref:`DATA/Workflow`.
