# https://help.aliyun.com/zh/tingwu/voice-transcription?spm=5176.28158887.0.0.6963k4J6k4J6dp

import os
import json
import datetime
from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest
from aliyunsdkcore.auth.credentials import AccessKeyCredential

def create_common_request(domain, version, protocolType, method, uri):
    request = CommonRequest()
    request.set_accept_format('json')
    request.set_domain(domain)
    request.set_version(version)
    request.set_protocol_type(protocolType)
    request.set_method(method)
    request.set_uri_pattern(uri)
    request.add_header('Content-Type', 'application/json')
    return request

def init_parameters():
    root = dict()
    root['AppKey'] = '输入您在听悟管控台创建的Appkey'

    # 基本请求参数
    input = dict()
    input['SourceLanguage'] = 'cn'
    input['TaskKey'] = 'task' + datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    input['FileUrl'] = '输入待测试的音频url链接'
    root['Input'] = input

    # AI相关参数，按需设置即可
    parameters = dict()

    # 语音识别控制相关
    transcription = dict()
    # 角色分离
    transcription['DiarizationEnabled'] = True
    diarization = dict()
    diarization['SpeakerCount'] = 2
    transcription['Diarization'] = diarization
    parameters['Transcription'] = transcription

    root['Parameters'] = parameters
    return root

body = init_parameters()
print(body)

# TODO  请通过环境变量设置您的 AccessKeyId 和 AccessKeySecret
credentials = AccessKeyCredential(os.environ['ALIBABA_CLOUD_ACCESS_KEY_ID'], os.environ['ALIBABA_CLOUD_ACCESS_KEY_SECRET'])
client = AcsClient(region_id='cn-beijing', credential=credentials)

request = create_common_request('tingwu.cn-beijing.aliyuncs.com', '2023-09-30', 'https', 'PUT', '/openapi/tingwu/v2/tasks')
request.add_query_param('type', 'offline')

request.set_content(json.dumps(body).encode('utf-8'))
response = client.do_action_with_exception(request)
print("response: \n" + json.dumps(json.loads(response), indent=4, ensure_ascii=False))