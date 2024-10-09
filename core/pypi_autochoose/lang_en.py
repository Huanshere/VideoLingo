MIRRORS = {
    "Alibaba Cloud": "https://mirrors.aliyun.com/pypi/simple",
    "Tsinghua University": "https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple",
    "Huawei Cloud": "https://repo.huaweicloud.com/repository/pypi/simple",
    "Tencent Cloud": "https://mirrors.cloud.tencent.com/pypi/simple",
    "S J T U": "https://mirror.sjtu.edu.cn/pypi/web/simple",
    "163 Cloud": "https://mirrors.163.com/pypi/simple",
    "PyPI Official": "https://pypi.org/simple"
}

MESSAGES = {
    "checking_speeds": "Checking mirror speeds...",
    "using_cached": "Using cached test results",
    "starting_new_test": "Starting new mirror speed test",
    "using_threads": "Using {} threads for testing",
    "testing_mirrors": "Testing mirrors...",
    "results_title": "Mirror Speed Test Results",
    "mirror_column": "Mirror",
    "response_time_column": "Response Time (ms)",
    "fastest_mirror": "Fastest mirror: {} ({})",
    "response_time": "Response time: {:.2f} ms",
    "current_pip_source": "Current pip source: {}",
    "switch_success": "Successfully switched to {} mirror.",
    "switch_fail": "Switch failed. Current pip source doesn't match the expected one.",
    "expected_source": "Expected pip source: {}",
    "manual_check": "Please check the configuration manually or try running this script with administrator privileges.",
    "switch_fail_permissions": "Failed to switch mirror, will continue using the current source.",
    "check_permissions": "Please check if you have sufficient permissions to modify pip configuration.",
    "all_unreachable": "All mirrors are unreachable. Please check your network connection.",
    "fast_mirror_found": "Find the image with a response time of less than 500 ms and skip the test.",
    "no_fast_mirror": "No images with a response time of less than 500 ms were found, and all images have been tested.",
    "testing_official_mirror": "Testing PyPI official mirror...",
    "official_mirror_fast": "PyPI official mirror is fast ({:.2f} ms). Using the official mirror.",
    "official_mirror_acceptable": "PyPI official mirror speed is acceptable ({:.2f} ms). You may continue using it.",
    "official_mirror_slow": "PyPI official mirror is slow ({:.2f} ms). Testing other mirrors..."
}
