# Mopidy-YMusic

[Mopidy](https://mopidy.com/) extension for playing music from [Yandex Music](https://music.yandex.ru)

## Dependencies

This plugin depends on an excellent [yandex-music-api](https://github.com/MarshalX/yandex-music-api) package.
Many thanks for its author.

## Installation

Install by running

```bash
pip install git+https://github.com/rkashapov/mopidy-ymusic@master 
```

## Configuration

Before starting Mopidy you need to pass your auth token to your Mopody configuration file.
A way you can get the auth token is described here: https://github.com/MarshalX/yandex-music-api/discussions/513.

A sample configuration:

```
[ymusic]
enabled = true
bitrate = 320
token = ****
```
