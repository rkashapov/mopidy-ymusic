import logging
from pathlib import Path

from mopidy import config, ext

from .backend import YMusicBackend


__version__ = '0.0.1'

logger = logging.getLogger(__name__)


class Extension(ext.Extension):
    dist_name: str = 'Mopidy-YMusic'
    ext_name: str = 'ymusic'
    version: str = __version__

    def get_default_config(self) -> str:
        return config.read(Path(__file__).parent / 'ext.conf')

    def get_config_schema(self):
        schema = super().get_config_schema()
        schema['token'] = config.String()
        schema['bitrate'] = config.Integer()
        return schema

    def setup(self, registry):
        registry.add('backend', YMusicBackend)
