import socket
# 便于小白理解
def get_localhost_ipv4_address(host = "127.0.0.1"):

    def get_internal_ip():
        """获取内部IP地址"""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # 这不会发送真正的数据包
            s.connect(('10.253.156.219', 1))
            IP = s.getsockname()[0]
        except Exception:
            IP = '127.0.0.1'
        finally:
            s.close()
        return IP

    if host == "0.0.0.0":
        display_hostname = get_internal_ip()
        return display_hostname
    else:
        return host
            
def get_gradio_frp(server_name, server_port, share_token) -> str:
    from urllib.parse import urlparse, urlunparse
    from gradio import networking
    share_url = networking.setup_tunnel(
        local_host=server_name,
        local_port=server_port,
        share_token=share_token,
        share_server_address=None,
    )
    parsed_url = urlparse(share_url)
    share_server_protocol = "https" 
    share_url = urlunparse(
        (share_server_protocol,) + parsed_url[1:]
    )
    return share_url