"""Verify proxy configuration without downloads, installations or services."""
import ast
import os
from pathlib import Path

import pytest
from yt_dlp import YoutubeDL

PROXY_DISCOVERY = YoutubeDL.proxies.func.__globals__['urllib'].request


def options(tmp_path, youtube):
    source = Path(__file__).resolve().parents[1] / 'core/_1_ytdlp.py'
    tree = ast.parse(source.read_text(encoding='utf-8'))
    tree.body = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                 and n.name == 'download_video_ytdlp']
    recorded = {}
    class Download:
        def __init__(self, opts): recorded.update(opts)
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def download(self, urls): assert urls == ['https://video.example.com/item']
    namespace = {
        'os': os, 'load_key': lambda key: youtube if key == 'youtube' else '',
        'update_ytdlp': lambda: Download, 'find_video_files': lambda _: 'synthetic.mp4',
        'write_input_manifest': lambda *a: None,
    }
    exec(compile(tree, str(source), 'exec'), namespace)
    namespace['download_video_ytdlp']('https://video.example.com/item', str(tmp_path))
    return recorded


@pytest.mark.parametrize('config', [{}, {'proxy': None}])
def test_default_preserves_environment_discovery(tmp_path, monkeypatch, config):
    opts = options(tmp_path, config)
    assert 'proxy' not in opts
    monkeypatch.setattr(PROXY_DISCOVERY, 'getproxies', lambda: {'https': 'http://proxy.example.com:8080'})
    with YoutubeDL({**opts, 'quiet': True, 'js_runtimes': {}}, auto_init=False) as ydl:
        assert ydl.proxies['https'] == 'http://proxy.example.com:8080'


def test_default_without_proxy_connects_directly(tmp_path, monkeypatch):
    monkeypatch.setattr(PROXY_DISCOVERY, 'getproxies', lambda: {})
    with YoutubeDL(options(tmp_path, {}), auto_init=False) as ydl:
        assert ydl.proxies == {}


@pytest.mark.parametrize('proxy', ['', 'http://proxy.example.com:8080', 'socks5://proxy.example.com:1080'])
def test_explicit_overrides_environment(tmp_path, monkeypatch, proxy):
    opts = options(tmp_path, {'proxy': proxy})
    monkeypatch.setattr(PROXY_DISCOVERY, 'getproxies', lambda: pytest.fail('Explicit mode must not discover proxies'))
    with YoutubeDL(opts, auto_init=False) as ydl:
        assert ydl.proxies == {'all': proxy or '__noproxy__'}


@pytest.mark.parametrize('proxy', [False, 7897, []])
def test_invalid_type_rejected_before_download(tmp_path, proxy):
    with pytest.raises(ValueError, match='youtube.proxy'):
        options(tmp_path, {'proxy': proxy})
