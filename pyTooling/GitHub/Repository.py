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
A data model of a GitHub repository's releases and tags.

.. tree::

   - :class:`Repository`                                  | the releases and tags of a repository
     - :class:`~pyTooling.GitHub.Release.Release`         | a release, published at a tag
       - :class:`~pyTooling.GitHub.Release.ReleaseAsset`  | a file attached to the release
     - :class:`Tag`                                       | a tag and the commit it points to

:class:`~pyTooling.GitHub.ReleaseReader.ReleaseReader` reads the model through GitHub's GraphQL API.
:meth:`Repository.Parse` reads the API's ``Repository`` object, :meth:`Repository.ToJSON` writes the model in the
same shape, and :meth:`Repository.ToSnapshot` and :meth:`Repository.ParseSnapshot` add a format version and the time
the data was read, so a consumer can store the model and read it back without another request.

.. hint::

   See :ref:`high-level help <DATA/Release>` for explanations and usage examples.
"""
from __future__                import annotations

from datetime                  import datetime
from typing                    import Iterable, Iterator, Optional as Nullable, Self

from pyTooling.Common          import getFullyQualifiedName, StringEnum
from pyTooling.Decorators      import export, readonly
from pyTooling.GenericPath.URL import URL
from pyTooling.MetaClasses     import ExtendedType
from pyTooling.REST            import JSONObject

from pyTooling.GitHub          import GitHubError, _parseISO8601Timestamp, _parseURL
from pyTooling.GitHub.Release  import Release, _readNodes


# A class with a property named like a class - ``URL`` - can't name that class in an annotation: the class body's
# namespace, where annotations are evaluated, binds the name to the property.
_URL = URL


@export
class SnapshotVersion(StringEnum):
	"""Versions of the snapshot format written by :meth:`Repository.ToSnapshot`."""

	Version1 = "1"       #: GitHub's GraphQL ``Repository`` object, all pages merged, asset labels added.
	Latest =   Version1  #: The version :meth:`Repository.ToSnapshot` writes.


@export
class Tag(metaclass=ExtendedType, slots=True):
	"""
	A tag of a repository and the commit it points to.

	A tag exists without a release - a repository may tag every version and publish a release for a few of them.
	"""

	_parent:      Nullable[Repository]  #: Repository the tag belongs to.
	_name:        str                   #: Name of the tag.
	_commitSHA:   Nullable[str]         #: Commit the tag points to.
	_commitURL:   Nullable[URL]         #: URL of that commit.
	_committedAt: Nullable[datetime]    #: Time of that commit.
	_isAnnotated: bool                  #: True, if the tag is a tag object of its own.

	def __init__(
		self,
		name:        str,
		commitSHA:   Nullable[str]        = None,
		commitURL:   Nullable[URL]        = None,
		committedAt: Nullable[datetime]   = None,
		isAnnotated: bool                 = False,
		*,
		parent:      Nullable[Repository] = None
	) -> None:
		"""
		Initializes a tag.

		:param name:        Name of the tag.
		:param commitSHA:   Optional, commit the tag points to. Default: ``None``.
		:param commitURL:   Optional, URL of that commit. Default: ``None``.
		:param committedAt: Optional, time of that commit, with a time zone. Default: ``None``.
		:param isAnnotated: Optional, ``True``, if the tag is a tag object of its own. Default: ``False``.
		:param parent:      Optional, reference to the repository the tag belongs to. Default: ``None``.
		:raises ValueError: If parameter 'name' is ``None``.
		:raises TypeError:  If parameter 'name' or 'commitSHA' is not of type :class:`str`.
		:raises ValueError: If parameter 'name' or 'commitSHA' is empty.
		:raises TypeError:  If parameter 'commitURL' is not of type :class:`~pyTooling.GenericPath.URL.URL`.
		:raises TypeError:  If parameter 'committedAt' is not of type :class:`~datetime.datetime`.
		:raises ValueError: If parameter 'committedAt' has no time zone.
		:raises ValueError: If parameter 'isAnnotated' is ``None``.
		:raises TypeError:  If parameter 'isAnnotated' is not of type :class:`bool`.
		:raises TypeError:  If parameter 'parent' is not of type :class:`Repository`.
		:raises ValueError: If parameter 'parent' has a tag of the same name.
		"""
		if name is None:
			raise ValueError("Parameter 'name' is None.")

		for parameterName, text in (("name", name), ("commitSHA", commitSHA)):
			if text is not None and not isinstance(text, str):
				ex = TypeError(f"Parameter '{parameterName}' is not of type 'str'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(text)}'.")
				raise ex
			elif text == "":
				raise ValueError(f"Parameter '{parameterName}' is empty.")

		if commitURL is not None and not isinstance(commitURL, URL):
			ex = TypeError("Parameter 'commitURL' is not of type 'URL'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(commitURL)}'.")
			raise ex

		if committedAt is not None and not isinstance(committedAt, datetime):
			ex = TypeError("Parameter 'committedAt' is not of type 'datetime'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(committedAt)}'.")
			raise ex
		elif committedAt is not None and committedAt.utcoffset() is None:
			ex = ValueError("Parameter 'committedAt' has no time zone.")
			ex.add_note(f"Got value '{committedAt}'.")
			raise ex

		if isAnnotated is None:
			raise ValueError("Parameter 'isAnnotated' is None.")
		elif not isinstance(isAnnotated, bool):
			ex = TypeError("Parameter 'isAnnotated' is not of type 'bool'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(isAnnotated)}'.")
			raise ex

		self._parent =      None
		self._name =        name
		self._commitSHA =   commitSHA
		self._commitURL =   commitURL
		self._committedAt = committedAt
		self._isAnnotated = isAnnotated

		if parent is None:
			pass
		elif not isinstance(parent, Repository):
			ex = TypeError("Parameter 'parent' is not of type 'Repository'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(parent)}'.")
			raise ex
		else:
			parent._AddTag(self)

	@readonly
	def Parent(self) -> Nullable[Repository]:
		"""
		Read-only property to access the repository the tag belongs to (:attr:`_parent`).

		:returns: The repository, or ``None`` if the tag belongs to none.
		"""
		return self._parent

	@readonly
	def Name(self) -> str:
		"""
		Read-only property to access the tag's name (:attr:`_name`).

		:returns: The name, unique within the repository.
		"""
		return self._name

	@readonly
	def CommitSHA(self) -> Nullable[str]:
		"""
		Read-only property to access the commit the tag points to (:attr:`_commitSHA`).

		An annotated tag is resolved to the commit it points to. A tag may point to another kind of object, e.g. a tree.

		:returns: The commit's hash, or ``None`` if the tag points to no commit.
		"""
		return self._commitSHA

	@readonly
	def CommitURL(self) -> Nullable[URL]:
		"""
		Read-only property to access the URL of the commit the tag points to (:attr:`_commitURL`).

		:returns: The commit's URL on github.com, or ``None`` if the tag points to no commit.
		"""
		return self._commitURL

	@readonly
	def CommittedAt(self) -> Nullable[datetime]:
		"""
		Read-only property to access the time of the commit the tag points to (:attr:`_committedAt`).

		This is the only time a tag without a release has.

		:returns: The time with its time zone - UTC, as GitHub reports it -, or ``None`` if the tag points to no commit.
		"""
		return self._committedAt

	@readonly
	def IsAnnotated(self) -> bool:
		"""
		Read-only property to access whether the tag is an annotated tag (:attr:`_isAnnotated`).

		An annotated tag is a tag object of its own, carrying a message; a lightweight tag is a name for a commit.

		:returns: ``True``, if the tag is an annotated tag.
		"""
		return self._isAnnotated

	@readonly
	def Release(self) -> Nullable[Release]:
		"""
		Read-only property to return the release published at the tag.

		:returns: The release, or ``None`` if the tag belongs to no repository or the repository has no release of it.
		"""
		if self._parent is None:
			return None

		return self._parent._releases.get(self._name, None)

	@readonly
	def HasRelease(self) -> bool:
		"""
		Read-only property to return whether a release is published at the tag.

		:returns: ``True``, if the repository the tag belongs to has a release of it.
		"""
		return self._parent is not None and self._name in self._parent._releases

	def __str__(self) -> str:
		"""
		Return a string representation of the tag.

		:returns: The tag's name.
		"""
		return self._name

	@classmethod
	def Parse(cls, ref: JSONObject, path: str = "ref") -> Self:
		"""
		Read a tag from a ``Ref`` object of GitHub's GraphQL API.

		The ref's target is a ``Commit`` for a lightweight tag, and a ``Tag`` object for an annotated tag, whose own target
		is the commit - or another ``Tag`` object, which is followed as far as the object holds the targets.

		:param ref:          The ``Ref`` object below ``refs/tags/``.
		:param path:         Optional, position of the tag, for an exception's message. Default: ``'ref'``.
		:returns:            The tag.
		:raises TypeError:   If parameter 'ref' is not of type :class:`dict`.
		:raises GitHubError: If field ``name`` is missing.
		:raises GitHubError: If a target has no field ``__typename``.
		:raises GitHubError: If a ``Tag`` object has no field ``target``, i.e. tag objects are nested deeper than read.
		:raises GitHubError: If a ``Commit`` object has no field ``oid``.
		:raises GitHubError: If field ``committedDate`` isn't an ISO 8601 timestamp.
		"""
		if not isinstance(ref, dict):
			ex = TypeError("Parameter 'ref' is not of type 'dict'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(ref)}'.")
			raise ex

		if (name := ref.get("name", None)) is None:
			raise GitHubError(f"Field '{path}.name' is missing.")

		targetPath =  f"{path}.target"
		target =      ref.get("target", None)
		isAnnotated = False
		while target is not None:
			if (typeName := target.get("__typename", None)) is None:
				raise GitHubError(f"Field '{targetPath}.__typename' is missing.")
			elif typeName != "Tag":
				break
			elif "target" not in target:
				ex = GitHubError(f"Field '{targetPath}.target' is missing.")
				ex.add_note(f"Tag '{name}' points to tag objects nested deeper than read.")
				raise ex

			isAnnotated = True
			targetPath =  f"{targetPath}.target"
			target =      target["target"]

		if target is None or target["__typename"] != "Commit":
			return cls(name, isAnnotated=isAnnotated)
		elif (commitSHA := target.get("oid", None)) is None:
			raise GitHubError(f"Field '{targetPath}.oid' is missing.")

		return cls(
			name,
			commitSHA,
			_parseURL(target.get("url", None), f"{targetPath}.url"),
			_parseISO8601Timestamp(target.get("committedDate", None), f"{targetPath}.committedDate"),
			isAnnotated
		)

	def ToJSON(self) -> JSONObject:
		"""
		Write the tag as a ``Ref`` object of GitHub's GraphQL API.

		A target that is no commit is written as ``None``, and an annotated tag's ``Tag`` object without its own hash.

		:returns: The JSON object, which :meth:`Parse` reads back.
		"""
		target: Nullable[JSONObject]
		if self._commitSHA is None:
			target = None
		else:
			target = {
				"__typename":    "Commit",
				"oid":           self._commitSHA,
				"url":           None if self._commitURL is None else str(self._commitURL),
				"committedDate": None if self._committedAt is None else self._committedAt.isoformat()
			}

		if self._isAnnotated:
			target = {"__typename": "Tag", "target": target}

		return {"name": self._name, "target": target}


@export
class Repository(metaclass=ExtendedType, slots=True):
	"""
	The releases and tags of a GitHub repository, and the top of the tree.

	The repository is a collection of its releases: ``tagName in repository`` asks whether a release is published at a
	tag, ``repository[tagName]`` returns it, and iterating yields the releases in the order GitHub reported them, the
	newest first. The tags - with or without a release - are in :attr:`Tags`.
	"""

	_owner:     str                 #: Owner of the repository, a user or an organization.
	_name:      str                 #: Name of the repository.
	_url:       _URL                #: URL of the repository on github.com.
	_releases:  dict[str, Release]  #: Releases, by the name of their tag.
	_tags:      dict[str, Tag]      #: Tags, by their name.
	_fetchedAt: Nullable[datetime]  #: Time the data was read from GitHub.

	def __init__(
		self,
		owner:     str,
		name:      str,
		url:       _URL,
		releases:  Nullable[Iterable[Release]] = None,
		tags:      Nullable[Iterable[Tag]]     = None,
		*,
		fetchedAt: Nullable[datetime]          = None
	) -> None:
		"""
		Initializes the releases and tags of a repository.

		:param owner:       Owner of the repository, a user or an organization.
		:param name:        Name of the repository.
		:param url:         URL of the repository on github.com.
		:param releases:    Optional, the releases, which are attached to the repository. Default: ``None``.
		:param tags:        Optional, the tags, which are attached to the repository. Default: ``None``.
		:param fetchedAt:   Optional, time the data was read from GitHub, with a time zone. Default: ``None``.
		:raises ValueError: If parameter 'owner' or 'name' is ``None``.
		:raises TypeError:  If parameter 'owner' or 'name' is not of type :class:`str`.
		:raises ValueError: If parameter 'owner' or 'name' is empty or contains a ``/``.
		:raises ValueError: If parameter 'url' is ``None``.
		:raises TypeError:  If parameter 'url' is not of type :class:`~pyTooling.GenericPath.URL.URL`.
		:raises TypeError:  If an element of parameter 'releases' is not of type :class:`~pyTooling.GitHub.Release.Release`.
		:raises ValueError: If two elements of parameter 'releases' have the same tag.
		:raises TypeError:  If an element of parameter 'tags' is not of type :class:`Tag`.
		:raises ValueError: If two elements of parameter 'tags' have the same name.
		:raises TypeError:  If parameter 'fetchedAt' is not of type :class:`~datetime.datetime`.
		:raises ValueError: If parameter 'fetchedAt' has no time zone.
		"""
		for parameterName, text in (("owner", owner), ("name", name)):
			if text is None:
				raise ValueError(f"Parameter '{parameterName}' is None.")
			elif not isinstance(text, str):
				ex = TypeError(f"Parameter '{parameterName}' is not of type 'str'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(text)}'.")
				raise ex
			elif text == "" or "/" in text:
				ex = ValueError(f"Parameter '{parameterName}' is empty or contains a '/'.")
				ex.add_note(f"Got value '{text}'.")
				raise ex

		if url is None:
			raise ValueError("Parameter 'url' is None.")
		elif not isinstance(url, URL):
			ex = TypeError("Parameter 'url' is not of type 'URL'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(url)}'.")
			raise ex

		if fetchedAt is not None and not isinstance(fetchedAt, datetime):
			ex = TypeError("Parameter 'fetchedAt' is not of type 'datetime'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(fetchedAt)}'.")
			raise ex
		elif fetchedAt is not None and fetchedAt.utcoffset() is None:
			ex = ValueError("Parameter 'fetchedAt' has no time zone.")
			ex.add_note(f"Got value '{fetchedAt}'.")
			raise ex

		self._owner =     owner
		self._name =      name
		self._url =       url
		self._releases =  {}
		self._tags =      {}
		self._fetchedAt = fetchedAt

		if releases is not None:
			for release in releases:
				if not isinstance(release, Release):
					ex = TypeError("Element of parameter 'releases' is not of type 'Release'.")
					ex.add_note(f"Got type '{getFullyQualifiedName(release)}'.")
					raise ex

				self._AddRelease(release)

		if tags is not None:
			for tag in tags:
				if not isinstance(tag, Tag):
					ex = TypeError("Element of parameter 'tags' is not of type 'Tag'.")
					ex.add_note(f"Got type '{getFullyQualifiedName(tag)}'.")
					raise ex

				self._AddTag(tag)

	def _AddRelease(self, release: Release) -> None:
		"""
		Attach a release to the repository.

		:param release:     The release.
		:raises ValueError: If the release belongs to a repository already.
		:raises ValueError: If the repository has a release of the same tag.
		"""
		if release._parent is not None:
			raise ValueError(f"Release '{release._tagName}' belongs to repository '{release._parent}' already.")
		elif release._tagName in self._releases:
			ex = ValueError(f"Repository '{self}' has a release of tag '{release._tagName}' already.")
			ex.add_note("GitHub reports drafts to a token with write access, and two drafts may name the same tag.")
			raise ex

		release._parent = self
		self._releases[release._tagName] = release

	def _AddTag(self, tag: Tag) -> None:
		"""
		Attach a tag to the repository.

		:param tag:         The tag.
		:raises ValueError: If the tag belongs to a repository already.
		:raises ValueError: If the repository has a tag of the same name.
		"""
		if tag._parent is not None:
			raise ValueError(f"Tag '{tag._name}' belongs to repository '{tag._parent}' already.")
		elif tag._name in self._tags:
			raise ValueError(f"Repository '{self}' has a tag '{tag._name}' already.")

		tag._parent = self
		self._tags[tag._name] = tag

	@readonly
	def Owner(self) -> str:
		"""
		Read-only property to access the repository's owner (:attr:`_owner`).

		:returns: The name of the user or organization owning the repository.
		"""
		return self._owner

	@readonly
	def Name(self) -> str:
		"""
		Read-only property to access the repository's name (:attr:`_name`).

		:returns: The name, without the owner.
		"""
		return self._name

	@readonly
	def URL(self) -> _URL:
		"""
		Read-only property to access the repository's URL (:attr:`_url`).

		:returns: The URL on github.com.
		"""
		return self._url

	@readonly
	def Releases(self) -> dict[str, Release]:
		"""
		Read-only property to access the releases (:attr:`_releases`).

		:returns: Dictionary of a tag's name to the release published at it, the newest first.
		"""
		return self._releases

	@readonly
	def Tags(self) -> dict[str, Tag]:
		"""
		Read-only property to access the tags (:attr:`_tags`).

		:returns: Dictionary of a tag's name to the tag, the tag of the newest commit first.
		"""
		return self._tags

	@readonly
	def FetchedAt(self) -> Nullable[datetime]:
		"""
		Read-only property to access the time the data was read from GitHub (:attr:`_fetchedAt`).

		A consumer storing the model tells the age of what it stored by this time.

		:returns: The time with its time zone, or ``None`` if unknown.
		"""
		return self._fetchedAt

	@readonly
	def LatestRelease(self) -> Nullable[Release]:
		"""
		Read-only property to return the release GitHub marks as the latest (:attr:`Release.IsLatest
		<pyTooling.GitHub.Release.Release.IsLatest>`).

		:returns: The latest release, or ``None`` if the repository has no published release.
		"""
		for release in self._releases.values():
			if release._isLatest:
				return release

		return None

	def __len__(self) -> int:
		"""
		Return the number of releases.

		:returns: The number of releases.
		"""
		return len(self._releases)

	def __iter__(self) -> Iterator[Release]:
		"""
		Iterate the releases, the newest first.

		:returns: An iterator of the releases.
		"""
		return iter(self._releases.values())

	def __contains__(self, tagName: str) -> bool:
		"""
		Check whether a release is published at a tag.

		:param tagName: The tag's name.
		:returns:       ``True``, if the repository has a release of that tag.
		"""
		return tagName in self._releases

	def __getitem__(self, tagName: str) -> Release:
		"""
		Return the release published at a tag.

		:param tagName:   The tag's name.
		:returns:         The release.
		:raises KeyError: If the repository has no release of that tag.
		"""
		return self._releases[tagName]

	def __str__(self) -> str:
		"""
		Return a string representation of the repository.

		:returns: The repository as ``owner/name``.
		"""
		return f"{self._owner}/{self._name}"

	@classmethod
	def Parse(cls, repository: JSONObject, fetchedAt: Nullable[datetime] = None) -> Self:
		"""
		Read the releases and tags of a repository from a ``Repository`` object of GitHub's GraphQL API.

		The object holds the fields ``nameWithOwner``, ``url``, ``releases`` and ``refs`` (the tags) as
		:class:`~pyTooling.GitHub.ReleaseReader.ReleaseReader` queries them, each connection with all its nodes.

		:param repository:   The ``Repository`` object.
		:param fetchedAt:    Optional, time the data was read from GitHub, with a time zone. Default: ``None``.
		:returns:            The repository, with its releases and tags attached.
		:raises TypeError:   If parameter 'repository' is not of type :class:`dict`.
		:raises GitHubError: If field ``nameWithOwner`` or ``url`` is missing.
		:raises GitHubError: If field ``nameWithOwner`` isn't of the form ``owner/name``.
		:raises GitHubError: If field ``releases`` or ``refs`` holds no complete list of nodes.
		:raises GitHubError: If a release or a tag can't be read.
		"""
		if not isinstance(repository, dict):
			ex = TypeError("Parameter 'repository' is not of type 'dict'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(repository)}'.")
			raise ex

		for field in ("nameWithOwner", "url"):
			if repository.get(field, None) is None:
				raise GitHubError(f"Field 'repository.{field}' is missing.")

		if len(parts := repository["nameWithOwner"].split("/")) != 2:
			ex = GitHubError("Field 'repository.nameWithOwner' isn't of the form 'owner/name'.")
			ex.add_note(f"Got '{repository['nameWithOwner']}'.")
			raise ex

		releases = [
			Release.Parse(release, f"repository.releases.nodes[{position}]")
			for position, release in enumerate(_readNodes(repository, "releases", "repository"))
		]
		tags =     [
			Tag.Parse(ref, f"repository.refs.nodes[{position}]")
			for position, ref in enumerate(_readNodes(repository, "refs", "repository"))
		]

		return cls(parts[0], parts[1], URL.Parse(repository["url"]), releases, tags, fetchedAt=fetchedAt)

	def ToJSON(self) -> JSONObject:
		"""
		Write the releases and tags as a ``Repository`` object of GitHub's GraphQL API.

		Each connection holds all its nodes, and an asset its label.

		:returns: The JSON object, which :meth:`Parse` reads back.
		"""
		return {
			"nameWithOwner": str(self),
			"url":           str(self._url),
			"releases":      {"nodes": [release.ToJSON() for release in self._releases.values()]},
			"refs":          {"nodes": [tag.ToJSON() for tag in self._tags.values()]}
		}

	@classmethod
	def ParseSnapshot(cls, snapshot: JSONObject) -> Self:
		"""
		Read the releases and tags of a repository from a snapshot written by :meth:`ToSnapshot`.

		:param snapshot:     The snapshot.
		:returns:            The repository, with its releases and tags attached.
		:raises TypeError:   If parameter 'snapshot' is not of type :class:`dict`.
		:raises GitHubError: If field ``version`` or ``repository`` is missing.
		:raises GitHubError: If field ``version`` names an unknown version. |br|
		                     The note lists the known versions.
		:raises GitHubError: If field ``fetchedAt`` isn't an ISO 8601 timestamp.
		:raises GitHubError: If field ``repository`` can't be read (see :meth:`Parse`).
		"""
		if not isinstance(snapshot, dict):
			ex = TypeError("Parameter 'snapshot' is not of type 'dict'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(snapshot)}'.")
			raise ex

		for field in ("version", "repository"):
			if snapshot.get(field, None) is None:
				raise GitHubError(f"Field '{field}' is missing.")

		try:
			SnapshotVersion.Parse(snapshot["version"])
		except (TypeError, ValueError) as cause:
			ex = GitHubError(f"Snapshot version '{snapshot['version']}' is unknown.")
			ex.add_note(f"Known: {', '.join(member.value for member in SnapshotVersion)}.")
			raise ex from cause

		return cls.Parse(snapshot["repository"], _parseISO8601Timestamp(snapshot.get("fetchedAt", None), "fetchedAt"))

	def ToSnapshot(self) -> JSONObject:
		"""
		Write the releases and tags as a snapshot, which :meth:`ParseSnapshot` reads back.

		The snapshot holds the format's version (:attr:`SnapshotVersion.Latest`), the time the data was read
		(:attr:`FetchedAt`) and the repository as :meth:`ToJSON` writes it.

		:returns: The snapshot as a JSON object, to be written with :func:`json.dump`.
		"""
		return {
			"version":    SnapshotVersion.Latest.value,
			"fetchedAt":  None if self._fetchedAt is None else self._fetchedAt.isoformat(),
			"repository": self.ToJSON()
		}
