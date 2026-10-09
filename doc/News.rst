.. _NEWS:

News
####

See :gh:`pyTooling.GitHub Release Pages <pyTooling/pyTooling.GitHub/releases>` for detail release
notes on every release.


Version 0.x (2026)
******************

.. topic:: :gh:`v0.1.0 - unreleased <pyTooling/pyTooling.GitHub/releases/v0.1.0>`

   .. rubric:: New Features

   * First release: pyTooling's GitHub Actions support becomes a package of its own (formerly developed as part of
     :doc:`pyTooling <pyTool:index>` v10.0.0).
   * Data models: :ref:`pipeline runs <DATA/PipelineRun>` read from the GitHub REST API, :ref:`workflow files
     <DATA/Workflow>` and :ref:`action files <DATA/Action>`.
   * The Sphinx domain :ref:`ghactions <GHA>` documents workflows and their parameters from the workflow files.
   * Visualization: the :ref:`pipeline graph <VIS/PipelineGraph>` of a workflow, and the :ref:`trace of a pipeline run
     <VIS/PipelineTrace>` as OTLP/JSON and as a Gantt chart.
   * The program :ref:`pytooling-github <CLI>` reads a pipeline run into a trace, writes it, and draws it.
