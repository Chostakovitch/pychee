#!/usr/bin/env python
# coding=utf-8
"""
# pychee: Client for Lychee, written in Python.

For additonal information, visit: [Lychee](https://github.com/LycheeOrg/Lychee).
"""
from posixpath import join
from urllib.parse import unquote
from typing import List
from requests import Session

__version__ = 0.0

class LycheeForbidden(Exception):
    """Raised when the Lychee request returns 401: Forbidden."""

    pass

class LycheeError(Exception):
    """Raised for general Lychee errors."""

    pass

class LycheeAPISession(Session):
    """
    Lychee API Session Handler.

    Wrapper around Session to set base API URL and throw exception if request
    needs auth and user is not logged in.
    """

    UNAUTH_MESSAGES = [
        '"Warning: Album private!"',
    ]

    def __init__(self, prefix_url: str, *args, **kwargs):
        """Initialize the `requests.session`."""
        super().__init__(*args, **kwargs)
        self._prefix_url = prefix_url

    def request(self, method, url, *args, **kwargs):
        """Make an HTTP request with the configured session."""
        url = join(self._prefix_url, 'api', url)
        response = super().request(method, url, *args, **kwargs)
        if response.text in self.UNAUTH_MESSAGES:
            raise LycheeForbidden(response.text)
        if response.text == 'false' or response.text is None:
            raise LycheeError('Could be unauthorized, wrong args, who knows?')
        return response

class LycheeClient:
    """
    Lychee API Client.

    The primary [Lychee API](https://lycheeorg.github.io/docs/api.html) client
    to interact with the specified Lychee server.
    """

    def __init__(self, url: str):
        """Initialize a new Lychee session for given URL with CSRF token."""
        self._session = LycheeAPISession(url)
        init_response = self._session.post('Session::init')
        csrf_token = unquote(init_response.cookies['XSRF-TOKEN'])
        self._session.headers.update({'X-XSRF-TOKEN': csrf_token})

    def login(self, username: str, password: str) -> bool:
        """Log in to Lychee server."""
        auth = {'username': username, 'password': password}
        # Session takes care of setting cookies
        login_response = self._session.post('Session::login', data=auth)
        return 'true' in login_response.text

    def logout(self):
        """Log out from Lychee server."""
        self._session.post('Session::logout')
        self._session.cookies.clear()

    def get_albums(self) -> dict:
        """
        Get List of Available Albums in Lychee.

        Returns an array of albums or false on failure.
        """
        return self._session.post('Albums::get').json()

    def get_albums_position_data(self) -> dict:
        """
        Get List of Available Album Data.

        Returns the album with only map related data.
        """
        return self._session.post('Albums::getPositionData').json()

    def get_album(self, album_id: str) -> dict:
        """
        Get a Specific Album's Information.

        Provided an albumID, returns the album.
        """
        data = {'albumID': album_id}
        return self._session.post('Album::get', data=data).json()

    def get_public_album(self, album_id: str, password: str = 'rand') -> bool:
        """
        Get Public Album Information.

        Provided the albumID and passwords, return whether the album can be
        accessed or not. The API won't work if password if empty, even if no
        password.
        """
        data = {'albumID': album_id, 'password': password}
        return 'true' in self._session.post('Album::getPublic', data=data).text

    def add_album(self, title: str, parent_id: str = "0") -> bool:
        """
        Add a new Album with option parent.

        API won't work with empty parent_id, use 0 as in webapp for no parent.
        """
        data = {'title': title, 'parent_id': parent_id}
        return 'true' in self._session.post('Album::add', data=data).text

    def set_albums_title(self, album_ids: List[str], title: str) -> bool:
        """Change the title of the albums."""
        data = {'albumIDs': ','.join(album_ids), 'title': title}
        return 'true' in self._session.post('Album::setTitle', data=data).text

    def set_album_description(self, album_id: str, description: str) -> bool:
        """Change the description of the album."""
        data = {'albumID': album_id, 'description': description}
        return 'true' in self._session.post('Album::setDescription', data=data).text

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
    ) -> bool:
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
        return 'true' in self._session.post('Album::setPublic', data=data).text

    def delete_album(self, album_id: List[str]) -> bool:
        """Delete the albums and all pictures in the album."""
        data = {'albumIDs': album_id}
        return 'true' in self._session.post('Album::delete', data=data).text

    def merge_albums(self, dest_id: str, source_ids: List[str]) -> bool:
        """
        Merge albums into one.

        Seems that if destination album is one of the sources,
        it will be deleted. Don't do this.
        """
        data = {'albumIDs': dest_id + ',' + ','.join(source_ids)}
        return 'true' in self._session.post('Album::merge', data=data).text

    def move_albums(self, dest_id: str, source_ids: List[str]) -> bool:
        """Move albums into another one, which becomes their parent."""
        data = {'albumIDs': dest_id + ',' + ','.join(source_ids)}
        return 'true' in self._session.post('Album::move', data=data).text

    def set_album_licence(self, album_id: str, license: str) -> bool:
        """
        Set the license of the Album.

        See https://github.com/LycheeOrg/Lychee/blob/master/app/Assets/Helpers.php
        for authorized licenses (search get_all_licenses())

        Returns false if license name is unrecognized.
        """
        data = {'albumID': album_id, 'license': license}
        return 'true' in self._session.post('Album::setLicense', data=data).text

    def get_albums_archive(self, album_ids: List[str]) -> bytes:
        """
        Get a ZIP file of the pictures of the albums and their subalbums.

        Archive is returned as bytes, you can open a file
        with wb mode and write to it.
        """
        data = {'albumIDs': ','.join(album_ids)}
        # For large archives, maybe we would use
        # stream=True and iterate over chunks of answer.
        return self._session.get('Album::getArchive', params=data).content

    """
    Get frame mode settings.

    For now, the only setting is the refresh time, in milliseconds.
    """
    def get_frame_settings(self) -> dict:
        return self._session.post('Frame::getSettings').json()
