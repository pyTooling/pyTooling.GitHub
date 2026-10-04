.. _VIS/PipelineGraph:

Pipeline Graph
##############

The jobs of a workflow and their ``needs`` form a graph. The ``gha`` domain draws it in a Sphinx documentation, so the
domain has to be enabled - see :ref:`GHA`.

.. grid:: 2

   .. grid-item::
      :columns: 6

      The ``gha:pipeline-graph`` directive draws the pipeline of a GitHub Actions workflow - its jobs and their
      ``needs`` - from the workflow file itself:

      * a job is a node labelled with its name and the file of the reusable workflow it calls;
      * a job running steps is a grey box with square corners;
      * a job with an ``if`` condition is dashed, and in HTML its tooltip is the condition;
      * a job with a ``strategy.matrix`` is a cluster of its instances, labelled with the matrix' dimensions; an
        instance calling a reusable workflow is drawn as the job calling it. A dynamic matrix - its combinations known
        at run time only - is one node with a double border;
      * a reusable workflow of another repository is a white leaf naming that repository and ref;
      * a reusable workflow of the documented repository is expanded into a cluster of its jobs, as many levels deep
        as ``:depth:`` says - the one an instance of a matrix calls as well;
      * the ``needs`` are the edges, without those a longer path implies.

      The workflow is read with :mod:`pyTooling.GitHub.WorkflowFile`, converted into a :mod:`pyTooling.CI` model
      and its :class:`~pyTooling.Graph.Graph` (:ref:`DATA/Workflow/Pipeline`), and drawn by :mod:`sphinx.ext.graphviz`.
      Every workflow file drawn becomes a dependency of the page.

   .. grid-item::
      :columns: 6

      .. code-block:: ReST

         .. gha:pipeline-graph:: Workflows/Pipeline.yml
            :depth: 1
            :caption: The pipeline of Pipeline.yml.

This is how the example renders, drawn from :download:`Workflows/Pipeline.yml` and
:download:`Workflows/Test.yml`:

.. gha:pipeline-graph:: Workflows/Pipeline.yml
   :depth: 1
   :caption: The pipeline of Pipeline.yml.

.. rst:directive:: .. gha:pipeline-graph:: <path of a workflow file>

   Draws the workflow the argument names, relative to the document.

   .. rst:directive:option:: depth: <levels>

      Levels of reusable workflows of the documented repository to expand into clusters. Default: 0.

   .. rst:directive:option:: direction: LR | TB

      Whether the pipeline flows from left to right or from top to bottom. Default: ``LR``.

   .. rst:directive:option:: reduce: yes | no

      Whether an edge a longer path implies is dropped. Default: ``yes``.

   .. rst:directive:option:: link: yes | no

      Whether a job links to the page documenting its reusable workflow, in HTML. Default: ``yes``.

   .. rst:directive:option:: caption: <text>

      A caption under the graph.

   .. rst:directive:option:: name: <label>

      A label to reference the graph by.

   .. rst:directive:option:: align: left | center | right

      The graph's horizontal alignment.

   .. rst:directive:option:: alt: <text>

      The graph's alternative text. Default: ``Pipeline of <file name>``.

.. _VIS/PipelineGraph/Repository:

The Documented Repository
*************************

A reusable workflow is called by a reference like ``pyTooling/Actions/.github/workflows/Package.yml@r8``.
:file:`conf.py` says which repository the documentation describes, where its workflow files are, and at which ref:

.. code-block:: Python

   # doc/conf.py
   gha_repository =         "pyTooling/Actions"
   gha_workflow_directory = "../.github/workflows"
   gha_ref =                "r8"

The graph reads the configuration values of the domain (:ref:`GHA/Config`), and its workflow files
through the domain, which reads every file once per build:

* The reusable workflows of :confval:`gha_repository` are expanded and linked, whatever the ref they are called at.
  Without it, only local references like ``./.github/workflows/Test.yml`` are.
* Without :confval:`gha_workflow_directory`, they are read from the directory of the drawn workflow file.
* A job calling a reusable workflow of the documented repository at another ref than :confval:`gha_ref` is a warning
  of type ``gha.ref``. Without it, refs aren't checked.

A job links to the page the ``gha`` domain documents its reusable workflow on. Without such a page, and in a format
other than HTML, the job has no link.
