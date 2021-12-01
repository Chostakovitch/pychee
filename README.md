# pychee

Client for [Lychee](https://github.com/LycheeOrg/Lychee), written in Python.

Lychee is a photo management system I've been using for years. I had the idea
to make a « Lychee filesystem » with [FUSE](https://fr.wikipedia.org/wiki/Filesystem_in_Userspace),
so I needed an API client.

My reference is [this documentation](https://lycheeorg.github.io/docs/api.html).
The API is partially implemented and focused on photo management, _i.e._ `Albums`, `Photo`, `Frame`, `Sharing` and `Settings::setLogin` are implemented, so that a user can do whatever he wants with its albums and photos and change its password. For my own usage, changing admin settings or layout from Python is not useful.

Disclaimer : I usually suck at coding, so use with caution and at your own risks. Tested with Lychee
v4.3.4. The code won't be retrocompatible and will just work with the last version.

Documentation is published there : https://chostakovitch.github.io/pychee/index.html
