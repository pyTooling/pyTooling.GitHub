.. _DATA/Action:

Action File
###########

:mod:`pyTooling.GitHub.WorkflowFile` models a **GitHub Actions action file** too - the :file:`action.yml` a step runs
with ``uses``:

.. code-block:: python

   from pathlib import Path
   from pyTooling.GitHub.WorkflowFile import Action

   action = Action.FromFile(Path(".github/actions/CheckArtifactNames/action.yml"))

   print(f"{action.Name} ({action.Using}): {action.StepCount} steps")
   for step in action.IterateSteps():
     print(f"  {step.Location:<16} {step.Name}")

.. code-block:: text

   CheckArtifactNames (composite): 2 steps
     action.yml:21    Install dependencies
     action.yml:25    Check artifact names


.. _DATA/Action/Tree:

The Tree
********

.. tree::

   - :class:`~pyTooling.GitHub.WorkflowFile.Action`            | an action's file, :file:`action.yml`
     - :class:`~pyTooling.GitHub.WorkflowFile.Step`            | a step of a composite action
       - :class:`~pyTooling.GitHub.WorkflowFile.UsesReference` | the action the step runs

* An action is named by its directory - ``ComputeRequirements`` for
  :file:`.github/actions/ComputeRequirements/action.yml` -, because a step names it that way in ``uses``. The ``name``
  key is :attr:`~pyTooling.GitHub.WorkflowFile.Action.DisplayName`.
* :attr:`~pyTooling.GitHub.WorkflowFile.Action.Using` is how the action runs - ``runs.using``, as ``composite``,
  ``docker`` or ``node24``:

  * Of a **composite** action (:attr:`~pyTooling.GitHub.WorkflowFile.Action.IsComposite`), the
    :attr:`~pyTooling.GitHub.WorkflowFile.Action.Steps` are read, so
    :meth:`~pyTooling.GitHub.WorkflowFile.Action.IterateActions` yields the actions it runs in turn.
  * Of a **Docker** action, the :attr:`~pyTooling.GitHub.WorkflowFile.Action.Image` it runs - ``Dockerfile`` or
    ``docker://alpine:3.22``.

* A step of an action is a :class:`~pyTooling.GitHub.WorkflowFile.Step`, as a step of a job is - with its ``name``,
  ``id``, ``if``, and the action in ``uses`` or the script in ``run``.
* An action's ``inputs`` and ``outputs`` aren't read.

An action is the root of its file's elements: assigning it a parent raises a :exc:`TypeError`. Every element knows the
line it starts at, and a file that isn't a well-formed action - no ``runs`` key, or no ``runs.using`` - raises
:exc:`~pyTooling.GitHub.WorkflowFile.WorkflowError`, naming the file and the line.


.. _DATA/Action/Resolver:

Actions a Step Runs
*******************

:meth:`~pyTooling.GitHub.WorkflowFile.WorkflowResolver.ResolveAction` reads the action a step runs from its
:file:`action.yml`, as :meth:`~pyTooling.GitHub.WorkflowFile.WorkflowResolver.Resolve` reads a called workflow (see
:ref:`DATA/Workflow/Resolver`), so the actions a composite action runs in turn are known:

* An action of a mapped repository - ``pyTooling/Actions/.github/actions/ComputeRequirements@r8`` - is read from the
  repository's root, the directory holding the ``.github`` directory the mapped directory is in.
* A local action - ``./.github/actions/ComputeRequirements`` - is read from the root of the repository of the calling
  workflow or action.
* :meth:`~pyTooling.GitHub.WorkflowFile.WorkflowResolver.LoadAction` reads an action's file by its path. Every file is
  read once; reading it again returns the same :class:`~pyTooling.GitHub.WorkflowFile.Action`.

The ``ghactions`` domain's :ref:`GHA/Dependencies` lists a composite action with the actions its steps run, and a Docker
action with its image, as read this way.
