"""Check that metadata preview never blocks a YouTube download."""
import ast
from contextlib import nullcontext
from pathlib import Path

import pytest


@pytest.mark.parametrize('preview_clicked, metadata', [
    (False, None),
    (True, None),
    (False, {'title': 'Example'}),
])
def test_download_with_optional_preview(preview_clicked, metadata):
    source = Path(__file__).resolve().parents[1] / 'core/st_utils/download_video_section.py'
    tree = ast.parse(source.read_text(encoding='utf-8'))
    tree.body = [node for node in tree.body if isinstance(node, ast.FunctionDef)
                 and node.name == 'download_video_section']
    downloads = []
    rendered = []

    class Rerun(Exception):
        pass

    class Streamlit:
        session_state = {'_youtube_metadata_preview': {
            'url': 'https://video.example.com/item', 'metadata': metadata,
        }} if metadata else {}
        header = error = warning = lambda *args, **kwargs: None
        container = expander = spinner = lambda *args, **kwargs: nullcontext()
        columns = lambda *args: (nullcontext(), nullcontext())

        def text_input(self, label, **kwargs):
            return 'https://video.example.com/item' if 'YouTube' in label else ''

        def selectbox(self, label, options, index):
            return options[index]

        def button(self, label, key, **kwargs):
            return key == 'download_button' or (preview_clicked and key == 'get_video_info_button')

        def rerun(self):
            raise Rerun

    def no_media():
        raise ValueError('No media file found')

    def failed_preview(url):
        raise RuntimeError('Preview unavailable')

    namespace = {
        'st': Streamlit(), 't': lambda text: text, 'find_media_file': no_media,
        'load_key': lambda key: {'ytb_resolution': '1080', 'youtube.cookies_path': ''}.get(key),
        'get_video_info_ytdlp': failed_preview,
        'download_video_ytdlp': lambda url, **kwargs: downloads.append((url, kwargs)),
        '_render_youtube_metadata': rendered.append,
    }
    exec(compile(tree, str(source), 'exec'), namespace)

    with pytest.raises(Rerun):
        namespace['download_video_section']()
    assert downloads == [('https://video.example.com/item', {'resolution': '1080', 'metadata': metadata})]
    assert rendered == ([metadata] if metadata else [])
