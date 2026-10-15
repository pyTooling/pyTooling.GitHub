# ==================================================================================================================== #
#             _____           _ _               ____ _ _   _   _       _                                               #
#  _ __  _   |_   _|__   ___ | (_)_ __   __ _  / ___(_) |_| | | |_   _| |__                                            #
# | '_ \| | | || |/ _ \ / _ \| | | '_ \ / _` || |  _| | __| |_| | | | | '_ \                                           #
# | |_) | |_| || | (_) | (_) | | | | | | (_| || |_| | | |_|  _  | |_| | |_) |                                          #
# | .__/ \__, ||_|\___/ \___/|_|_|_| |_|\__, (_)____|_|\__|_| |_|\__,_|_.__/                                           #
# |_|    |___/                          |___/                                                                          #
# ==================================================================================================================== #
# Authors:                                                                                                             #
#   Patrick Lehmann                                                                                                    #
#                                                                                                                      #
# License:                                                                                                             #
# ==================================================================================================================== #
# Copyright 2026-2026 Patrick Lehmann - Bötzingen, Germany                                                             #
#                                                                                                                      #
# Licensed under the Apache License, Version 2.0 (the "License");                                                      #
# you may not use this file except in compliance with the License.                                                     #
# You may obtain a copy of the License at                                                                              #
#                                                                                                                      #
#   http://www.apache.org/licenses/LICENSE-2.0                                                                         #
#                                                                                                                      #
# Unless required by applicable law or agreed to in writing, software                                                  #
# distributed under the License is distributed on an "AS IS" BASIS,                                                    #
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.                                             #
# See the License for the specific language governing permissions and                                                  #
# limitations under the License.                                                                                       #
#                                                                                                                      #
# SPDX-License-Identifier: Apache-2.0                                                                                  #
# ==================================================================================================================== #
#
"""
Unit tests for :mod:`pyTooling.GitHub.Release` and :mod:`pyTooling.GitHub.Repository`.
"""
from copy                        import deepcopy
from datetime                    import datetime, timedelta, timezone
from json                        import dumps as json_dumps, loads as json_loads
from pathlib                     import Path
from typing                      import Any

from pyTooling.GenericPath.URL   import URL
from pyTooling.GitHub            import GitHubError
from pyTooling.GitHub.Release    import Release, ReleaseAsset, SourceArchive
from pyTooling.GitHub.Repository import Repository, SnapshotVersion, Tag
from pyTooling.Testing           import Testcase


if __name__ == "__main__":  # pragma: no cover
	print("ERROR: you called a testcase declaration file as an executable module.")
	print("Use: 'python -m unittest <testcase module>'")
	exit(1)


def _repository(name: str) -> dict[str, Any]:
	"""
	Return the ``Repository`` object of a recorded GraphQL response.

	:param name: Name of the fixture file in ``tests/data/Releases``, without extension.
	:returns:    The ``Repository`` object of the fixture's first response.
	"""
	with Path(f"tests/data/Releases/{name}.json").open("r", encoding="utf-8") as file:
		return json_loads(file.read())["graphql"][0]["data"]["repository"]


_URL = URL.Parse("https://github.com/owner/repo/releases/tag/v1.0.0")
_UTC = datetime(2026, 10, 15, 12, 0, 0, tzinfo=timezone.utc)


class Parsing(Testcase):
	def test_GHDL(self) -> None:
		repository = Repository.Parse(_repository("GHDL"))

		self.assertEqual("ghdl/ghdl", str(repository))
		self.assertEqual(("ghdl", "ghdl"), (repository.Owner, repository.Name))
		self.assertEqual("https://github.com/ghdl/ghdl", str(repository.URL))
		self.assertEqual(["nightly", "v6.0.0", "v2.0.0", "v0.37"], [release.TagName for release in repository])
		self.assertEqual(4, len(repository))
		self.assertIsNone(repository.FetchedAt)

		nightly = repository["nightly"]
		self.assertEqual("Nightly Release", nightly.Name)
		self.assertTrue(nightly.IsPrerelease)
		self.assertFalse(nightly.IsLatest)
		self.assertFalse(nightly.IsDraft)
		self.assertTrue(nightly.Description.startswith("This *nightly* release"))
		self.assertEqual(datetime(2026, 9, 14, 0, 3, 11, tzinfo=timezone.utc), nightly.PublishedAt)
		self.assertIs(repository, nightly.Parent)

		latest = repository["v6.0.0"]
		self.assertIs(latest, repository.LatestRelease)
		self.assertIsNone(latest.Name, "An empty title is no title.")
		self.assertEqual("e589c698c351369ac5bcfe7abe1f1152ac5d4727", latest.CommitSHA)
		self.assertEqual(f"https://github.com/ghdl/ghdl/commit/{latest.CommitSHA}", str(latest.CommitURL))
		self.assertEqual("https://github.com/ghdl/ghdl/releases/tag/v6.0.0", str(latest.URL))

		asset = latest.Assets["ghdl-llvm-6.0.0-macos14-aarch64.tar.gz"]
		self.assertEqual(3, len(latest.Assets))
		self.assertIs(latest, asset.Parent)
		self.assertEqual(42493570, asset.Size)
		self.assertEqual("application/x-gtar", asset.ContentType)
		self.assertEqual(
			"https://github.com/ghdl/ghdl/releases/download/v6.0.0/ghdl-llvm-6.0.0-macos14-aarch64.tar.gz",
			str(asset.DownloadURL)
		)
		self.assertIsNone(asset.Label, "GitHub's GraphQL API reports no labels.")
		self.assertEqual(0, len(repository["v2.0.0"].Assets))

	def test_Tags(self) -> None:
		"""A lightweight tag points to its commit, an annotated tag through its tag object."""
		repository = Repository.Parse(_repository("GHDL"))

		self.assertEqual(
			["nightly", "v6.0.0", "v6.0.0-rc.1", "v2.0.0", "v0.37", "v0.34"], list(repository.Tags)
		)
		lightweight = repository.Tags["nightly"]
		self.assertFalse(lightweight.IsAnnotated)
		self.assertEqual(repository["nightly"].CommitSHA, lightweight.CommitSHA)
		self.assertEqual(datetime(2026, 9, 13, 12, 37, 17, tzinfo=timezone.utc), lightweight.CommittedAt)

		annotated = repository.Tags["v6.0.0"]
		self.assertTrue(annotated.IsAnnotated)
		self.assertEqual(repository["v6.0.0"].CommitSHA, annotated.CommitSHA, "The tag object is resolved.")
		self.assertEqual(f"https://github.com/ghdl/ghdl/commit/{annotated.CommitSHA}", str(annotated.CommitURL))
		self.assertIs(repository["v6.0.0"], annotated.Release)
		self.assertTrue(annotated.HasRelease)
		self.assertIs(repository, annotated.Parent)

		self.assertFalse(repository.Tags["v6.0.0-rc.1"].HasRelease)
		self.assertIsNone(repository.Tags["v6.0.0-rc.1"].Release)
		self.assertNotIn("v6.0.0-rc.1", repository, "'in' asks for a release, not for a tag.")
		self.assertIn("v6.0.0", repository)

	def test_OSVVM(self) -> None:
		"""OSVVM tags far more versions than it publishes releases of, and tags names that are no versions."""
		repository = Repository.Parse(_repository("OSVVM"))

		self.assertEqual("2026.09", repository["2026.09"].Name)
		self.assertEqual("2024.07 Release", repository["2024.07"].Name)
		self.assertIsNone(repository["2025.06a"].Name)
		self.assertIs(repository["2026.09"], repository.LatestRelease)
		self.assertEqual(
			["2025.06", "GhdlDebug_22_1114", "2022.05b_", "2020.12+doc"],
			[tag.Name for tag in repository.Tags.values() if not tag.HasRelease]
		)
		self.assertTrue(repository.Tags["2020.12+doc"].IsAnnotated)
		self.assertFalse(repository.Tags["2025.06a"].IsAnnotated)

	def test_SourceArchive(self) -> None:
		repository = Repository.Parse(_repository("OSVVM"))

		self.assertEqual(
			"https://github.com/OSVVM/OsvvmLibraries/archive/refs/tags/2026.09.zip",
			str(repository["2026.09"].SourceArchiveURL(SourceArchive.Zip))
		)
		self.assertEqual(
			"https://github.com/OSVVM/OsvvmLibraries/archive/refs/tags/2026.09.tar.gz",
			str(repository["2026.09"].SourceArchiveURL(SourceArchive.Tarball))
		)

		release = Release("v1.0+doc", _URL, parent=Repository("owner", "repo", URL.Parse("https://github.com/owner/repo")))
		self.assertEqual(
			"https://github.com/owner/repo/archive/refs/tags/v1.0%2Bdoc.zip", str(release.SourceArchiveURL(SourceArchive.Zip))
		)

		with self.assertRaises(GitHubError) as context:
			_ = Release("v1.0.0", _URL).SourceArchiveURL(SourceArchive.Zip)
		self.assertEqual("Release 'v1.0.0' belongs to no repository.", str(context.exception))

		with self.assertRaises(ValueError):
			_ = release.SourceArchiveURL(None)

		with self.assertRaises(TypeError):
			_ = release.SourceArchiveURL("zip")

	def test_MissingField(self) -> None:
		document = _repository("GHDL")
		del document["releases"]["nodes"][1]["tagName"]

		with self.assertRaises(GitHubError) as context:
			_ = Repository.Parse(document)

		self.assertEqual("Field 'repository.releases.nodes[1].tagName' is missing.", str(context.exception))

	def test_IncompletePage(self) -> None:
		"""A connection with a further page is never read as if it were complete."""
		document = _repository("GHDL")
		document["refs"]["pageInfo"]["hasNextPage"] = True

		with self.assertRaises(GitHubError) as context:
			_ = Repository.Parse(document)

		self.assertEqual("Field 'repository.refs' holds only the first page of nodes.", str(context.exception))

	def test_DuplicateTag(self) -> None:
		document = _repository("GHDL")
		document["releases"]["nodes"].append(deepcopy(document["releases"]["nodes"][0]))

		with self.assertRaises(ValueError) as context:
			_ = Repository.Parse(document)

		self.assertEqual("Repository 'ghdl/ghdl' has a release of tag 'nightly' already.", str(context.exception))

	def test_TagTargets(self) -> None:
		"""A tag of a tree has no commit, a tag object is followed, and nesting beyond what was read is an error."""
		commit = {"__typename": "Commit", "oid": "abc", "url": "https://github.com/o/r/commit/abc", "committedDate": None}

		tree = Tag.Parse({"name": "tree", "target": {"__typename": "Tree", "oid": "def"}})
		self.assertIsNone(tree.CommitSHA)
		self.assertFalse(tree.IsAnnotated)

		nested = Tag.Parse(
			{"name": "nested", "target": {"__typename": "Tag", "target": {"__typename": "Tag", "target": commit}}}
		)
		self.assertEqual("abc", nested.CommitSHA)
		self.assertTrue(nested.IsAnnotated)

		with self.assertRaises(GitHubError) as context:
			_ = Tag.Parse({"name": "deep", "target": {"__typename": "Tag", "oid": "123"}})
		self.assertEqual("Field 'ref.target.target' is missing.", str(context.exception))
		self.assertEqual(["Tag 'deep' points to tag objects nested deeper than read."], context.exception.__notes__)

		with self.assertRaises(GitHubError) as context:
			_ = Tag.Parse({"name": "untyped", "target": {"oid": "123"}})
		self.assertEqual("Field 'ref.target.__typename' is missing.", str(context.exception))


class Construction(Testcase):
	def test_Release(self) -> None:
		asset = ReleaseAsset("a.zip", URL.Parse("https://github.com/o/r/releases/download/v1/a.zip"), "application/zip", 7)
		release = Release(
			"v1.0.0", _URL, "Version 1", "Notes", _UTC, isPrerelease=True, commitSHA="abc", assets=[asset]
		)

		self.assertEqual("v1.0.0", str(release))
		self.assertEqual("Version 1", release.Name)
		self.assertEqual(_UTC, release.PublishedAt)
		self.assertTrue(release.IsPrerelease)
		self.assertIs(release, asset.Parent)
		self.assertEqual("a.zip", str(asset))
		self.assertIsNone(release.Parent)

	def test_Release_Parameters(self) -> None:
		for arguments, exception, message in (
			((None, _URL),                         ValueError, "Parameter 'tagName' is None."),
			((1, _URL),                            TypeError,  "Parameter 'tagName' is not of type 'str'."),
			(("", _URL),                           ValueError, "Parameter 'tagName' is empty."),
			(("v1", None),                         ValueError, "Parameter 'url' is None."),
			(("v1", "https://github.com"),         TypeError,  "Parameter 'url' is not of type 'URL'."),
			(("v1", _URL, ""),                     ValueError, "Parameter 'name' is empty."),
			(("v1", _URL, None, None),             ValueError, "Parameter 'description' is None."),
			(("v1", _URL, None, "", "2026-10-15"), TypeError,  "Parameter 'publishedAt' is not of type 'datetime'."),
			(("v1", _URL, None, "", datetime(2026, 10, 15)), ValueError, "Parameter 'publishedAt' has no time zone."),
			(("v1", _URL, None, "", None, None),   ValueError, "Parameter 'isDraft' is None."),
			(("v1", _URL, None, "", None, False, 1), TypeError, "Parameter 'isPrerelease' is not of type 'bool'."),
		):
			with self.subTest(message=message):
				with self.assertRaises(exception) as context:
					_ = Release(*arguments)

				self.assertEqual(message, str(context.exception))

		with self.assertRaises(TypeError):
			_ = Release("v1", _URL, assets=["a.zip"])

		with self.assertRaises(TypeError):
			_ = Release("v1", _URL, parent="owner/repo")

	def test_Release_PublishedAtTimeZone(self) -> None:
		"""A time in another time zone is kept as given."""
		cest = timezone(timedelta(hours=2))
		release = Release("v1", _URL, publishedAt=datetime(2026, 10, 15, 14, 0, 0, tzinfo=cest))

		self.assertEqual(_UTC, release.PublishedAt)
		self.assertEqual(cest, release.PublishedAt.tzinfo)

	def test_Asset_Parameters(self) -> None:
		download = URL.Parse("https://github.com/o/r/releases/download/v1/a.zip")
		for arguments, exception, message in (
			((None, download, "application/zip", 1),   ValueError, "Parameter 'name' is None."),
			(("a.zip", download, "", 1),               ValueError, "Parameter 'contentType' is empty."),
			(("a.zip", None, "application/zip", 1),    ValueError, "Parameter 'downloadURL' is None."),
			(("a.zip", download, "application/zip", True), TypeError, "Parameter 'size' is not of type 'int'."),
			(("a.zip", download, "application/zip", -1), ValueError, "Parameter 'size' is negative."),
			(("a.zip", download, "application/zip", 1, ""), ValueError, "Parameter 'label' is empty."),
		):
			with self.subTest(message=message):
				with self.assertRaises(exception) as context:
					_ = ReleaseAsset(*arguments)

				self.assertEqual(message, str(context.exception))

	def test_Parent(self) -> None:
		"""An element registers in the parent it is given, under its own name, and only once."""
		repository = Repository("owner", "repo", URL.Parse("https://github.com/owner/repo"))
		release = Release("v1", _URL, parent=repository)
		tag = Tag("v1", "abc", parent=repository)
		asset = ReleaseAsset("a.zip", URL.Parse("https://github.com/o/r/a.zip"), "application/zip", 1, parent=release)

		self.assertIs(release, repository["v1"])
		self.assertIs(tag, repository.Tags["v1"])
		self.assertIs(asset, release.Assets["a.zip"])
		self.assertIs(release, tag.Release)

		with self.assertRaises(ValueError) as context:
			_ = Release("v1", _URL, parent=repository)
		self.assertEqual("Repository 'owner/repo' has a release of tag 'v1' already.", str(context.exception))

		with self.assertRaises(ValueError) as context:
			_ = Repository("owner", "other", URL.Parse("https://github.com/owner/other"), [release])
		self.assertEqual("Release 'v1' belongs to repository 'owner/repo' already.", str(context.exception))

		with self.assertRaises(ValueError) as context:
			_ = Tag("v1", parent=repository)
		self.assertEqual("Repository 'owner/repo' has a tag 'v1' already.", str(context.exception))

		with self.assertRaises(ValueError) as context:
			_ = ReleaseAsset("a.zip", URL.Parse("https://github.com/o/r/a.zip"), "application/zip", 1, parent=release)
		self.assertEqual("Release 'v1' has an asset 'a.zip' already.", str(context.exception))

		self.assertFalse(Tag("v2").HasRelease, "A tag of no repository has no release.")

	def test_Repository_Parameters(self) -> None:
		url = URL.Parse("https://github.com/owner/repo")
		for arguments, exception, message in (
			((None, "repo", url),        ValueError, "Parameter 'owner' is None."),
			(("owner", 1, url),          TypeError,  "Parameter 'name' is not of type 'str'."),
			(("owner", "a/b", url),      ValueError, "Parameter 'name' is empty or contains a '/'."),
			(("owner", "repo", None),    ValueError, "Parameter 'url' is None."),
			(("owner", "repo", url, [1]), TypeError, "Element of parameter 'releases' is not of type 'Release'."),
			(("owner", "repo", url, None, ["v1"]), TypeError, "Element of parameter 'tags' is not of type 'Tag'."),
		):
			with self.subTest(message=message):
				with self.assertRaises(exception) as context:
					_ = Repository(*arguments)

				self.assertEqual(message, str(context.exception))

		with self.assertRaises(ValueError) as context:
			_ = Repository("owner", "repo", url, fetchedAt=datetime(2026, 10, 15))
		self.assertEqual("Parameter 'fetchedAt' has no time zone.", str(context.exception))

	def test_Tag_Parameters(self) -> None:
		for arguments, exception, message in (
			((None,),                               ValueError, "Parameter 'name' is None."),
			(("",),                                 ValueError, "Parameter 'name' is empty."),
			(("v1", 1),                             TypeError,  "Parameter 'commitSHA' is not of type 'str'."),
			(("v1", "abc", "https://github.com"),   TypeError,  "Parameter 'commitURL' is not of type 'URL'."),
			(("v1", "abc", None, datetime(2026, 1, 1)), ValueError, "Parameter 'committedAt' has no time zone."),
			(("v1", "abc", None, None, None),       ValueError, "Parameter 'isAnnotated' is None."),
		):
			with self.subTest(message=message):
				with self.assertRaises(exception) as context:
					_ = Tag(*arguments)

				self.assertEqual(message, str(context.exception))


class Snapshot(Testcase):
	def test_RoundTrip(self) -> None:
		"""A snapshot written as JSON text reads back into the same model."""
		for name in ("GHDL", "OSVVM"):
			with self.subTest(fixture=name):
				repository = Repository.Parse(_repository(name), _UTC)
				snapshot =   repository.ToSnapshot()
				restored =   Repository.ParseSnapshot(json_loads(json_dumps(snapshot)))

				self.assertEqual(snapshot, restored.ToSnapshot())
				self.assertEqual(_UTC, restored.FetchedAt)
				self.assertEqual("1", snapshot["version"])
				self.assertEqual(
					[tag.IsAnnotated for tag in repository.Tags.values()],
					[tag.IsAnnotated for tag in restored.Tags.values()]
				)

	def test_GraphQLShape(self) -> None:
		"""The snapshot's repository is GitHub's response, all pages merged and labels added."""
		repository = Repository.Parse(_repository("OSVVM"))
		release =    repository.ToJSON()["releases"]["nodes"][0]

		self.assertNotIn("pageInfo", repository.ToJSON()["releases"])
		self.assertEqual({"oid", "url"}, set(release["tagCommit"]))
		self.assertIsNone(release["releaseAssets"]["nodes"][0]["label"])
		self.assertEqual("2026-10-04T15:42:56+00:00", release["publishedAt"])

	def test_Version(self) -> None:
		snapshot = Repository.Parse(_repository("OSVVM")).ToSnapshot()
		snapshot["version"] = "0"

		with self.assertRaises(GitHubError) as context:
			_ = Repository.ParseSnapshot(snapshot)

		self.assertEqual("Snapshot version '0' is unknown.", str(context.exception))
		self.assertEqual([f"Known: {SnapshotVersion.Version1.value}."], context.exception.__notes__)
		self.assertIs(SnapshotVersion.Version1, SnapshotVersion.Latest)

	def test_MissingField(self) -> None:
		with self.assertRaises(GitHubError) as context:
			_ = Repository.ParseSnapshot({"version": "1"})
		self.assertEqual("Field 'repository' is missing.", str(context.exception))

		with self.assertRaises(TypeError):
			_ = Repository.ParseSnapshot([])
