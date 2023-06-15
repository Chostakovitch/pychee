# pychee

Client for [Lychee](https://github.com/LycheeOrg/Lychee), written in Python.

Lychee is a photo management system I've been using for years. I had the idea to
make a « Lychee filesystem » with
[FUSE](https://fr.wikipedia.org/wiki/Filesystem_in_Userspace), so I needed an
API client.

## Installation

```bash
python3 -m pip install pychee
```

## Notes

My reference is [this documentation](https://lycheeorg.github.io/docs/api.html).
The API is partially implemented and focused on photo management, _i.e._ only
`Albums`, `Photo`, `Frame`, `Sharing` and `Settings::setLogin`. Users can do
whatever they want with their albums and photos and change their password.

Disclaimer : I usually suck at coding, so use with caution and at your own risks.
Tested with Lychee v4.7.0. The code probably won't be retrocompatible and should
just work with the latest version.

## TODO

Add tests

## Example usage

> ⚠️ `pychee` returns exactly what the API sends back, just parsing it to `dict`
if necessary. As sample answers are not documented in the API and because answers
tend to change over time, you should inspect requests in browser if your client
code does not works anymore.

A sample of common API calls :

```python
#!/usr/bin/env python
# coding=utf-8
from pychee import pychee

# Initialize instance
client = pychee.LycheeClient('https://pic.chosto.me')

# Login
client.login('login', 'password')

# Create a new album
album_name = 'test_name'
album_id = client.add_album(album_name)['id']

# Add a photo in the created album
path_to_your_photo = '/your/path/photo.jpg'
with open(path_to_your_photo, 'rb') as f:
    photo_id = client.add_photo(f, 'photo.jpg', album_id)['id']

# Set uploaded photo public
client.set_photo_public(photo_id)

# Set licence of uploaded photo
client.set_photo_license(photo_id, 'CC0')

# Download an archive of the created album
output_path = '/tmp/photos.zip'
with(open(output_path, 'wb')) as f:
     f.write(client.get_albums_archive([album_id]))

# Logout
client.logout()
```

## Documentation

Documentation is automatically published on GitHub:
https://chostakovitch.github.io/pychee/index.html
