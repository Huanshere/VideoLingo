# Download network configuration

Video downloads use yt-dlp's native proxy support. No proxy application, local
port, JavaScript runtime, or browser impersonation profile is forced.

Set `youtube.proxy` in `config.yaml`:

```yaml
youtube:
  cookies_path: ''
  proxy: null
```

- Missing or `null`: leave yt-dlp's proxy option unset, preserving its existing
  system/environment discovery. With no discovered proxy, downloads connect directly.
- `''`: explicitly connect directly, even if the environment has a proxy.
- A URL such as `http://proxy.example.com:8080` or
  `socks5://proxy.example.com:1080`: use that proxy for yt-dlp downloads.

This setting applies to yt-dlp only, not translation, model downloads, TTS, or the
existing pip update operation preceding a download. It does not alter system or
process environment settings. Credentials in a proxy URL are private configuration:
never include them in commits or shared diagnostic logs.

Verification: `python -m pytest -q tests/test_download_proxy.py`. Tests replace
network downloads and package updates, and check the installed yt-dlp's actual
proxy selection without sending requests. Live site access still depends on the
user's network, cookies and the site's requirements.
