.. _GHA/Workflow:

Workflows and Parameters
########################

.. _GHA/Workflow/Directive:

Workflows
*********

.. rst:directive:: .. ghactions:workflow:: <name>

   Registers the workflow ``<name>`` - its file's stem, as ``Parameters`` - with an index entry, and makes it the
   **current workflow** of the document: every ``ghactions:input``, ``ghactions:output`` and ``ghactions:secret``
   following it belongs to it, and a role may name its parameters without the workflow's name.

   The directive writes no visible output. Placed above the page's title, its target is the title, as a label is.

   .. rst:directive:option:: file: <path>

      Path to the workflow file, relative to the document. Without it, the file is ``<name>.yml`` in
      :confval:`ghactions_workflow_directory`.

.. code-block:: ReST

   .. ghactions:workflow:: Parameters

   Parameters
   ##########

   The ``Parameters`` job template ...

A document using the workflow is read again, when the workflow file changed.


.. _GHA/Parameters:

Inputs, Outputs and Secrets
***************************

.. grid:: 2

   .. grid-item::
      :columns: 6

      Each of the three directives documents one parameter of the current workflow, as a **section** titled by the
      parameter's name - so it is listed in the page's table of contents - holding a field list:

      #. the fields read from the workflow file: *Type*, *Required* and *Default Value* for an input and a secret,
         where ``— — — —`` says there is no default, and a multi-line default is shown as a block;
      #. the fields of the directive's content, in the order written, as *Possible Values*, *Description* or
         *Example*;
      #. without a hand-written *Description*, the ``description`` of the workflow file, placed behind *Type*,
         *Required*, *Default Value* and *Possible Values*.

      Content after the field list follows it. A workflow file states no type and no default for an **output**, so
      those fields are hand-written there.

   .. grid-item::
      :columns: 6

      .. code-block:: ReST

         Input Parameters
         ****************

         .. ghactions:input:: package_name

            :Possible Values: Any valid Python package name.
            :Example:         ``myPackage``

         Outputs
         *******

         .. ghactions:output:: python_jobs

            :Type:        string (JSON)
            :Description: A JSON array of job descriptions.

.. rst:directive:: .. ghactions:input:: <name>
.. rst:directive:: .. ghactions:output:: <name>
.. rst:directive:: .. ghactions:secret:: <name>

   Documents the input, output or secret ``<name>`` of the current workflow. Its target is ``<Workflow>.<name>``.

.. rst:directive:: .. ghactions:autoinputs::

   Documents every input of the current workflow the document has no ``ghactions:input`` for - also those whose
   ``ghactions:input`` follows later in the document. An entry is what a ``ghactions:input`` without content creates:
   *Type*, *Required*, *Default Value* and the ``description`` of the workflow file.

   .. code-block:: ReST

      Input Parameters
      ****************

      .. ghactions:input:: package_name

         :Possible Values: Any valid Python package name.

      .. ghactions:autoinputs::


.. _GHA/Roles:

Roles
*****

.. rst:role:: ghactions:workflow
.. rst:role:: ghactions:input
.. rst:role:: ghactions:output
.. rst:role:: ghactions:secret

   Refer to a workflow by its name, and to a parameter as ``<Workflow>.<name>`` - after a ``ghactions:workflow``, the
   name alone refers to that workflow's parameter. A leading ``~`` shows only the name:

   .. code-block:: ReST

      :ghactions:input:`package_name`                 in the page of workflow 'Parameters'
      :ghactions:input:`Parameters.package_name`      from anywhere
      :ghactions:input:`~Parameters.package_name`     shown as 'package_name'
      :ghactions:workflow:`CompletePipeline`

   A target that isn't documented is a warning.
