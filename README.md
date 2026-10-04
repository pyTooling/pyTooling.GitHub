[![Sourcecode on GitHub](https://img.shields.io/badge/pyTooling-GitHub-63bf7f?longCache=true&style=flat-square&longCache=true&logo=GitHub)](https://GitHub.com/pyTooling/pyTooling.GitHub)
[![Sourcecode License](https://img.shields.io/pypi/l/pyTooling.GitHub?longCache=true&style=flat-square&logo=Apache&label=code)](LICENSE.md)
[![Documentation](https://img.shields.io/website?longCache=true&style=flat-square&label=pyTooling.github.io%2FpyTooling.GitHub&logo=GitHub&logoColor=fff&up_color=blueviolet&up_message=Read%20now%20%E2%9E%9A&url=https%3A%2F%2FpyTooling.github.io%2FpyTooling.GitHub%2Findex.html)](https://pyTooling.github.io/pyTooling.GitHub/)
[![Documentation License](https://img.shields.io/badge/doc-CC--BY%204.0-green?longCache=true&style=flat-square&logo=CreativeCommons&logoColor=fff)](doc/Doc-License.rst)  
[![PyPI](https://img.shields.io/pypi/v/pyTooling.GitHub?longCache=true&style=flat-square&logo=PyPI&logoColor=FBE072)](https://pypi.org/project/pyTooling.GitHub/)
![PyPI - Status](https://img.shields.io/pypi/status/pyTooling.GitHub?longCache=true&style=flat-square&logo=PyPI&logoColor=FBE072)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/pyTooling.GitHub?longCache=true&style=flat-square&logo=PyPI&logoColor=FBE072)  
[![GitHub Workflow - Build and Test Status](https://img.shields.io/github/actions/workflow/status/pyTooling/pyTooling.GitHub/Pipeline.yml?branch=main&longCache=true&style=flat-square&label=build%20and%20test&logo=GitHub%20Actions&logoColor=FFFFFF)](https://GitHub.com/pyTooling/pyTooling.GitHub/actions/workflows/Pipeline.yml)
[![Libraries.io status for latest release](https://img.shields.io/librariesio/release/pypi/pyTooling.GitHub?longCache=true&style=flat-square&logo=Libraries.io&logoColor=fff)](https://libraries.io/github/pyTooling/pyTooling.GitHub)
[![Codacy - Quality](https://img.shields.io/codacy/grade/e56604e36cf04f6090e0b171e948c1fa?longCache=true&style=flat-square&logo=Codacy)](https://app.codacy.com/gh/pyTooling/pyTooling.GitHub/dashboard)
[![Codacy - Coverage](https://img.shields.io/codacy/coverage/e56604e36cf04f6090e0b171e948c1fa?longCache=true&style=flat-square&logo=Codacy)](https://app.codacy.com/gh/pyTooling/pyTooling.GitHub/dashboard)
[![Codecov - Branch Coverage](https://img.shields.io/codecov/c/github/pyTooling/pyTooling.GitHub?longCache=true&style=flat-square&logo=Codecov)](https://codecov.io/gh/pyTooling/pyTooling.GitHub)

# pyTooling.GitHub

**pyTooling.GitHub** works with GitHub Actions pipelines: it reads workflow and action files into a data model,
reads the runs of a pipeline from GitHub's REST API, and converts them into traces - e.g. OpenTelemetry's OTLP/JSON
or a Gantt chart of the jobs and steps. A Sphinx domain `gha` documents workflows and their inputs, outputs and
secrets taken straight from the workflow files.

It builds on [pyTooling](https://GitHub.com/pyTooling/pyTooling)'s generic CI pipeline model and tracing, and on
[pyTooling.Sphinx](https://GitHub.com/pyTooling/pyTooling.Sphinx) for its documentation extensions.


> [!IMPORTANT]
> The Sphinx domain `gha` in `pyTooling.GitHub.Sphinx` requires [pyTooling.Sphinx][pyTooling.Sphinx], and thus
> **Python 3.12 or newer**, because Sphinx 9.1 requires Python 3.12.

The package is installed from PyPI, with the extras `diagram` (matplotlib, for Gantt charts) and `sphinx`
(pyTooling.Sphinx, for the domain `gha`):

```bash
pip install pyTooling.GitHub[diagram,sphinx]
```


## Features

### Data models

* [Pipeline runs][PipelineRun] - A GitHub Actions workflow run - pipeline, workflows, matrices, jobs and steps with
  their times and outcomes - read from the GitHub REST API's payloads.
* [Workflow files][WorkflowFile] - A workflow file: triggers, inputs, outputs, secrets, permissions and jobs with their
  dependencies, read with line numbers, and converted into a pipeline graph.

### Traces

* [GitHub Actions trace reader][Tracing] - Reads a workflow run through the GitHub REST API into a trace, written as
  OpenTelemetry's OTLP/JSON.

### Sphinx domain `gha`

The domain is enabled in `conf.py`; it sets up pyTooling.Sphinx itself:

```python
# doc/conf.py
extensions = [
  ...,
  "pyTooling.GitHub.Sphinx",
]
```

* [Workflows and their parameters][GHA] - `gha:workflow`, `gha:input`, `gha:output`, `gha:secret` and
  `gha:autoinputs`, taken straight from the workflow file; roles to reference them.
* [Tables and listings][GHA] - `gha:parameter-table`, `gha:interface`, `gha:dependencies` and `gha:yaml`.
* [Pipeline graph][GHA] - `gha:pipeline-graph` draws the jobs of a workflow and their `needs` as a Graphviz graph,
  with the reusable workflows it calls expanded.

### Program

* [pytooling-github][CLI] - The command `pipeline` reads a pipeline run into a trace, writes it, and draws it as a
  Gantt chart.

[PipelineRun]: https://pyTooling.github.io/pyTooling.GitHub/PipelineRun.html
[WorkflowFile]: https://pyTooling.github.io/pyTooling.GitHub/WorkflowFile.html
[Tracing]: https://pyTooling.github.io/pyTooling.GitHub/Tracing.html
[GHA]: https://pyTooling.github.io/pyTooling.GitHub/GHA/index.html
[CLI]: https://pyTooling.github.io/pyTooling.GitHub/CLI.html
[pyTooling.Sphinx]: https://pyTooling.github.io/pyTooling.Sphinx/


## Contributors

* [Patrick Lehmann](https://GitHub.com/Paebbels) (Maintainer)
* [and more...](https://GitHub.com/pyTooling/pyTooling.GitHub/graphs/contributors)


## License

This Python package (source code) is licensed under [Apache License 2.0](LICENSE.md).  
The accompanying documentation is licensed under [Creative Commons - Attribution 4.0 (CC-BY 4.0)](doc/Doc-License.rst).


-------------------------

SPDX-License-Identifier: Apache-2.0
