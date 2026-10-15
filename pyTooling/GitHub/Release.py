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
A release of a GitHub repository and the files attached to it.

A :class:`Release` belongs to a :class:`~pyTooling.GitHub.Repository.Repository`, which holds the releases and tags of
one repository and describes the whole model.

.. hint::

   See :ref:`high-level help <DATA/Release>` for explanations and usage examples.
"""
from __future__                    import annotations

from datetime                      import datetime
from typing                        import TYPE_CHECKING, Iterable, Optional as Nullable, Self
from urllib.parse                  import quote

from pyTooling.Common              import getFullyQualifiedName, StringEnum
from pyTooling.Decorators          import export, readonly
from pyTooling.GenericPath.URL     import URL
from pyTooling.MetaClasses         import ExtendedType
from pyTooling.REST                import JSONObject

from pyTooling.GitHub              import GitHubError, _parseISO8601Timestamp, _parseURL

if TYPE_CHECKING:
	from pyTooling.GitHub.Repository import Repository


# A class with a property named like a class - ``URL`` - can't name that class in an annotation: the class body's
# namespace, where annotations are evaluated, binds the name to the property.
_URL = URL


@export
class SourceArchive(StringEnum):
	"""The formats of the source code archive GitHub offers for a tag."""

	Zip =     "zip"     #: A ZIP file.
	Tarball = "tar.gz"  #: A gzip-compressed TAR file.


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
class ReleaseAsset(metaclass=ExtendedType, slots=True):
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
		else:
			parent._AddAsset(self)

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
class Release(metaclass=ExtendedType, slots=True):
	"""
	A release, published at a tag.

	A draft is no release: it is unpublished and may change, so the model has none.

	The release's commit is the one its **tag** points to - not GitHub's ``target_commitish``, which is usually a
	branch's name. The time is when the release was **published**, not when it was created, which is the commit's time.
	"""

	_parent:       Nullable[Repository]     #: Repository the release belongs to.
	_tagName:      str                      #: Name of the tag the release is published at.
	_url:          _URL                     #: URL of the release page.
	_name:         Nullable[str]            #: Title of the release.
	_description:  str                      #: Release notes as Markdown.
	_publishedAt:  Nullable[datetime]       #: Time the release was published.
	_isPrerelease: bool                     #: True, if the release is a pre-release.
	_isLatest:     bool                     #: True, if the release is the repository's latest release.
	_commitSHA:    Nullable[str]            #: Commit the tag points to.
	_commitURL:    Nullable[_URL]           #: URL of that commit.
	_assets:       dict[str, ReleaseAsset]  #: Files attached to the release, by file name.

	def __init__(
		self,
		tagName:      str,
		url:          _URL,
		name:         Nullable[str]                    = None,
		description:  str                              = "",
		publishedAt:  Nullable[datetime]               = None,
		isPrerelease: bool                             = False,
		isLatest:     bool                             = False,
		commitSHA:    Nullable[str]                    = None,
		commitURL:    Nullable[_URL]                   = None,
		assets:       Nullable[Iterable[ReleaseAsset]] = None,
		*,
		parent:       Nullable[Repository]             = None
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
		:raises TypeError:   If an element of parameter 'assets' is not of type :class:`ReleaseAsset`.
		:raises ValueError:  If two elements of parameter 'assets' have the same name.
		:raises TypeError:   If parameter 'parent' is not of type :class:`Repository`.
		:raises ValueError:  If parameter 'parent' has a release of the same tag.
		"""
		if tagName is None:
			raise ValueError("Parameter 'tagName' is None.")
		elif not isinstance(tagName, str):
			ex = TypeError("Parameter 'tagName' is not of type 'str'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(tagName)}'.")
			raise ex
		elif tagName == "":
			raise ValueError("Parameter 'tagName' is empty.")

		if url is None:
			raise ValueError("Parameter 'url' is None.")

		for parameterName, link in (("url", url), ("commitURL", commitURL)):
			if link is not None and not isinstance(link, URL):
				ex = TypeError(f"Parameter '{parameterName}' is not of type 'URL'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(link)}'.")
				raise ex

		for parameterName, text in (("name", name), ("commitSHA", commitSHA)):
			if text is not None and not isinstance(text, str):
				ex = TypeError(f"Parameter '{parameterName}' is not of type 'str'.")
				ex.add_note(f"Got type '{getFullyQualifiedName(text)}'.")
				raise ex
			elif text == "":
				raise ValueError(f"Parameter '{parameterName}' is empty.")

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

		self._parent =       None
		self._tagName =      tagName
		self._url =          url
		self._name =         name
		self._description =  description
		self._publishedAt =  publishedAt
		self._isPrerelease = isPrerelease
		self._isLatest =     isLatest
		self._commitSHA =    commitSHA
		self._commitURL =    commitURL
		self._assets =       {}

		if assets is not None:
			for asset in assets:
				if not isinstance(asset, ReleaseAsset):
					ex = TypeError("Element of parameter 'assets' is not of type 'ReleaseAsset'.")
					ex.add_note(f"Got type '{getFullyQualifiedName(asset)}'.")
					raise ex

				self._AddAsset(asset)

		if parent is None:
			return

		from pyTooling.GitHub.Repository import Repository

		if not isinstance(parent, Repository):
			ex = TypeError("Parameter 'parent' is not of type 'Repository'.")
			ex.add_note(f"Got type '{getFullyQualifiedName(parent)}'.")
			raise ex
		else:
			parent._AddRelease(self)

	def _AddAsset(self, asset: ReleaseAsset) -> None:
		"""
		Attach an asset to the release.

		:param asset:       The asset.
		:raises ValueError: If the asset is attached to a release already.
		:raises ValueError: If the release has an asset of the same name.
		"""
		if asset._parent is not None:
			raise ValueError(f"Asset '{asset._name}' is attached to release '{asset._parent._tagName}' already.")
		elif asset._name in self._assets:
			raise ValueError(f"Release '{self._tagName}' has an asset '{asset._name}' already.")

		asset._parent = self
		self._assets[asset._name] = asset

	@readonly
	def Parent(self) -> Nullable[Repository]:
		"""
		Read-only property to access the repository the release belongs to (:attr:`_parent`).

		:returns: The repository, or ``None`` if the release belongs to none.
		"""
		return self._parent

	@readonly
	def TagName(self) -> str:
		"""
		Read-only property to access the name of the tag the release is published at (:attr:`_tagName`).

		:returns: The tag's name, unique within the repository.
		"""
		return self._tagName

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
	def CommitSHA(self) -> Nullable[str]:
		"""
		Read-only property to access the commit the release's tag points to (:attr:`_commitSHA`).

		An annotated tag is resolved to the commit it points to.

		:returns: The commit's hash, or ``None`` if the tag doesn't exist.
		"""
		return self._commitSHA

	@readonly
	def CommitURL(self) -> Nullable[_URL]:
		"""
		Read-only property to access the URL of the commit the release's tag points to (:attr:`_commitURL`).

		:returns: The commit's URL on github.com, or ``None`` if the tag doesn't exist yet.
		"""
		return self._commitURL

	@readonly
	def Assets(self) -> dict[str, ReleaseAsset]:
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

	def __str__(self) -> str:
		"""
		Return a string representation of the release.

		:returns: The name of the release's tag.
		"""
		return self._tagName

	@classmethod
	def Parse(cls, release: JSONObject, path: str = "release") -> Self:
		"""
		Read a release and its assets from a ``Release`` object of GitHub's GraphQL API.

		An empty title is no title, and no release notes are empty release notes. A draft is rejected, as it is no
		release - :meth:`Repository.Parse <pyTooling.GitHub.Repository.Repository.Parse>` skips drafts.

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
			ReleaseAsset.Parse(asset, f"{path}.releaseAssets.nodes[{position}]")
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
