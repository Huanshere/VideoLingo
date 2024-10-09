MIRRORS = {
    "阿里云": "http://mirrors.aliyun.com/pypi/simple",
    "清华大学": "https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple",
    "华为云": "https://repo.huaweicloud.com/repository/pypi/simple",
    "腾讯云": "https://mirrors.cloud.tencent.com/pypi/simple",
    "上海交通大学": "https://mirror.sjtu.edu.cn/pypi/web/simple",
    "网易": "https://mirrors.163.com/pypi/simple",
    "PyPI官方": "https://pypi.org/simple"
}

MESSAGES = {
    "checking_speeds": "检查镜像源速度...",
    "using_cached": "使用缓存的测试结果",
    "starting_new_test": "开始新的镜像源速度测试",
    "using_threads": "使用 {} 个线程进行测试",
    "testing_mirrors": "测试镜像源...",
    "results_title": "镜像源速度测试结果",
    "mirror_column": "镜像源",
    "response_time_column": "响应时间 (ms)",
    "fastest_mirror": "最快的镜像源是: {} ({})",
    "response_time": "响应时间: {:.2f} ms",
    "current_pip_source": "当前的pip源是: {}",
    "switch_success": "已成功切换到 {} 镜像源。",
    "switch_fail": "切换失败。当前pip源与预期不符。",
    "expected_source": "预期的pip源: {}",
    "manual_check": "请手动检查配置或尝试以管理员权限运行此脚本。",
    "switch_fail_permissions": "切换镜像源失败，将继续使用当前源。",
    "check_permissions": "请检查是否有足够的权限来修改pip配置。",
    "all_unreachable": "所有镜像源都无法连接，请检查网络连接。",
    "fast_mirror_found": "找到响应时间小于500ms的镜像，跳过测试。",
    "no_fast_mirror": "未找到响应时间小于500ms的镜像，已测试所有镜像。"    
    "testing_official_mirror": "测试PyPI官方源速度...请耐心等待",
    "official_mirror_fast": "PyPI官方镜像速度很快 ({:.2f} ms)。使用官方镜像。",
    "official_mirror_acceptable": "PyPI官方镜像速度可以接受 ({:.2f} ms)。您可以继续使用它。",
    "official_mirror_slow": "PyPI官方镜像速度较慢 ({:.2f} ms)。测试其他镜像..."
}
