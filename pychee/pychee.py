#!/usr/bin/env python
# coding=utf-8
"""
# pychee: Client for Lychee, written in Python.

For additional information, visit: https://github.com/LycheeOrg/Lychee.
"""
from posixpath import join
from typing import List
from urllib.parse import unquote

from requests import Session

__version__ = '0.2.2'

class LycheeForbidden(Exception):
    """Raised when the Lychee request is unauthorized."""

class LycheeNotFound(Exception):
    """Raised when the requested resource was not found."""

class LycheeError(Exception):
    """Raised for general Lychee errors."""

#FIXME add error code handling
#FIXME adjust to API sending JSON because we changed Accept
#FIXME fix type hints...
class LycheeAPISession(Session):
    """
    Lychee API Session Handler.

    Wrapper around Session to set base API URL and throw exception if request
    needs auth and user is not logged in.
    """

    FORBID_MESSAGES = [
        '"Warning: Album private!"',
        '"Error: validation failed"'
    ]

    NOT_FOUND_MESSAGES = [
        '"Error: no pictures found!"'
    ]

    # CSRF-related field names
    _CSRF_HEADER = "X-XSRF-TOKEN"
    _CSRF_COOKIE = "XSRF-TOKEN"

    BASE_API_FRAGMENT = "api"

    def __init__(self, prefix_url: str, *args, **kwargs):
        """Initialize the `requests.session`."""
        super().__init__(*args, **kwargs)
        self._prefix_url = prefix_url
        # Initial CSRF
        super().request('GET', self._prefix_url)
        self._set_csrf_header()
        # Lychee now explicitly requires client to accept JSON,
        # else throws exception
        self.headers['Accept'] = 'application/json, text/javascript, */*; q=0.01'

    def request(self, method, url, *args, **kwargs):
        """Make an HTTP request with the configured session."""
        url = join(self._prefix_url, self.BASE_API_FRAGMENT, url)
        response = super().request(method, url, *args, **kwargs)
        self._set_csrf_header()
        # Update CSRF header if changed
        if response.text in self.FORBID_MESSAGES:
            raise LycheeForbidden(response.text)
        if response.text in self.NOT_FOUND_MESSAGES:
            raise LycheeNotFound(response.text)
        if response.text == 'false' or response.text is None:
            raise LycheeError('Could be unauthorized, wrong args, who knows?')
        return response

    def _set_csrf_header(self) -> None:
        """
        Set CSRF header from cookie for the whole session.

        CSRF generally prevents an attacker from forging a request
        sent from another website, e.g. in a JS script, by forcing
        requests to contain a specific value which has been set
        as a cookie in a previous GET request.

        Thus, a previous GET request is needed so this method works.
        """
        csrf_token = self.cookies.get(self._CSRF_COOKIE)
        if csrf_token is not None:
            if csrf_token != self.headers.get(self._CSRF_HEADER):
                self.headers[self._CSRF_HEADER] = unquote(
                    csrf_token
                ).replace('=', '')

class LycheeClient:
    """
    Lychee API Client.

    The primary [Lychee API](https://lycheeorg.github.io/docs/api.html) client
    to interact with the specified Lychee server.
    """

    def __init__(self, url: str):
        """Initialize a new Lychee session for given URL."""
        self._session = LycheeAPISession(url)
        self._session.post('Session::init', json={})

    def login(self, username: str, password: str) -> None:
        """Log in to Lychee server."""
        auth = {'username': username, 'password': password}
        # Session takes care of setting cookies
        login_response = self._session.post('Session::login', json=auth)

    def logout(self):
        """Log out from Lychee server."""
        self._session.post('Session::logout', json={})
        self._session.cookies.clear()

    def get_albums(self) -> dict:
        """
        Get List of Available Albums in Lychee.

        Returns an array of albums or false on failure.
        """
        return self._session.post('Albums::get', json={}).json()

    def get_albums_tree(self):
        """
        Get List of Album Trees in Lychee.

        Returns a list of albums dictionaries or an informative message on
        failure.
        """
        return self._session.post('Albums::tree', json={}).json()

    def get_albums_position_data(self) -> dict:
        """
        Get List of Available Album Data.

        Returns the album with only map related data.
        """
        return self._session.post('Albums::getPositionData', json={}).json()

    def get_album(self, album_id: str) -> dict:
        """
        Get a Specific Album's Information.

        Provided an albumID, returns the album.
        """
        data = {'albumID': album_id}
        return self._session.post('Album::get', json=data).json()

    def get_public_album(self, album_id: str, password: str = 'rand'):
        """
        Get Public Album Information.

        Provided the albumID and passwords, return whether the album can be
        accessed or not. The API won't work if password if empty, even if no
        password.
        """
        data = {'albumID': album_id, 'password': password}
        self._session.post('Album::getPublic', json=data)

    def add_album(self, title: str, parent_id: str = None) -> str:
        """
        Add a new Album with optional parent.

        API won't work with empty parent_id, use 0 as in webapp for no parent.

        Return the ID of the new image.
        """
        data = {'title': title, 'parent_id': parent_id}
        return self._session.post('Album::add', json=data).json()

    def set_albums_title(self, album_ids: List[str], title: str):
        """Change the title of the albums."""
        data = {'albumIDs': ','.join(album_ids), 'title': title}
        self._session.post('Album::setTitle', json=data)

    def set_album_description(self, album_id: str, description: str):
        """Change the description of the album."""
        data = {'albumID': album_id, 'description': description}
        self._session.post('Album::setDescription', json=data)

    def set_album_public(
        self,
        album_id: str,
        public: int,
        visible: int,
        nsfw: int,
        downloadable: int,
        share_button_visible: int,
        full_photo: int,
        password: str = ""
    ):
        """
        Change the sharing properties of the album.

        Contrary to getPublic API call, password can be empty (obv).
        """
        data = {
            'albumID': album_id,
            'public': public,
            'visible': visible,
            'nsfw': nsfw,
            'downloadable': downloadable,
            'share_button_visible': share_button_visible,
            'full_photo': full_photo,
            'password': password
        }
        self._session.post('Album::setPublic', json=data)

    def delete_album(self, album_id: List[str]):
        """Delete the albums and all pictures in the album."""
        data = {'albumIDs': album_id}
        self._session.post('Album::delete', json=data)

    def merge_albums(self, dest_id: str, source_ids: List[str]):
        """
        Merge albums into one.

        Seems that if destination album is one of the sources,
        it will be deleted. Don't do this.
        """
        data = {'albumIDs': dest_id + ',' + ','.join(source_ids)}
        self._session.post('Album::merge', json=data)

    def move_albums(self, dest_id: str, source_ids: List[str]):
        """Move albums into another one, which becomes their parent."""
        data = {'albumIDs': dest_id + ',' + ','.join(source_ids)}
        self._session.post('Album::move', json=data)

    def set_album_license(self, album_id: str, license: str):
        """
        Set the license of an album.

        See https://github.com/LycheeOrg/Lychee/blob/master/app/Assets/Helpers.php
        for authorized licenses (search get_all_licenses())

        Returns false if license name is unrecognized.
        """
        data = {'albumID': album_id, 'license': license}
        self._session.post('Album::setLicense', json=data)

    def get_albums_archive(self, album_ids: List[str]) -> bytes:
        """
        Get a ZIP file of the pictures of the albums and their subalbums.

        Archive is returned as bytes, you can open a file
        with wb mode and write a file.
        """
        data = {'albumIDs': ','.join(album_ids)}
        # For large archives, maybe we would use
        # stream=True and iterate over chunks of answer.
        return self._session.get('Album::getArchive', params=data).content

    def get_frame_settings(self) -> dict:
        """
        Get frame mode settings.

        For now, the only setting returns the refresh time, in milliseconds.
        """
        return self._session.post('Frame::getSettings', json={}).json()

    def get_photo(self, photo_id) -> dict:
        """Get information about a photo."""
        data = {'photoID': photo_id}
        return self._session.post('Photo::get', json=data).json()

    def get_random_photo(self) -> bytes:
        """Get a random photo with current auth."""
        return self._session.post('Photo::getRandom', json={}).content

    def set_photos_title(self, photo_ids: List[str], title: str):
        """Set the title of one or multiple photos."""
        data = {'photoIDs': ','.join(photo_ids), 'title': title}
        self._session.post('Photo::setTitle', json=data)

    def set_photo_description(self, photo_id: str, description: str):
        """Set the description of one or multiple photos."""
        data = {'photoID': photo_id, 'description': description}
        self._session.post('Photo::setDescription', json=data)

    def set_photos_star(self, photo_ids: List[str]):
        """
        Toggle the favorite status of one or multiple photos.

        A starred photo will be unstarred, and vice versa.
        """
        data = {'photoIDs': ','.join(photo_ids)}
        self._session.post('Photo::setStar', json=data)

    def set_photo_public(self, photo_id: str):
        """
        Toggle the public status of a photo.

        A public photo will be unstarred, and vice versa.
        """
        data = {'photoID': photo_id}
        self._session.post('Photo::setPublic', json=data)

    def set_photos_album(self, photo_ids: List[str], album_id: str):
        """Put one or multiple photos into an album."""
        data = {'photoIDs': ','.join(photo_ids), 'albumID': album_id}
        self._session.post('Photo::setAlbum', json=data)

    def set_photos_tags(self, photo_ids: List[str], tags: List[str]):
        """Set tags for one or multiple photos."""
        data = {'photoIDs': ','.join(photo_ids), 'tags': ','.join(tags)}
        self._session.post('Photo::setTags', json=data)

    def add_photo(self, photo: bytes, photo_name: str, album_id: str) -> str:
        """
        Upload a photo into an album.

        photo should be open('/your/photo', 'rb').read().

        Return the ID of the uploaded image.
        """
        data = {'albumID': album_id}
        # Lychee expects a multipart/form-data with a field called name and being `file`,
        # which contradicts with API doc for now
        # See syntax there : https://stackoverflow.com/a/12385661
        files = {'file': (photo_name, photo)}
        return self._session.post('Photo::add', data=data, files=files).json()

    def delete_photo(self, photo_ids: List[str]):
        """Delete one or multiple photos."""
        data = {'photoIDs': ','.join(photo_ids)}
        self._session.post('Photo::delete', json=data)

    def duplicate_photos(self, photo_ids: List[str], album_id: str):
        """Duplicate one or multiple photos into an album."""
        data = {'photoIDs': ','.join(photo_ids), 'albumID': album_id}
        self._session.post('Photo::duplicate', json=data)

    def set_photo_license(self, photo_id: str, license: str):
        """
        Set the license of a photo.

        See https://github.com/LycheeOrg/Lychee/blob/master/app/Assets/Helpers.php
        for authorized licenses (search get_all_licenses())

        Returns false if license name is unrecognized.
        """
        data = {'photoID': photo_id, 'license': license}
        self._session.post('Photo::setLicense', json=data)

    def get_photos_archive(self, photo_ids: List[str], kind: str) -> bytes:
        """
        Get a photo or an archive of photos.

        Kind is one of the following : FULL, LIVEPHOTOVIDEO, MEDIUM2X, MEDIUM, SMALL2X, SMALL, THUMB2X, THUMB.

        If len(photo_ids) == 1, returns an image. Otherwise returns a ZIP archive.

        Content is returned as bytes, you can open a file
        with wb mode and write a file.
        """
        data = {'photoIDs': ','.join(photo_ids), 'kind': kind}
        return self._session.get('Photo::getArchive', params=data).content

    def clear_photos_symlink(self):
        """
        Remove all photo's symlinks, if activated.

        Symlinks are disabled by default and allow to create expirable links to photos, preventing to guess the URL of the full sized photo.

        See [the documentation](https://lycheeorg.github.io/docs/settings.html#symbolic-link).
        """
        self._session.get('Photo::clearSymLink')

    def shared_albums(self) -> dict:
        """Get list of shared album."""
        return self._session.post('Sharing::List', json={}).json()

    def shared_users(self, album_ids: List[str]) -> dict:
        """Get users with whom one or several albums are shared."""
        data = {'albumIDs': ','.join(album_ids)}
        return self._session.post('Sharing::ListUser', json=data).json()

    def share_with_users(self, user_ids: List[str], album_ids: List[str]):
        """Share given albums with given users."""
        data = {
            'UserIDs': ','.join(user_ids),
            'albumIDs': ','.join(album_ids)}
        self._session.post('Sharing::Add', json=data)

    def delete_shares(self, share_ids: List[str]):
        """
        Delete given shares.

        Share IDs can be found in the `id` field of
        the `shared` array when calling shared_albums().
        """
        data = {'ShareIDs': ','.join(share_ids)}
        return self._session.post('Sharing::Delete', json=data).json()

    def change_login(self,
                     old_username: str,
                     old_password: str,
                     new_username: str = '',
                     new_password: str = ''):
        """
        Change username or password.

        If new_username of new_password is blank, it will stay the same.
        """
        if new_username == '':
            new_username = old_username
        if new_password == '':
            new_password = old_password

        data = {
            'username': new_username,
            'password': new_password,
            'oldUsername': old_username,
            'oldPassword': old_password
        }
        self._session.post('Settings::setLogin', json=data)

    def import_photo_from_url(self, url: str, album_id: str):
        """Import a photo from URL into an album."""
        data = {'url': url, 'albumID': album_id}
        self._session.post('Import::url', json=data)
