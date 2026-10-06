.. _GHA/Summaries:

Summaries
#########

The directives below summarize the current workflow. Like the entries, they read the workflow file, so they can't
drift from it.


.. _GHA/ParameterTable:

Parameter Tables
****************

.. grid:: 2

   .. grid-item::
      :columns: 6

      ``ghactions:parameter-table`` renders the summary tables of the current workflow's parameters - one per kind, the
      parameters in file order, each name linked to its entry:

      * **inputs** - *Parameter Name*, *Required*, *Type* and *Default*;
      * **secrets** - *Token Name*, *Required*, *Type* and *Default*;
      * **outputs** - *Result Name* and the ``description`` of the workflow file.

      A default longer than 120 characters, or of several lines, is shortened in the table and followed by ``…``; the
      entry shows it in full.

   .. grid-item::
      :columns: 6

      .. code-block:: ReST

         Parameter Summary
         *****************

         .. rubric:: Inputs

         .. ghactions:parameter-table::
            :kinds: inputs

         .. rubric:: Secrets

         .. ghactions:parameter-table::
            :kinds: secrets

.. rst:directive:: .. ghactions:parameter-table::

   .. rst:directive:option:: kinds: <kind> ...

      The kinds of parameters to summarize, from ``inputs``, ``secrets`` and ``outputs``, separated by spaces or
      commas. The tables are rendered in the order written. Without the option, a table is rendered for every kind the
      workflow has parameters of, in the order inputs, secrets, outputs. A kind named here, of which the workflow has
      none, is a table saying so.


.. _GHA/Interface:

Interface
*********

.. grid:: 2

   .. grid-item::
      :columns: 6

      ``ghactions:interface`` renders the contract of the current workflow with its caller, as a field list:

      * **Required Inputs**, **Secrets** - a secret the caller has to pass is marked *required* - and **Outputs**,
        each linked to its entry;
      * **Permissions** - the permissions a caller has to grant the ``GITHUB_TOKEN``. A called workflow can keep or
        reduce them, never raise them, so these are the permissions the workflow's jobs and the jobs of the workflows
        they call declare - per scope the highest access, with the job and the line asking for it, linked to GitHub
        when :confval:`ghactions_ref` is configured.

      What the workflow uses is listed by ``ghactions:dependencies``.

   .. grid-item::
      :columns: 6

      .. code-block:: ReST

         .. topic:: Interface

            .. ghactions:interface::

.. rst:directive:: .. ghactions:interface::

   Summarizes the contract of the current workflow with its caller.


.. _GHA/Dependencies:

Dependencies
************

.. grid:: 2

   .. grid-item::
      :columns: 6

      ``ghactions:dependencies`` renders what the current workflow uses, as a nested bullet list. From the workflow
      file, and from the files of the templates and actions it uses, as far as they are in the documented repository:

      * the **templates** the jobs call - each once, with the jobs calling it, when several do - each with its own
        dependencies. A template of the documented repository links to its page, one of another repository to
        GitHub;
      * the **actions** the steps run, each once, linked to GitHub. A composite action is listed with the actions
        its steps run, a Docker action with its image, read from its :file:`action.yml`;
      * the **images** of the containers and service containers the jobs run in.

      What a file can't tell - packages a step installs, tools it calls - is the directive's content: a bullet list
      merged into the derived one. An item whose text is the name of a derived item adds its nested list to that
      item, recursively; any other item is appended to its list. Content after the bullet list follows the list.

   .. grid-item::
      :columns: 6

      .. code-block:: ReST

         .. topic:: Dependencies

            .. ghactions:dependencies::

               * pyTooling/upload-artifact

                 * :gh:`actions/upload-artifact`

               * pip

                 * :term:`wheel`

.. rst:directive:: .. ghactions:dependencies::

   Lists the templates, actions and container images the current workflow uses, merged with the hand-written items of
   its content. A derived item is named by:

   ========================= ==========================================================================================
   Derived item              Names
   ========================= ==========================================================================================
   template                  the reference as written, and without its ref, the file name, the file's stem - as
                             ``UnitTesting.yml``
   action                    the reference as written, and without its ref - as ``actions/checkout``
   container                 ``container``, the image as written
   service container         ``service <name>``, the name, the image as written
   image of a Docker action  ``image``, the image as written
   ========================= ==========================================================================================

   A file of the documented repository that doesn't exist - a template or an :file:`action.yml` - is a warning of type
   ``ghactions.workflow``, and its item has no nested list.


.. _GHA/YAML:

YAML Excerpts
*************

.. grid:: 2

   .. grid-item::
      :columns: 6

      ``ghactions:yaml`` renders the current workflow's file, or a part of it, as a YAML code block. The lines are
      numbered as in the file, and the part is shifted left by the indentation of its first line.

      The caption names the file and the lines. When :confval:`ghactions_repository` and :confval:`ghactions_ref` are
      configured, it links to these lines on GitHub:
      ``https://github.com/<repository>/blob/<ref>/.github/workflows/<file>#L<first>-L<last>``.

   .. grid-item::
      :columns: 6

      .. code-block:: ReST

         .. ghactions:yaml::
            :section: inputs

         .. ghactions:yaml::
            :job: Package

.. rst:directive:: .. ghactions:yaml::

   .. rst:directive:option:: section: inputs | outputs | secrets | jobs

      The ``inputs``, ``outputs`` or ``secrets`` of ``on.workflow_call``, or the ``jobs``.

   .. rst:directive:option:: job: <name>

      One job. Excludes ``:section:``. Without either option, the whole file is shown.

   .. rst:directive:option:: caption: <text>

      A caption replacing the file name and the lines.

   .. rst:directive:option:: name: <label>

      A label to reference the code block by.
