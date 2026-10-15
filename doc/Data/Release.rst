.. _DATA/Release:

Releases and Tags
#################

:mod:`pyTooling.GitHub.Repository` models the **releases and tags of a GitHub repository**, and
:class:`~pyTooling.GitHub.ReleaseReader.ReleaseReader` reads them through GitHub's GraphQL API:

.. code-block:: python

   from os import getenv
   from pyTooling.GitHub.Release       import SourceArchive
   from pyTooling.GitHub.ReleaseReader import ReleaseReader

   repository = ReleaseReader("ghdl/ghdl", token=getenv("GITHUB_TOKEN")).Read()

   release = repository["v5.0.1"]                # the release published at tag 'v5.0.1'
   print(f"{release.Name or release.TagName}: {release.PublishedAt:%d.%m.%Y %H:%M:%S} {release.CommitSHA[:7]}")
   for asset in release.Assets.values():
     print(f"  {asset.Label or asset.Name}: {asset.Size} bytes, {asset.DownloadURL}")
   print(release.SourceArchiveURL(SourceArchive.Tarball))

   for tag in repository.Tags.values():         # every tag, with or without a release
     if not tag.HasRelease:
       print(f"{tag.Name} at {tag.CommitSHA[:7]}, committed {tag.CommittedAt}")


.. _DATA/Release/Tree:

The Tree
********

.. tree::

   - :class:`~pyTooling.GitHub.Repository.Repository`     | the releases and tags of a repository
     - :class:`~pyTooling.GitHub.Release.Release`         | a release, published at a tag
       - :class:`~pyTooling.GitHub.Release.ReleaseAsset`  | a file attached to the release
     - :class:`~pyTooling.GitHub.Repository.Tag`          | a tag and the commit it points to

Every element knows its ``Parent``. A repository is a collection of its **releases**: ``"v5.0.1" in repository`` asks
whether a release is published at that tag, ``repository["v5.0.1"]`` returns it, and iterating yields the releases
the newest first. Its :attr:`~pyTooling.GitHub.Repository.Repository.Tags` hold every tag, and
:attr:`Tag.HasRelease <pyTooling.GitHub.Repository.Tag.HasRelease>` tells the tags without a release - OSVVM, for
example, tags far more versions than it publishes releases of.

* **A release's commit is the commit its tag points to.** GitHub's ``target_commitish`` is usually a branch's name,
  e.g. ``main``, and no commit. An annotated tag is resolved through its tag object.
* **A release's time is when it was published**
  (:attr:`~pyTooling.GitHub.Release.Release.PublishedAt`). The time GitHub calls *created* is the commit's.
* Every time keeps its time zone - GitHub reports UTC -, so a consumer converts it to the time zone it shows; a
  constructor rejects a time without one.
* A release without a title has :attr:`~pyTooling.GitHub.Release.Release.Name` ``None``; GitHub's release page shows
  the tag's name instead. The release notes are GitHub Flavored Markdown.
* :attr:`~pyTooling.GitHub.Release.Release.IsLatest` is GitHub's *latest release*, which a maintainer may also set by
  hand; :attr:`~pyTooling.GitHub.Repository.Repository.LatestRelease` returns it.
* An asset's :attr:`~pyTooling.GitHub.Release.ReleaseAsset.Label` is the text GitHub's release page shows instead of
  the file name, if the uploader set one.
* GitHub's *Source code* archives are no assets: GitHub creates them on request.
  :meth:`~pyTooling.GitHub.Release.Release.SourceArchiveURL` returns the URL the release page links.

.. note::

   Download counts are not part of the model: they change with every download, so a stored snapshot would never be
   the same twice.


.. _DATA/Release/Reading:

Reading a Repository
********************

GitHub's GraphQL API serves no anonymous requests, so :class:`~pyTooling.GitHub.ReleaseReader.ReleaseReader` needs a
token - inside a workflow, ``GITHUB_TOKEN`` with the ``contents: read`` permission suffices. A token with write
access to the repository also sees its draft releases.

* One query (:data:`~pyTooling.GitHub.ReleaseReader.RELEASES_QUERY`) reads a page of 50 releases with their assets and
  a page of 100 tags with their commits. Both are read page by page, until each is complete.
* GitHub's GraphQL API reports no asset labels. Each release with assets costs one request to the REST API, which
  does.
* A request is tried again after a transient failure. A failed request, and an error GitHub's GraphQL API responds
  with, raise a :exc:`~pyTooling.GitHub.GitHubError`, whose notes report the cause - e.g. an unknown repository, an
  exhausted rate limit or an invalid token.


.. _DATA/Release/Snapshot:

Snapshots
*********

:meth:`~pyTooling.GitHub.Repository.Repository.ToSnapshot` writes the model as a JSON object, which
:meth:`~pyTooling.GitHub.Repository.Repository.ParseSnapshot` reads back - so a consumer stores a repository's
releases and reads them again without another request. The snapshot holds a format version
(:class:`~pyTooling.GitHub.Repository.SnapshotVersion`), the time the data was read
(:attr:`~pyTooling.GitHub.Repository.Repository.FetchedAt`), and the repository in the shape of GitHub's GraphQL API -
all pages merged and each asset's label added:

.. code-block:: json

   {
     "version": "1",
     "fetchedAt": "2026-10-15T21:05:44+00:00",
     "repository": {
       "nameWithOwner": "ghdl/ghdl",
       "url": "https://github.com/ghdl/ghdl",
       "releases": {"nodes": [
         {
           "tagName": "v6.0.0", "name": null, "description": "# GHDL 6.0.0 ...",
           "publishedAt": "2026-03-07T18:38:42+00:00", "url": "https://github.com/ghdl/ghdl/releases/tag/v6.0.0",
           "isDraft": false, "isPrerelease": false, "isLatest": true,
           "tagCommit": {"oid": "e589c698...", "url": "https://github.com/ghdl/ghdl/commit/e589c698..."},
           "releaseAssets": {"nodes": [
             {
               "name": "ghdl-llvm-6.0.0-macos14-aarch64.tar.gz",
               "label": "GHDL - v6.0.0 - macOS 14 (aarch64) - llvm backend",
               "contentType": "application/x-gtar", "size": 42493570,
               "downloadUrl": "https://github.com/ghdl/ghdl/releases/download/v6.0.0/ghdl-llvm-6.0.0-..."
             }
           ]}
         }
       ]},
       "refs": {"nodes": [
         {"name": "v6.0.0", "target": {"__typename": "Tag", "target": {
           "__typename": "Commit", "oid": "e589c698...", "url": "https://github.com/ghdl/ghdl/commit/e589c698...",
           "committedDate": "2026-03-07T17:47:40+00:00"
         }}}
       ]}
     }
   }

:meth:`Repository.Parse <pyTooling.GitHub.Repository.Repository.Parse>` reads both, GitHub's response and the
snapshot's ``repository``. A connection still announcing a further page is rejected instead of read as complete.
