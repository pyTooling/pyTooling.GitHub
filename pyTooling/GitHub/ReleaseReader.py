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
Read the releases and tags of a GitHub repository through GitHub's GraphQL API.

.. code-block:: python

   from os import getenv
   from pyTooling.GitHub.ReleaseReader import ReleaseReader

   repository = ReleaseReader("ghdl", "ghdl", token=getenv("GITHUB_TOKEN")).Read()
   release = repository["v5.0.1"]
   print(f"{release.TagName} published {release.PublishedAt:%d.%m.%Y %H:%M:%S} at commit {release.CommitSHA[:7]}")

.. hint::

   See :ref:`high-level help <DATA/Release>` for explanations and usage examples.
"""
from datetime                 import datetime, timezone
from http                     import HTTPMethod
from textwrap                 import dedent
from typing                   import Any, Optional as Nullable, Union

from pyTooling.Decorators     import export
from pyTooling.URI            import URL
from pyTooling.REST           import JSONObject, RESTError

from pyTooling.GitHub         import GITHUB_API_URL, GitHubError, RepositoryClient
from pyTooling.GitHub.Release import Repository


__all__ = ["RELEASES_QUERY", "RELEASE_ASSETS_QUERY"]

RELEASES_QUERY = dedent("""\
	query Releases(
	  $owner: String!, $name: String!,
	  $withReleases: Boolean!, $releasesCursor: String,
	  $withTags: Boolean!, $tagsCursor: String
	) {
	  repository(owner: $owner, name: $name) {
	    nameWithOwner
	    url
	    releases(
	      first: 50, after: $releasesCursor, orderBy: {field: CREATED_AT, direction: DESC}
	    ) @include(if: $withReleases) {
	      pageInfo { hasNextPage endCursor }
	      nodes {
	        id
	        databaseId
	        tagName
	        name
	        description
	        publishedAt
	        url
	        isDraft
	        isPrerelease
	        isLatest
	        tagCommit { oid url }
	        releaseAssets(first: 100) {
	          pageInfo { hasNextPage endCursor }
	          nodes { ...Asset }
	        }
	      }
	    }
	    refs(
	      refPrefix: "refs/tags/", first: 100, after: $tagsCursor, orderBy: {field: TAG_COMMIT_DATE, direction: DESC}
	    ) @include(if: $withTags) {
	      pageInfo { hasNextPage endCursor }
	      nodes {
	        name
	        target {
	          ...Target
	          ... on Tag {
	            target {
	              ...Target
	              ... on Tag { target { ...Target ... on Tag { target { __typename oid } } } }
	            }
	          }
	        }
	      }
	    }
	  }
	}

	fragment Asset on ReleaseAsset { name contentType size downloadUrl digest }

	fragment Target on GitObject { __typename oid ... on Commit { url committedDate } }
""")
"""
GraphQL query reading a page of releases and a page of tags of a repository.

The variables ``withReleases`` and ``withTags`` leave out a connection whose last page was read already. An annotated
tag is followed through up to three tag objects to its commit.
"""

RELEASE_ASSETS_QUERY = dedent("""\
	query ReleaseAssets($id: ID!, $cursor: String) {
	  node(id: $id) {
	    ... on Release {
	      releaseAssets(first: 100, after: $cursor) {
	        pageInfo { hasNextPage endCursor }
	        nodes { name contentType size downloadUrl digest }
	      }
	    }
	  }
	}
""")
"""GraphQL query reading a further page of a release's assets."""


@export
class ReleaseReader(RepositoryClient):
	"""
	Reads the releases and tags of a GitHub repository through GitHub's GraphQL API.

	One query reads a page of releases with their assets and a page of tags with their commits, so a repository with
	fewer than 50 releases and 100 tags is read by one request. GitHub's GraphQL API reports no asset labels, so each
	release with assets costs one request to the REST API for its labels. Draft releases are skipped.

	GitHub's GraphQL API serves no anonymous requests, so a token is required - inside a workflow, ``GITHUB_TOKEN``
	with the ``contents: read`` permission suffices. The GraphQL endpoint is ``graphql`` below :attr:`APIURL`, as on
	github.com.
	"""

	def __init__(
		self,
		owner:      str,
		repository: str,
		token:      str,
		*,
		apiURL:     Union[str, URL] = GITHUB_API_URL,
		timeout:    float = 30.0,
		retries:    int = 3,
		retryDelay: float = 2.0
	) -> None:
		"""
		Initializes a reader for the releases and tags of a repository.

		:param owner:       The owner of the repository, a user or an organization.
		:param repository:  The name of the repository.
		:param token:       Token authorizing the requests.
		:param apiURL:      Optional, base URL of the GitHub API. Default: :data:`~pyTooling.GitHub.GITHUB_API_URL`.
		:param timeout:     Optional, timeout of a single request in seconds. Default: ``30.0``.
		:param retries:     Optional, how often a transiently failing request is tried again. ``0`` tries once.
		                    Default: ``3``.
		:param retryDelay:  Optional, pause in seconds before a request is tried again the first time. The pause doubles
		                    with every further attempt. Default: ``2.0``.
		:raises ValueError: If parameter 'token' is ``None``.
		:raises ValueError: If parameter 'token' is empty.
		:raises TypeError:  If a parameter of :class:`~pyTooling.GitHub.RepositoryClient` has the wrong type.
		:raises ValueError: If a parameter of :class:`~pyTooling.GitHub.RepositoryClient` has an invalid value.
		"""
		super().__init__(
			owner, repository, token, apiURL=apiURL, timeout=timeout, retries=retries, retryDelay=retryDelay
		)

		if token is None:
			raise ValueError("Parameter 'token' is None.")
		elif token == "":
			raise ValueError("Parameter 'token' is empty.")

	def Read(self) -> Repository:
		"""
		Read the releases and tags of the repository.

		Every page of releases, tags and assets is read, draft releases are skipped, the asset labels are added from the
		REST API, and the result is parsed by :meth:`Repository.Parse <pyTooling.GitHub.Release.Repository.Parse>`.
		A request fails e.g. on an exhausted rate limit or an unreachable API, and GitHub's GraphQL API reports e.g. an
		unknown repository as an error.

		:returns:            The repository, with its releases and tags attached, and the time reading began.
		:raises GitHubError: If a request fails. |br|
		                     The notes report the cause.
		:raises GitHubError: If GitHub's GraphQL API responds with errors. |br|
		                     The notes report each error.
		:raises GitHubError: If a response lacks a field or a page.
		:raises GitHubError: If the REST API reports the assets of a release differently. |br|
		                     The note says to read the repository again, as assets may have changed while reading.
		"""
		fetchedAt = datetime.now(timezone.utc)
		variables: dict[str, Any] = {
			"owner":          self._owner,
			"name":           self._repository,
			"withReleases":   True,
			"releasesCursor": None,
			"withTags":       True,
			"tagsCursor":     None
		}
		releases:   list[JSONObject] = []
		refs:       list[JSONObject] = []
		repository: JSONObject
		while variables["withReleases"] or variables["withTags"]:
			if not isinstance(repository := self._Query(RELEASES_QUERY, variables).get("repository", None), dict):
				raise GitHubError(f"GraphQL response has no repository '{self._owner}/{self._repository}'.")

			for field, nodes, flag, cursor in (
				("releases", releases, "withReleases", "releasesCursor"),
				("refs",     refs,     "withTags",     "tagsCursor")
			):
				if not variables[flag]:
					continue
				elif not isinstance(connection := repository.get(field, None), dict) \
					or not isinstance(connection.get("nodes", None), list) \
					or not isinstance(pageInfo := connection.get("pageInfo", None), dict):
					raise GitHubError(f"GraphQL response has no page of field '{field}'.")
				elif pageInfo.get("hasNextPage", False) and pageInfo.get("endCursor", None) is None:
					raise GitHubError(f"GraphQL response announces a further page of field '{field}' without a cursor.")

				nodes.extend(connection["nodes"])
				variables[flag] =   pageInfo.get("hasNextPage", False) is True
				variables[cursor] = pageInfo.get("endCursor", None)

		releases = [release for release in releases if release.get("isDraft", None) is not True]
		for release in releases:
			tagName = release.get("tagName", None)
			if not isinstance(connection := release.get("releaseAssets", None), dict) \
				or not isinstance(assets := connection.get("nodes", None), list) \
				or not isinstance(pageInfo := connection.get("pageInfo", None), dict):
				raise GitHubError(f"GraphQL response has no assets of release '{tagName}'.")

			while pageInfo.get("hasNextPage", False):
				if (assetsCursor := pageInfo.get("endCursor", None)) is None:
					raise GitHubError(f"GraphQL response announces further assets of release '{tagName}' without a cursor.")

				node = self._Query(RELEASE_ASSETS_QUERY, {"id": release.get("id", None), "cursor": assetsCursor})
				if not isinstance(node.get("node", None), dict) \
					or not isinstance(connection := node["node"].get("releaseAssets", None), dict) \
					or not isinstance(connection.get("nodes", None), list) \
					or not isinstance(pageInfo := connection.get("pageInfo", None), dict):
					raise GitHubError(f"GraphQL response has no further assets of release '{tagName}'.")

				assets.extend(connection["nodes"])

			release["releaseAssets"] = {"nodes": assets}
			if len(assets) == 0:
				continue

			if (databaseID := release.get("databaseId", None)) is None:
				raise GitHubError(f"Field 'databaseId' of release '{tagName}' is missing.")

			try:
				restRelease, _ = self.GetJSONObject(f"repos/{self._owner}/{self._repository}/releases/{databaseID}")
			except RESTError as cause:
				ex = GitHubError(f"Request for asset labels of release '{tagName}' failed: {cause}")
				for note in getattr(cause, "__notes__", []):
					ex.add_note(note)
				raise ex from cause

			if not isinstance(restAssets := restRelease.get("assets", None), list):
				raise GitHubError(f"REST response for release '{tagName}' has no assets.")

			labels = {asset.get("name", None): asset.get("label", None) for asset in restAssets if isinstance(asset, dict)}
			for asset in assets:
				if (assetName := asset.get("name", None)) not in labels:
					ex = GitHubError(f"REST response for release '{tagName}' lacks asset '{assetName}'.")
					ex.add_note("Assets may have changed while reading. Read the repository again.")
					raise ex

				asset["label"] = labels[assetName]

		document = {
			"nameWithOwner": repository.get("nameWithOwner", None),
			"url":           repository.get("url", None),
			"releases":      {"nodes": releases},
			"refs":          {"nodes": refs}
		}

		return Repository.Parse(document, fetchedAt)

	def _Query(self, query: str, variables: dict[str, Any]) -> JSONObject:
		"""
		Send a query to GitHub's GraphQL API and return the response's data.

		A query changes nothing, so a transiently failing request is tried again, unlike a ``POST`` sent by
		:meth:`~pyTooling.REST.RESTClient.PostJSONObject`.

		:param query:        The GraphQL query.
		:param variables:    The query's variables.
		:returns:            The field ``data`` of the response.
		:raises GitHubError: If the request fails. |br|
		                     The notes report the cause.
		:raises GitHubError: If the response reports errors. |br|
		                     The notes report each error. For an unknown repository, they say to check the repository's
		                     name and the token's permission; for an exceeded rate limit, to wait for its reset or use a
		                     token with a higher limit.
		:raises GitHubError: If the response is empty or has no data.
		"""
		try:
			response, _ = self._Request(HTTPMethod.POST, "graphql", {"query": query, "variables": variables})
		except RESTError as cause:
			ex = GitHubError(f"GraphQL request for repository '{self._owner}/{self._repository}' failed: {cause}")
			for note in getattr(cause, "__notes__", []):
				ex.add_note(note)
			raise ex from cause

		if response is None:
			raise GitHubError("GraphQL response is empty.")
		elif (errors := response.get("errors", None)) is not None:
			ex = GitHubError(f"GraphQL request for repository '{self._owner}/{self._repository}' failed.")
			types = set()
			for error in errors if isinstance(errors, list) else [errors]:
				if not isinstance(error, dict):
					ex.add_note(f"Error: {error}")
					continue

				errorType = error.get("type", None)
				if errorType is None and isinstance(extensions := error.get("extensions", None), dict):
					errorType = extensions.get("code", None)

				types.add(errorType)
				ex.add_note(f"{'Error' if errorType is None else errorType}: {error.get('message', '')}")

			if "NOT_FOUND" in types:
				ex.add_note("Check the repository's name, and that the token may read the repository.")

			if "RATE_LIMITED" in types:
				ex.add_note("GraphQL rate limit exceeded. Wait for its reset, or use a token with a higher limit.")

			raise ex
		elif not isinstance(data := response.get("data", None), dict):
			raise GitHubError("GraphQL response has no data.")

		return data

	def _AddErrorNotes(self, error: RESTError, status: int) -> None:
		"""
		Add a note saying what a failing status means for GitHub's APIs.

		The note names an invalid or expired token (401), an exceeded rate limit or a token that may not read the
		repository (403, 429), or says to check the repository's name and the token's permission (404).

		:param error:  The error the note is added to.
		:param status: The HTTP status the request failed with.
		"""
		if status == 401:
			error.add_note("Token is invalid or expired.")
		elif status in (403, 429):
			error.add_note("Rate limit exceeded, or the token may not read the repository.")
		elif status == 404:
			error.add_note("Check the repository's name, and that the token may read the repository.")
