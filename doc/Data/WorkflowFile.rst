.. _DATA/Workflow:

Workflow File
#############

:mod:`pyTooling.GitHub.WorkflowFile` models a **GitHub Actions workflow file** - the YAML file below
:file:`.github/workflows`, not a run of it (that's :ref:`DATA/PipelineRun`). The actions its steps run are read by the
same module, see :ref:`DATA/Action`:

.. code-block:: python

   from pathlib import Path
   from pyTooling.GitHub.WorkflowFile import Workflow

   workflow = Workflow.FromFile(Path(".github/workflows/CompletePipeline.yml"))

   print(f"{workflow.Name}: {len(workflow.Inputs)} inputs, {workflow.JobCount} jobs")
   for job in workflow.IterateJobs():
     print(f"  {job.Name:<24} {job.Uses or job.RunsOn}  needs {', '.join(job.NeedNames)}")

The file is read with ``ruamel.yaml``, a requirement of this package.


.. _DATA/Workflow/Tree:

The Tree
********

.. code-block:: text

   Workflow                 a workflow file
   +-- Input                an input of 'on.workflow_call'
   +-- Output               an output of 'on.workflow_call'
   +-- Secret               a secret of 'on.workflow_call'
   +-- Permission           a permission the workflow declares
   +-- Job                  a job, in file order
       +-- UsesReference    the reusable workflow the job calls
       +-- Permission       a permission the job declares
       +-- Matrix           the job's 'strategy.matrix'
       +-- Step             a step of the job
           +-- UsesReference    the action the step runs

* A workflow is named by its file's stem - ``CompletePipeline`` - because a caller names it that way in ``uses``.
  The ``name`` key is :attr:`~pyTooling.GitHub.WorkflowFile.Workflow.DisplayName`.
* An input keeps the type its default is written with - ``'3.14'`` is a string, ``false`` a boolean - and a
  multi-line default keeps its line breaks.
* A job either runs steps on :attr:`~pyTooling.GitHub.WorkflowFile.Job.RunsOn`, or calls the reusable workflow in
  :attr:`~pyTooling.GitHub.WorkflowFile.Job.Uses`. :class:`~pyTooling.GitHub.WorkflowFile.UsesReference` takes a
  reference apart into :attr:`~pyTooling.GitHub.WorkflowFile.UsesReference.Repository`,
  :attr:`~pyTooling.GitHub.WorkflowFile.UsesReference.Path` and
  :attr:`~pyTooling.GitHub.WorkflowFile.UsesReference.Reference`:

  .. code-block:: text

     pyTooling/Actions/.github/workflows/Package.yml@r8   repository, path and ref
     ./.github/workflows/Package.yml                       a file of the same repository and commit

* :attr:`Matrix.IsDynamic <pyTooling.GitHub.WorkflowFile.Matrix.IsDynamic>` says whether a matrix' instances are
  known at run time only, as for ``include: ${{ fromJson(inputs.jobs) }}``.
* A job's :attr:`~pyTooling.GitHub.WorkflowFile.Job.Container` and
  :attr:`~pyTooling.GitHub.WorkflowFile.Job.Services` are the images of the containers it runs in.
* Expressions - ``if``, ``runs-on: ${{ matrix.runs-on }}``, an output's ``value`` - are kept as written and are
  not evaluated.


.. _DATA/Workflow/Lines:

Source Lines
************

Every element knows the file it was read from and the line it starts at, so a message
can say where a finding comes from:

.. code-block:: python

   job = workflow.Jobs["PublishOnPyPI"]
   print(f"{job.Location}: job '{job.Name}' has a condition")   # CompletePipeline.yml:532: ...

A file that is not a well-formed workflow - a job needing a job the workflow doesn't have, jobs needing each other in a
cycle, an input without ``type`` - raises :exc:`~pyTooling.GitHub.WorkflowFile.WorkflowError`. It carries the file
and the line in :attr:`~pyTooling.GitHub.WorkflowFile.WorkflowError.Path` and
:attr:`~pyTooling.GitHub.WorkflowFile.WorkflowError.Line`, and names both in a note.


.. _DATA/Workflow/Graph:

Dependencies Between Jobs
*************************

:attr:`Job.Needs <pyTooling.GitHub.WorkflowFile.Job.Needs>` resolves the names of ``needs`` to the jobs. The pipeline
they form is built by :meth:`~pyTooling.GitHub.WorkflowFile.Workflow.ToPipeline` (see :ref:`DATA/Workflow/Pipeline`)
and converted into a :class:`~pyTooling.Graph.Graph` by :meth:`~pyTooling.CI.Workflow.ToGraph`, whose edges read
*needs*, and which by default drops a dependency a longer path already implies:

.. code-block:: text

   Package  needs Prepare               Local --> Package --> Prepare
   Local    needs Prepare, Package
                                        (Local --> Prepare is implied)


.. _DATA/Workflow/Resolver:

Called Workflows
****************

A job calling a reusable workflow names it by repository, path and ref.
:class:`~pyTooling.GitHub.WorkflowFile.WorkflowResolver` reads the called file from a local directory, mapped per
repository, whatever the ref:

.. code-block:: python

   from pyTooling.GitHub.WorkflowFile import WorkflowResolver

   resolver = WorkflowResolver({"pyTooling/Actions": Path(".github/workflows")})
   pipeline = resolver.Load(Path(".github/workflows/CompletePipeline.yml"))

   for job in pipeline.IterateJobs():
     if job.Uses is not None and (called := resolver.Resolve(job.Uses)) is not None:
       print(f"{job.Name} calls {called.Name} with {called.JobCount} jobs")

* A local reference - ``./.github/workflows/Package.yml`` - is read from the directory of the calling workflow.
* A repository without a directory answers ``None``: its files are not fetched.
* Every file is read once; resolving it again returns the same :class:`~pyTooling.GitHub.WorkflowFile.Workflow`.

The resolver reads the actions the steps run too - see :ref:`DATA/Action/Resolver`.


.. _DATA/Workflow/Permissions:

Permissions
***********

A called workflow can keep or reduce the permissions of the ``GITHUB_TOKEN``, never raise them, so what its jobs declare
is what a caller has to grant. :meth:`~pyTooling.GitHub.WorkflowFile.Workflow.CollectPermissions` collects the
permissions a workflow and its jobs declare, and - given a resolver - those of the workflows they call:

.. code-block:: python

   for scope, permission in pipeline.CollectPermissions(resolver).items():
     print(f"{permission}   asked for at {permission.Location}")

   # contents: write   asked for at CompletePipeline.yml:500
   # pages: write      asked for at PublishToGitHubPages.yml:67

When several elements declare a scope, the permission granting the most access is returned, so its location names
where that access is asked for.


.. _DATA/Workflow/Pipeline:

Building a Pipeline
*******************

:meth:`~pyTooling.GitHub.WorkflowFile.Workflow.ToPipeline` builds the pipeline a workflow defines as a
:mod:`pyTooling.CI` model (`pyTooling's pipeline model <https://pyTooling.github.io/pyTooling/CI/Pipeline.html>`__),
expanding the workflows its jobs call as far as a resolver reads them and ``depth`` allows:

.. code-block:: python

   pipeline = workflow.ToPipeline(resolver, depth=1)
   graph =    pipeline.ToGraph()                       # transitively reduced

   for vertex in graph.IterateTopologically():         # in an order the jobs can run in
     element = vertex.Value
     print(f"{element.QualifiedName}  {element.Definition.Location}")

.. list-table::
   :header-rows: 1
   :widths: 35 65

   * - Job in the workflow file
     - Element of the pipeline
   * - with ``steps``
     - :class:`~pyTooling.GitHub.WorkflowFile.DefinedJob`, its steps as
       :class:`~pyTooling.GitHub.WorkflowFile.DefinedStep`
   * - with ``uses``
     - :class:`~pyTooling.GitHub.WorkflowFile.DefinedWorkflow`, the ``uses`` text as
       :attr:`~pyTooling.CI.Workflow.Reference`, holding the elements of the called workflow - or none, if
       the call isn't expanded
   * - with ``strategy.matrix``
     - :class:`~pyTooling.GitHub.WorkflowFile.DefinedMatrix`, holding a
       :class:`~pyTooling.GitHub.WorkflowFile.DefinedMatrixJob` - or a
       :class:`~pyTooling.GitHub.WorkflowFile.DefinedMatrixWorkflow` for a job with ``uses`` - per combination
   * - ``needs``
     - :attr:`~pyTooling.CI.DependencyMixin.Needs` between the elements
   * - ``if``
     - :attr:`~pyTooling.CI.ConditionMixin.Condition`

* An element is named by its job's key, as the file names it in ``needs``. A step is named as GitHub displays it:
  by its ``name``, or ``Run`` followed by its action or the first line of its script.
* Every element links to what it was built from: :attr:`~pyTooling.GitHub.WorkflowFile.DefinitionMixin.Definition` is
  the :class:`~pyTooling.GitHub.WorkflowFile.Job` - with its line, its ``uses`` reference and its permissions - or
  the :class:`~pyTooling.GitHub.WorkflowFile.Step`, and for the pipeline the
  :class:`~pyTooling.GitHub.WorkflowFile.Workflow`. A called workflow's
  :attr:`~pyTooling.GitHub.WorkflowFile.CallMixin.CalledWorkflow` is the file it was expanded from.
* A matrix yields its combinations as GitHub computes them from its dimensions, ``exclude`` and ``include`` -
  :attr:`Matrix.Combinations <pyTooling.GitHub.WorkflowFile.Matrix.Combinations>` -, and an instance is named by its
  values: ``Test (ubuntu, 3.14)``. Its :attr:`~pyTooling.CI.MatrixInstanceMixin.Dimensions` are the combination, the
  values formatted as GitHub prints them: ``{"os": "ubuntu", "python": "3.14"}``. A **dynamic** matrix -
  ``include: ${{ fromJson(...) }}`` - is a :class:`~pyTooling.GitHub.WorkflowFile.DefinedMatrix` without instances,
  since its combinations are known at run time only.
* A workflow calling itself, directly or through others, raises :exc:`~pyTooling.GitHub.WorkflowFile.WorkflowError`.


.. _DATA/Workflow/Run:

Linking a Run
*************

A run read from the GitHub REST API (:ref:`DATA/PipelineRun`) has no ``needs``: the API doesn't report them.
:meth:`~pyTooling.GitHub.WorkflowFile.Workflow.ApplyNeeds` gives a run the dependencies its workflow file - named by
:attr:`Pipeline.Path <pyTooling.GitHub.Pipeline.Path>` - declares:

.. code-block:: python

   run =      Pipeline.FromJSON(runJSON, jobsJSON)
   workflow = resolver.Load(Path(run.Path))

   for name in workflow.ApplyNeeds(run, resolver):
     print(f"Job '{name}' isn't in the run.")

   graph = run.ToGraph()

* A job is looked up in the run by its display name - its ``name`` -, or else by its key:
  :pycode:`group.GetElement(name)`. A matrix is found as the :class:`~pyTooling.CI.Matrix` its instances were grouped
  into.
* A job calling a reusable workflow is followed into the run's called workflow, and a matrix of calls into each
  instance, as far as the resolver reads the called file.
* A run names an instance's dimensions by position - ``{"0": "ubuntu", "1": "3.14"}`` -, since a job's name carries
  the values only. For a static matrix, an instance whose values are those of a combination gets the combination's
  names: ``{"os": "ubuntu", "python": "3.14"}``. The instances of a dynamic matrix, and one matching no combination,
  keep the positions.
* A job named by an expression - ``${{ matrix.os }} Tests`` - can't be looked up and is skipped. A job with a
  condition may have been skipped in the run, so it isn't reported when it's missing. Every other job missing in the
  run is returned by its qualified name, as the run would name it: ``Local / Static`` for the job ``Static`` of the
  workflow the job ``Local`` calls.
