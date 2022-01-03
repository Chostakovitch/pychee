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

__version__ = '0.1.1'

class LycheeForbidden(Exception):
    """Raised when the Lychee request is unauthorized."""

class LycheeNotFound(Exception):
    """Raised when the requested ressource was not found."""

class LycheeError(Exception):
    """Raised for general Lychee errors."""

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
    def __init__(self, prefix_url: str, *args, **kwargs):
        """Initialize the `requests.session`."""
        super().__init__(*args, **kwargs)
        self._prefix_url = prefix_url

    def request(self, method, url, *args, **kwargs):
        """Make an HTTP request with the configured session."""
        url = join(self._prefix_url, 'api', url)
        response = super().request(method, url, *args, **kwargs)
        if response.text in self.FORBID_MESSAGES:
            raise LycheeForbidden(response.text)
        if response.text in self.NOT_FOUND_MESSAGES:
            raise LycheeNotFound(response.text)
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

    def set_album_license(self, album_id: str, license: str) -> bool:
        """
        Set the license of an album.

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
        return self._session.post('Frame::getSettings').json()

    def get_photo(self, photo_id) -> dict:
        """Get information about a photo."""
        data = {'photoID': photo_id}
        return self._session.post('Photo::get', data=data).json()

    def get_random_photo(self) -> bytes:
        """Get a random photo with current auth."""
        return self._session.post('Photo::getRandom').content

    def set_photos_title(self, photo_ids: List[str], title: str) -> bool:
        """Set the title of one or multiple photos."""
        data = {'photoIDs': ','.join(photo_ids), 'title': title}
        return 'true' in self._session.post('Photo::setTitle', data=data).text

    def set_photo_description(self, photo_id: str, description: str) -> bool:
        """Set the description of one or multiple photos."""
        data = {'photoID': photo_id, 'description': description}
        return 'true' in self._session.post('Photo::setDescription', data=data).text

    def set_photos_star(self, photo_ids: List[str]) -> bool:
        """
        Toggle the favorite status of one or multiple photos.

        A starred photo will be unstarred, and vice versa.
        """
        data = {'photoIDs': ','.join(photo_ids)}
        return 'true' in self._session.post('Photo::setStar', data=data).text

    def set_photo_public(self, photo_id: str) -> bool:
        """
        Toggle the public status of a photo.

        A public photo will be unstarred, and vice versa.
        """
        data = {'photoID': photo_id}
        return 'true' in self._session.post('Photo::setPublic', data=data).text

    def set_photos_album(self, photo_ids: List[str], album_id: str) -> bool:
        """Put one or multiple photos into an album."""
        data = {'photoIDs': ','.join(photo_ids), 'albumID': album_id}
        return 'true' in self._session.post('Photo::setAlbum', data=data).text

    def set_photos_tags(self, photo_ids: List[str], tags: List[str]) -> bool:
        """Set tags for one or multiple photos."""
        data = {'photoIDs': ','.join(photo_ids), 'tags': ','.join(tags)}
        return 'true' in self._session.post('Photo::setTags', data=data).text

    def add_photo(self, photo: bytes, photo_name: str, album_id: str) -> int:
        """
        Upload a photo into an album.

        photo should be open('/your/photo', 'rb').read().

        Return the ID of the uploaded image.
        """
        data = {'albumID': album_id}
        files = {'0': (photo_name, photo)}
        return int(self._session.post('Photo::add', data=data, files=files).text)

    def delete_photo(self, photo_ids: List[str]) -> bool:
        """Delete one or multiple photos."""
        data = {'photoIDs': ','.join(photo_ids)}
        return 'true' in self._session.post('Photo::delete', data=data).text

    def duplicate_photos(self, photo_ids: List[str], album_id: str) -> bool:
        """Duplicate one or multiple photos into an album."""
        data = {'photoIDs': ','.join(photo_ids), 'albumID': album_id}
        return 'true' in self._session.post('Photo::duplicate', data=data).text

    def set_photo_license(self, photo_id: str, license: str) -> bool:
        """
        Set the license of a photo.

        See https://github.com/LycheeOrg/Lychee/blob/master/app/Assets/Helpers.php
        for authorized licenses (search get_all_licenses())

        Returns false if license name is unrecognized.
        """
        data = {'photoID': photo_id, 'license': license}
        return 'true' in self._session.post('Photo::setLicense', data=data).text

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

    def clear_photos_symlink(self) -> bool:
        """
        Remove all photo's symlinks, if activated.

        Symlinks are disabled by default and allow to create expirable links to photos, preventing to guess the URL of the full sized photo.

        See [the documentation](https://lycheeorg.github.io/docs/settings.html#symbolic-link).
        """
        return 'true' in self._session.get('Photo::clearSymLink').text

    def shared_albums(self) -> dict:
        """Get list of shared album."""
        return self._session.post('Sharing::List').json()

    def shared_users(self, album_ids: List[str]) -> dict:
        """Get users with whom one or several albums are shared."""
        data = {'albumIDs': ','.join(album_ids)}
        return self._session.post('Sharing::ListUser', data=data).json()

    def share_with_users(self, user_ids: List[str], album_ids: List[str]) -> bool:
        """Share given albums with given users."""
        data = {
            'UserIDs': ','.join(user_ids),
            'albumIDs': ','.join(album_ids)}
        print(data)
        return 'true' in self._session.post('Sharing::Add', data=data).text

    def delete_shares(self, share_ids: List[str]) -> bool:
        """
        Delete given shares.

        Share IDs can be found in the `id` field of
        the `shared` array when calling shared_albums().
        """
        data = {'ShareIDs': ','.join(share_ids)}
        return self._session.post('Sharing::Delete', data=data).json()

    def change_login(self,
                     old_username: str,
                     old_password: str,
                     new_username: str = '',
                     new_password: str = '') -> bool:
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
        return 'true' in self._session.post('Settings::setLogin', data=data).text

    def import_photo_from_url(self, url: str, album_id: str) -> bool:
        """Import a photo from URL into an album."""
        data = {'url': url, 'albumID': album_id}
        return 'true' in self._session.post('Import::url', data=data).text
