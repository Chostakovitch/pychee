# pychee

Client for [Lychee](https://github.com/LycheeOrg/Lychee), written in Python.

Lychee is a photo management system I've been using for years. I had the idea to make a « Lychee filesystem » with [FUSE](https://fr.wikipedia.org/wiki/Filesystem_in_Userspace), so I needed an API client.

## Installation

```bash
python3 -m pip install pychee
```

## Notes

My reference is [this documentation](https://lycheeorg.github.io/docs/api.html).
The API is partially implemented and focused on photo management, _i.e._ only `Albums`, `Photo`, `Frame`, `Sharing` and `Settings::setLogin`. Users can do whatever they want with their albums and photos and change their password.

Disclaimer : I usually suck at coding, so use with caution and at your own risks.
Tested with Lychee v4.3.4. The code probably won't be retrocompatible and should just work with the latest version.

## Documentation

Documentation is automatically published there : https://chostakovitch.github.io/pychee/index.html
