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

   - :class:`Repository` | the releases and tags of a repository
     - :class:`Release`  | a release, published at a tag
       - :class:`Asset`  | a file attached to the release
     - :class:`Tag`      | a tag and the commit it points to

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
from urllib.parse              import quote

from pyTooling.Common          import getFullyQualifiedName, StringEnum
from pyTooling.Decorators      import export, readonly
from pyTooling.GenericPath.URL import URL
from pyTooling.MetaClasses     import ExtendedType
from pyTooling.REST            import JSONObject

from pyTooling.GitHub          import GitHubError, _parseISO8601Timestamp, _parseURL


# A class with a property named like a class - ``URL`` - can't name that class in an annotation: the class body's
# namespace, where annotations are evaluated, binds the name to the property.
_URL = URL


@export
class SourceArchive(StringEnum):
	"""The formats of the source code archive GitHub offers for a tag."""

	Zip =     "zip"     #: A ZIP file.
	Tarball = "tar.gz"  #: A gzip-compressed TAR file.


@export
class SnapshotVersion(StringEnum):
	"""Versions of the snapshot format written by :meth:`Repository.ToSnapshot`."""

	Version1 = "1"       #: GitHub's GraphQL ``Repository`` object: pages merged, no drafts, labels added.
	Latest =   Version1  #: The version :meth:`Repository.ToSnapshot` writes.


def _readNodes(json: JSONObject, field: str, path: str) -> list[JSONObject]:
	"""
	Read the nodes of a connection in a response of GitHub's GraphQL API.

	:param json:         The object holding the connection.
	:param field:        Name of the connection's field.
	:param path:         Position of the object, for the exception's message.
	:returns:            The nodes.
	:raises GitHubError: If the field is missing.
	:raises GitHubError: If the connection has no list of nodes.
	:raises GitHubError: If the connection has a further page.
	"""
	if (connection := json.get(field, None)) is None:
		raise GitHubError(f"Field '{path}.{field}' is missing.")
	elif not isinstance(connection, dict) or not isinstance(nodes := connection.get("nodes", None), list):
		raise GitHubError(f"Field '{path}.{field}' has no list of nodes.")
	elif isinstance(pageInfo := connection.get("pageInfo", None), dict) and pageInfo.get("hasNextPage", False):
		ex = GitHubError(f"Field '{path}.{field}' holds only the first page of nodes.")
		ex.add_note("Merge all pages into one list of nodes, before parsing it.")
		raise ex

	return nodes


@export
class Asset(metaclass=ExtendedType, slots=True):
	"""A file attached to a release."""

	_parent:      Nullable[Release]  #: Release the file is attached to.
	_name:        str                #: File name of the asset.
	_label:       Nullable[str]      #: Text shown instead of the file name.
	_digest:      Nullable[str]      #: Checksum of the asset as ``algorithm:value``.
	_contentType: str                #: Media type of the asset.
	_size:        int                #: Size of the asset in bytes.
	_downloadURL: URL                #: URL to download the asset from.

	def __init__(
		self,
		name:        str,
		downloadURL: URL,
		contentType: str,
		size:        int,
		label:       Nullable[str] = None,
		digest:      Nullable[str] = None,
		*,
		parent:      Nullable[Release] = None
	) -> None:
		"""
		Initializes a file attached to a release.

		:param name:        File name of the asset.
		:param downloadURL: URL to download the asset from.
		:param contentType: Media type of the asset.
		:param size:        Size of the asset in bytes.
		:param label:       Optional, text shown instead of the file name. Default: ``None``.
		:param digest:      Optional, checksum of the asset as ``algorithm:value``. Default: ``None``.
		:param parent:      Optional, reference to the release the asset is attached to. Default: ``None``.
		:raises ValueError: If parameter 'name' or 'contentType' is ``None``.
		:raises TypeError:  If parameter 'name' or 'contentType' is not of type :class:`str`.
		:raises ValueError: If parameter 'name' or 'contentType' is empty.
		:raises ValueError: If parameter 'downloadURL' is ``None``.
		:raises TypeError:  If parameter 'downloadURL' is not of type :class:`~pyTooling.GenericPath.URL.URL`.
		:raises ValueError: If parameter 'size' is ``None``.
		:raises TypeError:  If parameter 'size' is not of type :class:`int`.
		:raises ValueError: If parameter 'size' is negative.
		:raises TypeError:  If parameter 'label' is not of type :class:`str`.
		:raises ValueError: If parameter 'label' is empty.
		:raises TypeError:  If parameter 'digest' is not of type :class:`str`.
		:raises ValueError: If parameter 'digest' isn't of the form ``algorithm:value``.
		:raises TypeError:  If parameter 'parent' is not of type :class:`Release`.
		:raises ValueError: If parameter 'parent' has an asset of the same name.
		"""
		for parameterName, text in (("name", name), ("contentType", contentType)):
			if text is None:
				raise ValueError(f"Parameter '{parameterName}' is None.")
			elif not isinstance(text, str):
				ex = TypeError(f"Parameter '{parameterName}' is not of type 'str'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(text)}'.")
				raise ex
			elif text == "":
				raise ValueError(f"Parameter '{parameterName}' is empty.")

		if downloadURL is None:
			raise ValueError("Parameter 'downloadURL' is None.")
		elif not isinstance(downloadURL, URL):
			ex = TypeError("Parameter 'downloadURL' is not of type 'URL'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(downloadURL)}'.")
			raise ex

		if size is None:
			raise ValueError("Parameter 'size' is None.")
		elif isinstance(size, bool) or not isinstance(size, int):
			ex = TypeError("Parameter 'size' is not of type 'int'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(size)}'.")
			raise ex
		elif size < 0:
			ex = ValueError("Parameter 'size' is negative.")
			ex.add_note(f"Got value '{size}'.")
			raise ex

		if label is not None and not isinstance(label, str):
			ex = TypeError("Parameter 'label' is not of type 'str'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(label)}'.")
			raise ex
		elif label == "":
			raise ValueError("Parameter 'label' is empty.")

		if digest is not None and not isinstance(digest, str):
			ex = TypeError("Parameter 'digest' is not of type 'str'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(digest)}'.")
			raise ex
		elif digest is not None and "" in digest.partition(":"):
			ex = ValueError("Parameter 'digest' isn't of the form 'algorithm:value'.")
			ex.add_note(f"Got value '{digest}'.")
			raise ex

		self._parent =      None
		self._name =        name
		self._label =       label
		self._digest =      digest
		self._contentType = contentType
		self._size =        size
		self._downloadURL = downloadURL

		if parent is None:
			pass
		elif not isinstance(parent, Release):
			ex = TypeError("Parameter 'parent' is not of type 'Release'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(parent)}'.")
			raise ex
		elif name in parent._assets:
			raise ValueError(f"Release '{parent._tagName}' has an asset '{name}' already.")
		else:
			self._parent = parent
			parent._assets[name] = self

	@readonly
	def Parent(self) -> Nullable[Release]:
		"""
		Read-only property to access the release the asset is attached to (:attr:`_parent`).

		:returns: The release, or ``None`` if the asset isn't attached to one.
		"""
		return self._parent

	@readonly
	def Name(self) -> str:
		"""
		Read-only property to access the asset's file name (:attr:`_name`).

		:returns: The file name, unique within its release.
		"""
		return self._name

	@readonly
	def Label(self) -> Nullable[str]:
		"""
		Read-only property to access the text shown instead of the file name (:attr:`_label`).

		GitHub shows the label on the release page, when the asset has one, e.g. ``GHDL - v5.0.1 - Windows (x86-64,
		MinGW64, standalone) - mcode backend`` for ``ghdl-mcode-5.0.1-mingw64.zip``.

		:returns: The label, or ``None`` if the asset has none.
		"""
		return self._label

	@readonly
	def Digest(self) -> Nullable[str]:
		"""
		Read-only property to access the asset's checksum (:attr:`_digest`).

		GitHub computes it on upload as ``algorithm:value``, e.g. ``sha256:8c7dd2e9...`` - for an asset uploaded before
		GitHub computed checksums, there is none.

		:returns: The checksum as ``algorithm:value``, or ``None`` if GitHub has none.
		"""
		return self._digest

	@readonly
	def ContentType(self) -> str:
		"""
		Read-only property to access the asset's media type (:attr:`_contentType`).

		The uploader declares it, e.g. ``application/zip`` for a ZIP file.

		:returns: The media type.
		"""
		return self._contentType

	@readonly
	def Size(self) -> int:
		"""
		Read-only property to access the asset's size (:attr:`_size`).

		:returns: The size in bytes.
		"""
		return self._size

	@readonly
	def DownloadURL(self) -> URL:
		"""
		Read-only property to access the URL to download the asset from (:attr:`_downloadURL`).

		:returns: The download URL on github.com.
		"""
		return self._downloadURL

	def __str__(self) -> str:
		"""
		Return a string representation of the asset.

		:returns: The asset's file name.
		"""
		return self._name

	@classmethod
	def Parse(cls, asset: JSONObject, path: str = "asset") -> Self:
		"""
		Read an asset from a ``ReleaseAsset`` object of GitHub's GraphQL API.

		GitHub's GraphQL API reports no label, so the field ``label`` is read when present, as
		:class:`~pyTooling.GitHub.ReleaseReader.ReleaseReader` adds it from the REST API. An empty label is no label.

		:param asset:        The ``ReleaseAsset`` object.
		:param path:         Optional, position of the asset, for an exception's message. Default: ``'asset'``.
		:returns:            The asset.
		:raises TypeError:   If parameter 'asset' is not of type :class:`dict`.
		:raises GitHubError: If field ``name``, ``contentType``, ``size`` or ``downloadUrl`` is missing.
		"""
		if not isinstance(asset, dict):
			ex = TypeError("Parameter 'asset' is not of type 'dict'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(asset)}'.")
			raise ex

		for field in ("name", "contentType", "size", "downloadUrl"):
			if asset.get(field, None) is None:
				raise GitHubError(f"Field '{path}.{field}' is missing.")

		label = asset.get("label", None)

		return cls(
			asset["name"],
			URL.Parse(asset["downloadUrl"]),
			asset["contentType"],
			asset["size"],
			None if label == "" else label,
			asset.get("digest", None)
		)

	def ToJSON(self) -> JSONObject:
		"""
		Write the asset as a ``ReleaseAsset`` object of GitHub's GraphQL API, plus its label.

		:returns: The JSON object, which :meth:`Parse` reads back.
		"""
		return {
			"name":        self._name,
			"label":       self._label,
			"contentType": self._contentType,
			"size":        self._size,
			"downloadUrl": str(self._downloadURL),
			"digest":      self._digest
		}


@export
class CommitReference(metaclass=ExtendedType, slots=True):
	"""
	Base-class of a tag and a release: an element of a repository named by a tag, which points to a commit.

	An annotated tag is resolved to the commit it points to.
	"""

	_parent:    Nullable[Repository]  #: Repository the element belongs to.
	_tagName:   str                   #: Name of the tag.
	_commitSHA: Nullable[str]         #: Commit the tag points to.
	_commitURL: Nullable[URL]         #: URL of that commit.

	def __init__(
		self,
		tagName:   str,
		commitSHA: Nullable[str] = None,
		commitURL: Nullable[URL] = None
	) -> None:
		"""
		Initializes the tag's name and the commit it points to.

		:param tagName:     Name of the tag.
		:param commitSHA:   Optional, commit the tag points to. Default: ``None``.
		:param commitURL:   Optional, URL of that commit. Default: ``None``.
		:raises ValueError: If parameter 'tagName' is ``None``.
		:raises TypeError:  If parameter 'tagName' or 'commitSHA' is not of type :class:`str`.
		:raises ValueError: If parameter 'tagName' or 'commitSHA' is empty.
		:raises TypeError:  If parameter 'commitURL' is not of type :class:`~pyTooling.GenericPath.URL.URL`.
		"""
		if tagName is None:
			raise ValueError("Parameter 'tagName' is None.")

		for parameterName, text in (("tagName", tagName), ("commitSHA", commitSHA)):
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

		self._parent =    None
		self._tagName =   tagName
		self._commitSHA = commitSHA
		self._commitURL = commitURL

	@readonly
	def Parent(self) -> Nullable[Repository]:
		"""
		Read-only property to access the repository the element belongs to (:attr:`_parent`).

		:returns: The repository, or ``None`` if the element belongs to none.
		"""
		return self._parent

	@readonly
	def TagName(self) -> str:
		"""
		Read-only property to access the tag's name (:attr:`_tagName`).

		:returns: The tag's name, unique among the repository's tags and among its releases.
		"""
		return self._tagName

	@readonly
	def CommitSHA(self) -> Nullable[str]:
		"""
		Read-only property to access the commit the tag points to (:attr:`_commitSHA`).

		:returns: The commit's hash, or ``None`` if the tag doesn't exist or points to no commit, e.g. to a tree.
		"""
		return self._commitSHA

	@readonly
	def CommitURL(self) -> Nullable[URL]:
		"""
		Read-only property to access the URL of the commit the tag points to (:attr:`_commitURL`).

		:returns: The commit's URL on github.com, or ``None`` if the tag doesn't exist or points to no commit.
		"""
		return self._commitURL

	def __str__(self) -> str:
		"""
		Return a string representation of the element.

		:returns: The tag's name.
		"""
		return self._tagName


@export
class Release(CommitReference):
	"""
	A release, published at a tag.

	A draft is no release: it is unpublished and may change, so the model has none.

	The release's commit is the one its **tag** points to - not GitHub's ``target_commitish``, which is usually a
	branch's name. The time is when the release was **published**, not when it was created, which is the commit's time.

	The release is a collection of its assets: ``name in release`` asks whether a file of that name is attached,
	``release[name]`` returns it, and iterating yields the assets in the order GitHub reported them.
	"""

	_url:          _URL                #: URL of the release page.
	_name:         Nullable[str]       #: Title of the release.
	_description:  str                 #: Release notes as Markdown.
	_publishedAt:  Nullable[datetime]  #: Time the release was published.
	_isPrerelease: bool                #: True, if the release is a pre-release.
	_isLatest:     bool                #: True, if the release is the repository's latest release.
	_assets:       dict[str, Asset]    #: Files attached to the release, by file name.

	def __init__(
		self,
		tagName:      str,
		url:          _URL,
		name:         Nullable[str]             = None,
		description:  str                       = "",
		publishedAt:  Nullable[datetime]        = None,
		isPrerelease: bool                      = False,
		isLatest:     bool                      = False,
		commitSHA:    Nullable[str]             = None,
		commitURL:    Nullable[_URL]            = None,
		assets:       Nullable[Iterable[Asset]] = None,
		*,
		parent:       Nullable[Repository]      = None
	) -> None:
		"""
		Initializes a release.

		:param tagName:      Name of the tag the release is published at.
		:param url:          URL of the release page.
		:param name:         Optional, title of the release. Default: ``None``.
		:param description:  Optional, release notes as Markdown. Default: ``""``.
		:param publishedAt:  Optional, time the release was published, with a time zone. Default: ``None``.
		:param isPrerelease: Optional, ``True``, if the release is a pre-release. Default: ``False``.
		:param isLatest:     Optional, ``True``, if the release is the repository's latest release. Default: ``False``.
		:param commitSHA:    Optional, commit the tag points to. Default: ``None``.
		:param commitURL:    Optional, URL of that commit. Default: ``None``.
		:param assets:       Optional, the release's assets, which are attached to it. Default: ``None``.
		:param parent:       Optional, reference to the repository the release belongs to. Default: ``None``.
		:raises ValueError:  If parameter 'tagName' is ``None``.
		:raises TypeError:   If parameter 'tagName' is not of type :class:`str`.
		:raises ValueError:  If parameter 'tagName' is empty.
		:raises ValueError:  If parameter 'url' is ``None``.
		:raises TypeError:   If parameter 'url' or 'commitURL' is not of type :class:`~pyTooling.GenericPath.URL.URL`.
		:raises TypeError:   If parameter 'name' or 'commitSHA' is not of type :class:`str`.
		:raises ValueError:  If parameter 'name' or 'commitSHA' is empty.
		:raises ValueError:  If parameter 'description' is ``None``.
		:raises TypeError:   If parameter 'description' is not of type :class:`str`.
		:raises TypeError:   If parameter 'publishedAt' is not of type :class:`~datetime.datetime`.
		:raises ValueError:  If parameter 'publishedAt' has no time zone.
		:raises ValueError:  If parameter 'isPrerelease' or 'isLatest' is ``None``.
		:raises TypeError:   If parameter 'isPrerelease' or 'isLatest' is not of type :class:`bool`.
		:raises TypeError:   If an element of parameter 'assets' is not of type :class:`Asset`.
		:raises ValueError:  If two elements of parameter 'assets' have the same name.
		:raises ValueError:  If an element of parameter 'assets' is attached to a release already.
		:raises TypeError:   If parameter 'parent' is not of type :class:`Repository`.
		:raises ValueError:  If parameter 'parent' has a release of the same tag.
		"""
		super().__init__(tagName, commitSHA, commitURL)

		if url is None:
			raise ValueError("Parameter 'url' is None.")
		elif not isinstance(url, URL):
			ex = TypeError("Parameter 'url' is not of type 'URL'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(url)}'.")
			raise ex

		if name is not None and not isinstance(name, str):
			ex = TypeError("Parameter 'name' is not of type 'str'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(name)}'.")
			raise ex
		elif name == "":
			raise ValueError("Parameter 'name' is empty.")

		if description is None:
			raise ValueError("Parameter 'description' is None.")
		elif not isinstance(description, str):
			ex = TypeError("Parameter 'description' is not of type 'str'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(description)}'.")
			raise ex

		if publishedAt is not None and not isinstance(publishedAt, datetime):
			ex = TypeError("Parameter 'publishedAt' is not of type 'datetime'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(publishedAt)}'.")
			raise ex
		elif publishedAt is not None and publishedAt.utcoffset() is None:
			ex = ValueError("Parameter 'publishedAt' has no time zone.")
			ex.add_note(f"Got value '{publishedAt}'.")
			raise ex

		for parameterName, flag in (("isPrerelease", isPrerelease), ("isLatest", isLatest)):
			if flag is None:
				raise ValueError(f"Parameter '{parameterName}' is None.")
			elif not isinstance(flag, bool):
				ex = TypeError(f"Parameter '{parameterName}' is not of type 'bool'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(flag)}'.")
				raise ex

		self._url =          url
		self._name =         name
		self._description =  description
		self._publishedAt =  publishedAt
		self._isPrerelease = isPrerelease
		self._isLatest =     isLatest
		self._assets =       {}

		if assets is not None:
			for asset in assets:
				if not isinstance(asset, Asset):
					ex = TypeError("Element of parameter 'assets' is not of type 'Asset'.")
					ex.add_note(f"Got type '{getFullyQualifiedName(asset)}'.")
					raise ex
				elif asset._parent is not None:
					raise ValueError(f"Asset '{asset._name}' is attached to release '{asset._parent._tagName}' already.")
				elif asset._name in self._assets:
					raise ValueError(f"Release '{tagName}' has an asset '{asset._name}' already.")

				asset._parent = self
				self._assets[asset._name] = asset

		if parent is None:
			pass
		elif not isinstance(parent, Repository):
			ex = TypeError("Parameter 'parent' is not of type 'Repository'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(parent)}'.")
			raise ex
		elif tagName in parent._releases:
			raise ValueError(f"Repository '{parent}' has a release of tag '{tagName}' already.")
		else:
			self._parent = parent
			parent._releases[tagName] = self

	@readonly
	def URL(self) -> _URL:
		"""
		Read-only property to access the URL of the release page (:attr:`_url`).

		:returns: The release page's URL on github.com.
		"""
		return self._url

	@readonly
	def Name(self) -> Nullable[str]:
		"""
		Read-only property to access the release's title (:attr:`_name`).

		GitHub's release page shows the tag's name instead, when a release has no title.

		:returns: The title, or ``None`` if the release has none.
		"""
		return self._name

	@readonly
	def Description(self) -> str:
		"""
		Read-only property to access the release notes (:attr:`_description`).

		:returns: The release notes as GitHub Flavored Markdown, empty if the release has none.
		"""
		return self._description

	@readonly
	def PublishedAt(self) -> Nullable[datetime]:
		"""
		Read-only property to access the time the release was published (:attr:`_publishedAt`).

		:returns: The time with its time zone - UTC, as GitHub reports it -, or ``None`` if unknown.
		"""
		return self._publishedAt

	@readonly
	def IsPrerelease(self) -> bool:
		"""
		Read-only property to access whether the release is a pre-release (:attr:`_isPrerelease`).

		:returns: ``True``, if the release is a pre-release.
		"""
		return self._isPrerelease

	@readonly
	def IsLatest(self) -> bool:
		"""
		Read-only property to access whether the release is the repository's latest release (:attr:`_isLatest`).

		GitHub decides which release is the latest, or the maintainer marks it by hand - it isn't necessarily the
		newest one, and never a draft or a pre-release.

		:returns: ``True``, if the release is the latest release.
		"""
		return self._isLatest

	@readonly
	def Assets(self) -> dict[str, Asset]:
		"""
		Read-only property to access the files attached to the release (:attr:`_assets`).

		:returns: Dictionary of a file name to its asset, in the order GitHub reported them.
		"""
		return self._assets

	def SourceArchiveURL(self, archive: SourceArchive) -> _URL:
		"""
		Return the URL of a source code archive of the release's tag, as GitHub's release page links it.

		GitHub creates the archive on request, so it is no asset of the release and has no size.

		:param archive:      The archive's format.
		:returns:            The archive's URL on github.com.
		:raises ValueError:  If parameter 'archive' is ``None``.
		:raises TypeError:   If parameter 'archive' is not of type :class:`SourceArchive`.
		:raises GitHubError: If the release belongs to no repository.
		"""
		if archive is None:
			raise ValueError("Parameter 'archive' is None.")
		elif not isinstance(archive, SourceArchive):
			ex = TypeError("Parameter 'archive' is not of type 'SourceArchive'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(archive)}'.")
			raise ex

		if self._parent is None:
			raise GitHubError(f"Release '{self._tagName}' belongs to no repository.")

		return self._parent._url / f"archive/refs/tags/{quote(self._tagName)}.{archive}"

	def __len__(self) -> int:
		"""
		Return the number of assets.

		:returns: The number of files attached to the release.
		"""
		return len(self._assets)

	def __iter__(self) -> Iterator[Asset]:
		"""
		Iterate the assets, in the order GitHub reported them.

		:returns: An iterator of the assets.
		"""
		return iter(self._assets.values())

	def __contains__(self, name: str) -> bool:
		"""
		Check whether a file of a name is attached to the release.

		:param name: The file name.
		:returns:    ``True``, if the release has an asset of that name.
		"""
		return name in self._assets

	def __getitem__(self, name: str) -> Asset:
		"""
		Return the asset of a file name.

		:param name:      The file name.
		:returns:         The asset.
		:raises KeyError: If the release has no asset of that name.
		"""
		return self._assets[name]

	@classmethod
	def Parse(cls, release: JSONObject, path: str = "release") -> Self:
		"""
		Read a release and its assets from a ``Release`` object of GitHub's GraphQL API.

		An empty title is no title, and no release notes are empty release notes. A draft is rejected, as it is no
		release - :meth:`Repository.Parse` skips drafts.

		:param release:      The ``Release`` object.
		:param path:         Optional, position of the release, for an exception's message. Default: ``'release'``.
		:returns:            The release, with its assets attached.
		:raises TypeError:   If parameter 'release' is not of type :class:`dict`.
		:raises GitHubError: If field ``tagName``, ``url``, ``isDraft``, ``isPrerelease``, ``isLatest`` or
		                     ``releaseAssets`` is missing.
		:raises GitHubError: If the release is a draft.
		:raises GitHubError: If field ``tagCommit`` has no ``oid``.
		:raises GitHubError: If field ``releaseAssets`` holds no complete list of nodes.
		:raises GitHubError: If field ``publishedAt`` isn't an ISO 8601 timestamp.
		"""
		if not isinstance(release, dict):
			ex = TypeError("Parameter 'release' is not of type 'dict'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(release)}'.")
			raise ex

		for field in ("tagName", "url", "isDraft", "isPrerelease", "isLatest"):
			if release.get(field, None) is None:
				raise GitHubError(f"Field '{path}.{field}' is missing.")

		if release["isDraft"] is True:
			raise GitHubError(f"Release '{release['tagName']}' is a draft.")

		if (tagCommit := release.get("tagCommit", None)) is None:
			commitSHA = None
			commitURL = None
		elif (commitSHA := tagCommit.get("oid", None)) is None:
			raise GitHubError(f"Field '{path}.tagCommit.oid' is missing.")
		else:
			commitURL = _parseURL(tagCommit.get("url", None), f"{path}.tagCommit.url")

		name =        release.get("name", None)
		description = release.get("description", None)
		assets =      [
			Asset.Parse(asset, f"{path}.releaseAssets.nodes[{position}]")
			for position, asset in enumerate(_readNodes(release, "releaseAssets", path))
		]

		return cls(
			release["tagName"],
			URL.Parse(release["url"]),
			None if name == "" else name,
			"" if description is None else description,
			_parseISO8601Timestamp(release.get("publishedAt", None), f"{path}.publishedAt"),
			release["isPrerelease"],
			release["isLatest"],
			commitSHA,
			commitURL,
			assets
		)

	def ToJSON(self) -> JSONObject:
		"""
		Write the release as a ``Release`` object of GitHub's GraphQL API.

		:returns: The JSON object, which :meth:`Parse` reads back.
		"""
		if self._commitSHA is None:
			tagCommit = None
		else:
			tagCommit = {"oid": self._commitSHA, "url": None if self._commitURL is None else str(self._commitURL)}

		return {
			"tagName":       self._tagName,
			"name":          self._name,
			"description":   self._description,
			"publishedAt":   None if self._publishedAt is None else self._publishedAt.isoformat(),
			"url":           str(self._url),
			"isDraft":       False,
			"isPrerelease":  self._isPrerelease,
			"isLatest":      self._isLatest,
			"tagCommit":     tagCommit,
			"releaseAssets": {"nodes": [asset.ToJSON() for asset in self._assets.values()]}
		}


@export
class Tag(CommitReference):
	"""
	A tag of a repository and the commit it points to.

	A tag exists without a release - a repository may tag every version and publish a release for a few of them.
	"""

	_committedAt: Nullable[datetime]  #: Time of the commit the tag points to.
	_isAnnotated: bool                #: True, if the tag is a tag object of its own.

	def __init__(
		self,
		tagName:     str,
		commitSHA:   Nullable[str]        = None,
		commitURL:   Nullable[URL]        = None,
		committedAt: Nullable[datetime]   = None,
		isAnnotated: bool                 = False,
		*,
		parent:      Nullable[Repository] = None
	) -> None:
		"""
		Initializes a tag.

		:param tagName:     Name of the tag.
		:param commitSHA:   Optional, commit the tag points to. Default: ``None``.
		:param commitURL:   Optional, URL of that commit. Default: ``None``.
		:param committedAt: Optional, time of that commit, with a time zone. Default: ``None``.
		:param isAnnotated: Optional, ``True``, if the tag is a tag object of its own. Default: ``False``.
		:param parent:      Optional, reference to the repository the tag belongs to. Default: ``None``.
		:raises ValueError: If parameter 'tagName' is ``None``.
		:raises TypeError:  If parameter 'tagName' or 'commitSHA' is not of type :class:`str`.
		:raises ValueError: If parameter 'tagName' or 'commitSHA' is empty.
		:raises TypeError:  If parameter 'commitURL' is not of type :class:`~pyTooling.GenericPath.URL.URL`.
		:raises TypeError:  If parameter 'committedAt' is not of type :class:`~datetime.datetime`.
		:raises ValueError: If parameter 'committedAt' has no time zone.
		:raises ValueError: If parameter 'isAnnotated' is ``None``.
		:raises TypeError:  If parameter 'isAnnotated' is not of type :class:`bool`.
		:raises TypeError:  If parameter 'parent' is not of type :class:`Repository`.
		:raises ValueError: If parameter 'parent' has a tag of the same name.
		"""
		super().__init__(tagName, commitSHA, commitURL)

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

		self._committedAt = committedAt
		self._isAnnotated = isAnnotated

		if parent is None:
			pass
		elif not isinstance(parent, Repository):
			ex = TypeError("Parameter 'parent' is not of type 'Repository'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(parent)}'.")
			raise ex
		elif tagName in parent._tags:
			raise ValueError(f"Repository '{parent}' has a tag '{tagName}' already.")
		else:
			self._parent = parent
			parent._tags[tagName] = self

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

		return self._parent._releases.get(self._tagName, None)

	@readonly
	def HasRelease(self) -> bool:
		"""
		Read-only property to return whether a release is published at the tag.

		:returns: ``True``, if the repository the tag belongs to has a release of it.
		"""
		return self._parent is not None and self._tagName in self._parent._releases

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

		return {"name": self._tagName, "target": target}


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
		:raises TypeError:  If an element of parameter 'releases' is not of type :class:`Release`.
		:raises ValueError: If two elements of parameter 'releases' have the same tag.
		:raises ValueError: If an element of parameter 'releases' belongs to a repository already.
		:raises TypeError:  If an element of parameter 'tags' is not of type :class:`Tag`.
		:raises ValueError: If two elements of parameter 'tags' have the same name.
		:raises ValueError: If an element of parameter 'tags' belongs to a repository already.
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
				elif release._parent is not None:
					raise ValueError(f"Release '{release._tagName}' belongs to repository '{release._parent}' already.")
				elif release._tagName in self._releases:
					raise ValueError(f"Repository '{self}' has a release of tag '{release._tagName}' already.")

				release._parent = self
				self._releases[release._tagName] = release

		if tags is not None:
			for tag in tags:
				if not isinstance(tag, Tag):
					ex = TypeError("Element of parameter 'tags' is not of type 'Tag'.")
					ex.add_note(f"Got type '{getFullyQualifiedName(tag)}'.")
					raise ex
				elif tag._parent is not None:
					raise ValueError(f"Tag '{tag._tagName}' belongs to repository '{tag._parent}' already.")
				elif tag._tagName in self._tags:
					raise ValueError(f"Repository '{self}' has a tag '{tag._tagName}' already.")

				tag._parent = self
				self._tags[tag._tagName] = tag

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
		Read-only property to return the release GitHub marks as the latest (:attr:`Release.IsLatest`).

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
		:class:`~pyTooling.GitHub.ReleaseReader.ReleaseReader` queries them, each connection with all its nodes. Draft
		releases are skipped: a draft is unpublished and may change, so it is no part of a repository's releases.

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
			if not isinstance(release, dict) or release.get("isDraft", None) is not True
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
