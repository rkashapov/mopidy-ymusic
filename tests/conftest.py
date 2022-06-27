import pytest

from mopidy_ymusic.backend import YMusicBackend


@pytest.fixture
def config():
    return {'ymusic': {'token': '', 'bitrate': 128}}


@pytest.fixture
def backend(config):
    return YMusicBackend(config, None)
