.. _CLI:

Overview
########

pyTooling.GitHub installs a program: :program:`pytooling-github`. It is the command line front-end to what the package
models - reading a GitHub Actions pipeline run into a trace, writing that trace, rendering it - so a pipeline job can
do those things without a script of its own.

.. code-block:: bash

   pytooling-github help              # what the program can do
   pytooling-github help <command>    # what one command can do
   pytooling-github version           # which pyTooling.GitHub is installed

The program is the ``console_scripts`` entry point :pycode:`pyTooling.GitHub.CLI:main`, which :file:`setup.py`
registers, so it is on the path after :pycode:`pip install pyTooling.GitHub`.

.. attention::

   **Drawing needs the** ``diagram`` **extra**: :pycode:`pip install pyTooling.GitHub[diagram]` installs
   *matplotlib*, which :pycode:`--gantt` draws with. Without it, :pycode:`--gantt` names the missing package and the
   command line installing it rather than failing on an import. *colorama*, which a
   :class:`~pyTooling.TerminalUI.TerminalApplication` needs to write anything at all, comes with the package's
   requirement ``pyTooling[terminal]``.


.. _CLI/Structure:

How a command is declared
#########################

The program is a :class:`~pyTooling.TerminalUI.TerminalApplication` **and** an
:class:`~pyTooling.Attributes.ArgParse.ArgParseHelperMixin`, so it prints like the first and parses like the
second: a command is a **method** marked with :class:`~pyTooling.Attributes.ArgParse.CommandHandler`, and the
arguments of that command are the attributes written above the method. See :ref:`ATTR/ArgParse` for the attributes
themselves.

.. code-block:: Python

   @CommandHandler("version", help="Display version information.")
   def HandleVersion(self, _: Namespace) -> None:
     ...

Two commands are always there: :pycode:`help`, which prints the help page of the program or of one command, and
:pycode:`version`. A call with no command prints the help page.

**A group of related commands is a mixin-class of its own.**
:class:`~pyTooling.GitHub.CLI.Application` inherits from all of them, and the attributes are found on the assembled
class, so adding a command means writing a mixin and adding one base-class - see :ref:`ATTR/ArgParse/Mixin`. That is the
same construction :program:`pyedaa-outputfilter` uses.

.. hint::

   The three global switches - ``-q`` / ``--quiet``, ``-v`` / ``--verbose`` and ``-d`` / ``--debug`` - are declared
   on the **default handler**, so they belong before the command: ``pytooling-github --verbose version``, not
   ``pytooling-github version --verbose``.


.. _CLI/Errors:

What a failure looks like
#########################

:func:`~pyTooling.GitHub.CLI.main` runs the program inside a ``try ... except``, so a user of the program sees a message
and a non-zero exit code rather than a traceback. A :exc:`~pyTooling.Exceptions.ToolingException` is printed with
its cause and with every note it carries, because the notes are where pyTooling puts the advice - *"check the
repository's name"* rather than only *"404"*.

A :exc:`~pyTooling.Exceptions.MissingDependencyError` is not handled where it is raised. An output needing an
optional package - ``--gantt`` needs *matplotlib* - imports it where it draws and lets the exception travel to
:func:`~pyTooling.GitHub.CLI.main`, which hands it to
:meth:`~pyTooling.TerminalUI.TerminalApplication.PrintMissingDependencyError`: that printer names the missing
package and every command line installing it, and reports no bug, because nothing is wrong with the program.


.. _CLI/Pipeline:

The ``pipeline`` command
########################

:pycode:`pytooling-github pipeline` reads one run of a CI pipeline into a :class:`~pyTooling.Tracing.Trace` and writes
what was asked of it. Reading and writing are separate steps: the trace is the intermediate every output is
derived from, so a further output is a further option rather than a second reader.

.. code-block:: bash

   pytooling-github pipeline --github-repository=pyTooling/pyTooling \
                             --github-pipeline-id=35479251694 \
                             --trace-file=report/Pipeline.otlp.json \
                             --gantt=report/Pipeline.png

.. list-table::
   :header-rows: 1
   :widths: 34 66

   * - Option
     - Meaning
   * - ``--github-repository=<owner/name>``
     - The repository the run belongs to. Default: :pycode:`$GITHUB_REPOSITORY`, which a workflow sets.
   * - ``--github-pipeline-id=<ID>``
     - The workflow run to read - the number in its URL, :file:`.../actions/runs/35479251694`. Default:
       :pycode:`$GITHUB_RUN_ID`, which a workflow sets.
   * - ``--trace-file=[<format>:]<file>``
     - Write the trace. Default format: ``otlp-json``, currently the only one.
   * - ``--gantt=[<format>:]<file>``
     - Draw the run as a Gantt chart: ``matplotlib-png``, ``matplotlib-svg`` or ``matplotlib-pdf``.
   * - ``--force``
     - Overwrite files that exist. Without it, an existing file is an error.

The token is read from :pycode:`$GITHUB_TOKEN`. Inside a workflow, the built-in token with the
``actions: read`` permission suffices; outside one, it raises the rate limit and is required for a private
repository.

.. hint::

   **A job cannot see itself.** It is still running when it reads the run, so a job that reports the pipeline's
   timing depends on every other job and runs last.


.. _CLI/Pipeline/Formats:

``[<format>:]<file>``
=====================

Every option that writes a file takes the format in front of the path, separated by a colon, and assumes a
default when none is given - :pycode:`--trace-file=report/Pipeline.otlp.json` and
:pycode:`--trace-file=otlp-json:report/Pipeline.otlp.json` are the same thing.

**A colon alone doesn't make a format.** A format is more than one character long and holds no path separator, so
a Windows drive (:file:`C:\\report\\trace.json`) and a colon deeper down a path are paths. A prefix that looks
like a format but isn't one is an error naming the formats that exist, rather than a file with a strange name.

None of that is the command's own: :func:`~pyTooling.Attributes.ArgParse.splitFormat` does the splitting for any
program declaring an option of this shape, and a value naming no format gets the enumeration's ``DEFAULT`` - see
`pyTooling's argument formats <https://pyTooling.github.io/pyTooling/Attributes/ArgParse.html#attr-argparse-formats>`__.

Both are checked **before** the pipeline is read, so a misspelled format or a file that exists is reported at once
instead of after a network round-trip.


.. _CLI/Pipeline/Gantt:

Drawing the run
===============

``--gantt`` lays the trace out as a `Gantt chart <https://pyTooling.github.io/pyTooling/Tracing.html#tracing-render>`__
and draws it: one row per job, the time it waited for a runner in light gray in front of the time it ran, and a line for
the pipeline and every called workflow. The legend carries the statistics per runner image. **The steps are left out** -
a pipeline of 57 jobs has more than a thousand of them, and a chart of one row per step is a different picture.

A format is the backend and the file format - ``matplotlib-png``, ``matplotlib-svg``, ``matplotlib-pdf`` - and the
file's suffix has to agree with it. A value naming no format gets ``matplotlib-png``, so a PNG needs no format, and
any other file states it: :pycode:`--gantt=matplotlib-svg:report/Pipeline.svg`. A suffix that disagrees with the
format is reported rather than a file being written under a name that lies about its content.

matplotlib is an optional dependency. Without it, ``--gantt`` reports which extra installs it
(:pycode:`pyTooling[diagram]`) instead of failing on an import.

.. hint::

   In an SVG, every bar or line is a group named after the timespan it draws - ``span-<SpanID>`` - so a script can
   find the elements of a job.
   `pyTooling's rendering section <https://pyTooling.github.io/pyTooling/Tracing.html#tracing-render>`__ describes
   the identifiers.
