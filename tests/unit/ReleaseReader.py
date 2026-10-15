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
Unit tests for :mod:`pyTooling.GitHub.ReleaseReader`.
"""
from copy                           import deepcopy
from json                           import dumps as json_dumps, loads as json_loads
from pathlib                        import Path
from typing                         import Any, Callable
from unittest                       import mock
from urllib.error                   import HTTPError

from pyTooling.GitHub               import GitHubError
from pyTooling.GitHub.ReleaseReader import RELEASE_ASSETS_QUERY, RELEASES_QUERY, ReleaseReader
from pyTooling.Testing              import Testcase


if __name__ == "__main__":  # pragma: no cover
	print("ERROR: you called a testcase declaration file as an executable module.")
	print("Use: 'python -m unittest <testcase module>'")
	exit(1)


_GRAPHQL = "https://api.github.com/graphql"
_REST =    "https://api.github.com/"


def _fixture(name: str) -> dict[str, Any]:
	"""
	Return a fixture of recorded responses.

	:param name: Name of the fixture file in ``tests/data/Releases``, without extension.
	:returns:    The fixture: a list of GraphQL responses in request order, and a dictionary of REST resources.
	"""
	with Path(f"tests/data/Releases/{name}.json").open("r", encoding="utf-8") as file:
		return json_loads(file.read())


class _Response:
	"""A fake HTTP response for :func:`urllib.request.urlopen`."""

	def __init__(self, document: Any) -> None:
		"""
		Initializes a fake response.

		:param document: The JSON document to respond with.
		"""
		self._body = json_dumps(document).encode()
		self.headers = {"Content-Type": "application/json; charset=utf-8"}

	def read(self) -> bytes:
		"""
		Return the response's body.

		:returns: The encoded JSON document.
		"""
		return self._body

	def close(self) -> None:
		"""
		Close the response, as :class:`~urllib.error.HTTPError` does with the response it wraps.
		"""

	def __enter__(self) -> "_Response":
		"""
		Enter the response's context.

		:returns: The response.
		"""
		return self

	def __exit__(self, *_: Any) -> None:
		"""
		Leave the response's context.

		:param _: Exception information.
		"""


class Server:
	"""A fake GitHub API answering GraphQL requests in order and REST requests by path."""

	def __init__(self, graphql: list[Any], rest: dict[str, Any]) -> None:
		"""
		Initializes a fake GitHub API.

		:param graphql: The GraphQL responses, in request order.
		:param rest:    The REST resources, by path.
		"""
		self.graphql =   list(graphql)
		self.rest =      rest
		self.requests =  []
		self.variables = []

	def __call__(self, request: Any, timeout: float) -> _Response:
		"""
		Respond to a request.

		:param request: The request.
		:param timeout: The request's timeout.
		:returns:       The response.
		"""
		self.requests.append(request)
		if request.full_url == _GRAPHQL:
			self.variables.append(json_loads(request.data)["variables"])
			return _Response(self.graphql.pop(0))

		return _Response(self.rest[request.full_url[len(_REST):]])

	def Patch(self) -> Any:
		"""
		Patch :func:`urlopen` to be answered by this API.

		:returns: The patcher.
		"""
		return mock.patch("pyTooling.REST.urlopen", side_effect=self)


class Reading(Testcase):
	def _Read(self, server: Server, repository: str) -> Any:
		"""
		Read a repository from a fake GitHub API.

		:param server:     The fake API.
		:param repository: The repository as ``owner/name``.
		:returns:          The repository's releases and tags.
		"""
		with server.Patch():
			return ReleaseReader(repository, "secret").Read()

	def test_GHDL(self) -> None:
		"""One query reads the releases and tags; a release with assets costs one REST request for its labels."""
		fixture =    _fixture("GHDL")
		server =     Server(fixture["graphql"], fixture["rest"])
		repository = self._Read(server, "ghdl/ghdl")

		self.assertEqual(4, len(repository))
		self.assertEqual(6, len(repository.Tags))
		self.assertIsNotNone(repository.FetchedAt)
		self.assertEqual(4, len(server.requests), "One GraphQL request, three REST requests for labels.")
		self.assertEqual(
			["POST", "GET", "GET", "GET"], [request.get_method() for request in server.requests]
		)
		self.assertEqual("Bearer secret", server.requests[0].get_header("Authorization"))
		self.assertEqual(RELEASES_QUERY, json_loads(server.requests[0].data)["query"])
		self.assertEqual(
			{
				"owner": "ghdl", "name": "ghdl", "withReleases": True, "releasesCursor": None, "withTags": True,
				"tagsCursor": None
			},
			server.variables[0]
		)

		asset = repository["v6.0.0"].Assets["ghdl-llvm-6.0.0-macos14-aarch64.tar.gz"]
		self.assertEqual("GHDL - v6.0.0 - macOS 14 (aarch64) - llvm backend", asset.Label)
		self.assertTrue(all(asset.Label is None for asset in repository["v0.37"].Assets.values()), "'' is no label.")

	def test_OSVVM(self) -> None:
		fixture =    _fixture("OSVVM")
		repository = self._Read(Server(fixture["graphql"], fixture["rest"]), "OSVVM/OsvvmLibraries")

		self.assertEqual(
			"OsvvmLibraries - 2026.09 - all-in-one (ZIP)", repository["2026.09"].Assets["OsvvmLibraries-2026.09.zip"].Label
		)
		self.assertEqual(
			"sha256:236214bf06b8f755a19203b49f1f4df4660c36460a4d771449379c5a3a7459a1",
			repository["2026.09"].Assets["OsvvmLibraries-2026.09.zip"].Digest
		)
		self.assertEqual(4, sum(1 for tag in repository.Tags.values() if not tag.HasRelease))

	def test_Pagination(self) -> None:
		"""Both connections are read page by page, and a tag of the first page finds its release on the second."""
		fixture =    _fixture("pyTooling")
		server =     Server(fixture["graphql"], fixture["rest"])
		repository = self._Read(server, "pyTooling/pyTooling")

		firstPage = fixture["graphql"][0]["data"]["repository"]
		self.assertEqual(2, len(server.requests))
		self.assertEqual(firstPage["releases"]["pageInfo"]["endCursor"], server.variables[1]["releasesCursor"])
		self.assertEqual(firstPage["refs"]["pageInfo"]["endCursor"], server.variables[1]["tagsCursor"])
		self.assertEqual(["v10.0.0-rc2", "v9.0.0", "v8.19.0", "v8.18.0"], [release.TagName for release in repository])
		self.assertEqual(6, len(repository.Tags))
		self.assertTrue(repository.Tags["v8.19.0"].HasRelease)
		self.assertTrue(repository["v10.0.0-rc2"].IsPrerelease)
		self.assertIs(repository["v9.0.0"], repository.LatestRelease)

	def test_Pagination_OneConnection(self) -> None:
		"""A connection whose last page was read is left out of the next request."""
		fixture = _fixture("pyTooling")
		pages =   deepcopy(fixture["graphql"])
		pages[0]["data"]["repository"]["releases"]["pageInfo"]["hasNextPage"] = False
		pages[0]["data"]["repository"]["releases"]["nodes"].extend(pages[1]["data"]["repository"]["releases"]["nodes"])
		del pages[1]["data"]["repository"]["releases"]

		server =     Server(pages, fixture["rest"])
		repository = self._Read(server, "pyTooling/pyTooling")

		self.assertFalse(server.variables[1]["withReleases"])
		self.assertTrue(server.variables[1]["withTags"])
		self.assertEqual((4, 6), (len(repository), len(repository.Tags)))

	def test_AssetPages(self) -> None:
		"""A release with more assets than a page holds is completed by a query of its own."""
		fixture = _fixture("GHDL")
		pages =   deepcopy(fixture["graphql"])
		release = pages[0]["data"]["repository"]["releases"]["nodes"][0]
		further = release["releaseAssets"]["nodes"][2:]
		release["releaseAssets"]["nodes"] = release["releaseAssets"]["nodes"][:2]
		release["releaseAssets"]["pageInfo"] = {"hasNextPage": True, "endCursor": "Mg"}
		pages.append({"data": {"node": {"releaseAssets": {
			"pageInfo": {"hasNextPage": False, "endCursor": "Mw"}, "nodes": further
		}}}})

		server =     Server(pages, fixture["rest"])
		repository = self._Read(server, "ghdl/ghdl")

		self.assertEqual(3, len(repository["nightly"].Assets))
		self.assertEqual({"id": release["id"], "cursor": "Mg"}, server.variables[1])
		self.assertEqual(RELEASE_ASSETS_QUERY, json_loads(server.requests[1].data)["query"])

	def test_Drafts(self) -> None:
		"""A draft is skipped before its labels are requested."""
		fixture = _fixture("OSVVM")
		pages =   deepcopy(fixture["graphql"])
		pages[0]["data"]["repository"]["releases"]["nodes"][0]["isDraft"] = True

		server =     Server(pages, fixture["rest"])
		repository = self._Read(server, "OSVVM/OsvvmLibraries")

		self.assertNotIn("2026.09", repository)
		self.assertFalse(repository.Tags["2026.09"].HasRelease)
		self.assertNotIn(
			"https://api.github.com/repos/OSVVM/OsvvmLibraries/releases/403085803",
			[request.full_url for request in server.requests]
		)

	def test_LabelsMissing(self) -> None:
		"""An asset the REST API doesn't report is an error, not an asset without label."""
		fixture = _fixture("OSVVM")
		rest =    deepcopy(fixture["rest"])
		rest["repos/OSVVM/OsvvmLibraries/releases/403085803"]["assets"].pop()

		with self.assertRaises(GitHubError) as context:
			_ = self._Read(Server(fixture["graphql"], rest), "OSVVM/OsvvmLibraries")

		self.assertTrue(str(context.exception).startswith("REST response for release '2026.09' lacks asset '"))


class Errors(Testcase):
	def _Fail(self, urlopen: Callable[..., Any], repository: str = "pyTooling/DoesNotExist") -> GitHubError:
		"""
		Read a repository from a fake GitHub API expected to fail.

		:param urlopen:    The fake :func:`urlopen`.
		:param repository: The repository as ``owner/name``.
		:returns:          The exception raised.
		"""
		with mock.patch("pyTooling.REST.urlopen", side_effect=urlopen):
			with mock.patch("pyTooling.REST.sleep"):
				with self.assertRaises(GitHubError) as context:
					_ = ReleaseReader(repository, "secret").Read()

		self.assertNotIn("secret", str(context.exception) + "".join(getattr(context.exception, "__notes__", [])))
		return context.exception

	def test_NotFound(self) -> None:
		ex = self._Fail(Server([_fixture("Errors")["NotFound"]], {}))

		self.assertEqual("GraphQL request for repository 'pyTooling/DoesNotExist' failed.", str(ex))
		self.assertEqual([
			"NOT_FOUND: Could not resolve to a Repository with the name 'pyTooling/DoesNotExist'.",
			"Check the repository's name, and that the token may read the repository."
		], ex.__notes__)

	def test_RateLimited(self) -> None:
		ex = self._Fail(Server([{"errors": [{"type": "RATE_LIMITED", "message": "API rate limit exceeded."}]}], {}))

		self.assertEqual([
			"RATE_LIMITED: API rate limit exceeded.",
			"GraphQL rate limit exceeded. Wait for its reset, or use a token with a higher limit."
		], ex.__notes__)

	def test_QueryError(self) -> None:
		"""An error without a type reports its code."""
		ex = self._Fail(Server([_fixture("Errors")["UndefinedField"]], {}))

		self.assertEqual(["undefinedField: Field 'label' doesn't exist on type 'ReleaseAsset'"], ex.__notes__)

	def test_NoData(self) -> None:
		self.assertEqual("GraphQL response has no data.", str(self._Fail(Server([{}], {}))))
		self.assertEqual(
			"GraphQL response has no repository 'pyTooling/DoesNotExist'.",
			str(self._Fail(Server([{"data": {"repository": None}}], {})))
		)
		self.assertEqual(
			"GraphQL response has no page of field 'refs'.",
			str(self._Fail(Server([{"data": {"repository": {"releases": {"nodes": [], "pageInfo": {}}}}}], {})))
		)

	def test_BadCredentials(self) -> None:
		def urlopen(request: Any, timeout: float) -> None:
			"""
			Nested function failing a request with HTTP 401.

			:param request: The request.
			:param timeout: The request's timeout.
			"""
			raise HTTPError(request.full_url, 401, "Unauthorized", {}, _Response(_fixture("Errors")["BadCredentials"]))

		ex = self._Fail(urlopen)

		self.assertEqual(
			f"GraphQL request for repository 'pyTooling/DoesNotExist' failed: Request failed with HTTP 401: {_GRAPHQL}",
			str(ex)
		)
		self.assertEqual(["Answer: Bad credentials", "Token is invalid or expired."], ex.__notes__)

	def test_Retry(self) -> None:
		"""A query changes nothing, so a transient failure is tried again."""
		fixture = _fixture("pyTooling")
		server =  Server(fixture["graphql"], fixture["rest"])
		failed =  False

		def urlopen(request: Any, timeout: float) -> _Response:
			"""
			Nested function failing the first request transiently, then responding from the fake API.

			:param request: The request.
			:param timeout: The request's timeout.
			:returns:       The response.
			"""
			nonlocal failed
			if not failed:
				failed = True
				raise HTTPError(request.full_url, 502, "Bad Gateway", {}, _Response({"message": "Bad Gateway"}))

			return server(request, timeout)

		with mock.patch("pyTooling.REST.urlopen", side_effect=urlopen):
			with mock.patch("pyTooling.REST.sleep") as sleep:
				repository = ReleaseReader("pyTooling/pyTooling", "secret").Read()

		self.assertEqual(4, len(repository))
		sleep.assert_called_once_with(2.0)

	def test_Unreachable(self) -> None:
		def urlopen(request: Any, timeout: float) -> None:
			"""
			Nested function failing every request, as an unreachable API does.

			:param request: The request.
			:param timeout: The request's timeout.
			"""
			raise OSError("Network is unreachable")

		ex = self._Fail(urlopen)

		self.assertEqual(
			f"GraphQL request for repository 'pyTooling/DoesNotExist' failed: API couldn't be reached: {_GRAPHQL}", str(ex)
		)
		self.assertEqual(["Reason: Network is unreachable", "Tried 4 times."], ex.__notes__)

	def test_Token(self) -> None:
		"""GitHub's GraphQL API serves no anonymous requests."""
		with self.assertRaises(ValueError) as context:
			_ = ReleaseReader("owner/repo", None)
		self.assertEqual("Parameter 'token' is None.", str(context.exception))

		with self.assertRaises(ValueError) as context:
			_ = ReleaseReader("owner/repo", "")
		self.assertEqual("Parameter 'token' is empty.", str(context.exception))

		with self.assertRaises(TypeError):
			_ = ReleaseReader("owner/repo", 4711)

		with self.assertRaises(ValueError):
			_ = ReleaseReader("owner", "secret")
