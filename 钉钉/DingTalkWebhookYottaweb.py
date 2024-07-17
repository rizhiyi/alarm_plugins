# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name   :     DingTalkWebhookYottaweb
   Description :     自定义机器人推送消息到群聊
   Company     :     AlphaBrock
   Author      :     jcciam@outlook.com
   Date        :     2024/4/12
-------------------------------------------------
"""
import logging
import time
import hmac
import hashlib
import base64
import urllib.parse
import requests
import html
from django.template import Context, Template

###########公共参数##############################################
# 日志平台名称
sysTitle = "日志平台"
# 兜底机器人token，监控项未配置则使用该配置项
webhook_access_token = ""
# (可选)兜底机器人加签密钥，监控项未配置则使用该配置项
webhook_secret = ""
# 单条最大消息大小
max_message_size = 2048
# 事件数统计、SPL统计以及拓展搜索最大结果行数
max_result_size = 20
# 前置http代理, 适用于无法直连互联网, 需要过一层代理，不涉及留空即可
proxies = {
  'http': '',
  'https': '',
}
url_prefix = "https://oapi.dingtalk.com"
################################################################

reply_content = ""
ONLINE_CONTENT = """{% if alert.strategy.name == "count" and alert.result.hits %}{% for item in alert.result.hits %}原始日志{{forloop.counter}} :  {{item.raw_message}}
 {% endfor %}{% elif alert.strategy.name == "spl_query" %}{% for result_row in alert.result.hits %}{% for k in alert.result.columns %}{% for rk, rv in result_row.items %}{% if rk == k.name %}{{k.name}}:  {{rv}}
{% endif %}{% endfor %}{% endfor %}{% endfor %}{% endif %}"""

META = {
    "name": "DingTalkWebhook",
    "version": 1,
    "alias": "钉钉-自定义机器人群消息告警",
    "configs": [
        {
            "name": "Access_token",
            "alias": "(可选)自定义机器人AccessToken",
            "presence": False,
            "value_type": "string",
            "default_value": "",
            "style": {
                "rows": 1,
                "cols": 30
            }
        },
        {
            "name": "Secret",
            "alias": "(可选)加签密钥",
            "presence": False,
            "value_type": "string",
            "default_value": "",
            "style": {
                "rows": 1,
                "cols": 30
            }
        },{
            "name": "Phones",
            "alias": u"(可选)接收人手机号, 用以@",
            "presence": False,
            "value_type": "string",
            "default_value": "",
            "input_type": "phone",
            "style": {
                "rows": 1,
                "cols": 30
            }
        },
        {
            "name": "content_tmpl",
            "alias": "消息内容模板",
            "presence": True,
            "value_type": "template",
            "default_value": ONLINE_CONTENT,
            "style": {
                "rows": 10,
                "cols": 100
            }
        },
    ]
}


def _render(conf_obj, tmpl_str):
    """
    提供【预览】功能
    Args:
        conf_obj:
        tmpl_str:

    Returns:

    """
    t = Template(tmpl_str)
    c = Context(conf_obj)
    _content = t.render(c)
    return _content


def content(params, alert):
    """
    渲染消息
    Args:
        params:
        alert:

    Returns:

    """
    template_str = params.get("configs")[-1].get("value")
    conf_obj = {"alert": alert}
    _content = _render(conf_obj, template_str)
    return _content


def split_string_by_bytes(string):
    """
    根据指定字节长度分割字符串
    Args:
        string: 字符

    Returns:

    """
    encoded_string = string.encode('utf-8')  # 将字符串编码为 UTF-8 字节序列

    # 如果字符串本身的字节长度小于等于指定字节长度，则无需分割，直接返回原字符串
    if len(encoded_string) <= max_message_size:
        return [string]

    parts = []
    current_bytes = 0
    current_part = ""

    for char in string:
        encoded_char = char.encode('utf-8')
        char_bytes = len(encoded_char)

        # 如果当前部分加上当前字符的字节长度不超过指定字节长度，则将当前字符添加到当前部分中
        if current_bytes + char_bytes <= max_message_size:
            current_part += char
            current_bytes += char_bytes
        else:
            parts.append(current_part)
            current_part = char
            current_bytes = char_bytes

    parts.append(current_part)

    return parts



def gen_timestamp_sign(secret):
    """
    生成签名
    @param secret:
    @return:
    """
    timestamp = str(round(time.time() * 1000))
    secret_enc = secret.encode("utf-8")
    string_to_sign = "{}\n{}".format(timestamp, secret)
    string_to_sign_enc = string_to_sign.encode("utf-8")
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return timestamp, sign


def send_message(alertName, message, phones, access_token, secret):
    """
    推送消息
    Args:
        alertName: 告警名称
        message: 推送消息
        access_token: 机器人key
        phones: 群艾特成员
    Returns:

    """
    if secret:
        timestamp, sign = gen_timestamp_sign(secret)
        url = url_prefix + "/robot/send?access_token={}&timestamp={}&sign={}".format(access_token, timestamp, sign)
    else:
        url = url_prefix + "/robot/send?access_token={}".format(access_token)
    header = {
        "Content-Type": "application/json"
    }
    if len(phones) > 0:
        payload = {
            "msgtype": "text",
            "text": {
                "content": message
            },
            "at": {
                "atMobiles": phones
            }
        }
    else:
        payload = {
            "msgtype": "text",
            "text": {
                "content": message
            }
        }
    try:
        response = requests.request("POST", url=url, headers=header, json=payload, timeout=30, proxies=proxies)
        log_and_reply(logging.INFO, response.text)
        logger.info("告警名称:{}, 推送消息成功, 内容:{}, 返回结果:{}".format(alertName, message, response.text))
    except Exception as e:
        log_and_reply(logging.ERROR, "推送失败, {}".format(e))
        logger.error("告警名称:{}, 推送消息失败, 内容:{}, 抛出错误:{}".format(alertName, message, e))


def handle(params, alert):
    """
    cruxee调用执行函数
    Args:
        params:
        alert:

    Returns:

    """
    logger.info("告警名称:{}, 触发监控, 开始执行推送...".format(alert["name"]))
    alertLevels = {
        "critical": "严重",
        "high": "高",
        "mid": "中",
        "low": "低",
        "info": "信息"
    }
    access_token = params.get('configs')[0].get('value') if params.get('configs')[0].get('value') else webhook_access_token
    secret = params.get('configs')[1].get('value') if params.get('configs')[1].get('value') else webhook_secret
    phones = params.get('configs')[2].get('value').strip(',').split(',')

    if not access_token:
        log_and_reply(logging.WARNING, "access_token未配置, 不允许发送告警")
        return
    extendData = ""
    is_alert_recovery = alert["is_alert_recovery"]
    if is_alert_recovery:
        message = html.unescape(alert['name'] + "告警已恢复")
    else:
        if alert["result"].get("extend_hits"):
            extendData = []
            for extend_hits in alert["result"]["extend_hits"][0:max_result_size]:
                tmpExtendData = []
                for key, value in extend_hits.items():
                    tmpExtendData.append(key + ": " + str(value))
                extendData.append(", ".join(tmpExtendData))
            extendData = "拓展内容:\n" + "\n".join(extendData)
            logger.info("拓展搜索内容:{}".format(extendData))

        message = ""
        if alert["strategy"]["name"] == "field_stat" or alert["strategy"]["name"] == "sequence_stat" or \
                alert["strategy"]["name"] == "baseline_cmp":
            message = alert["description"]
        elif alert["strategy"]["name"] == "count" and alert["result"].get("hits"):
            contens = []
            for data in alert["result"]["hits"][0:max_result_size]:
                if data.get("raw_message") and data.get("ip") and data.get("hostname"):
                    contens.append("IP地址:" + data.get("ip") + ", 主机名:" + data.get("hostname") + ", 原始日志:" + data.get("raw_message") + "\n")
                else:
                    tmpData = []
                    for key, value in data.items():
                        tmpData.append(key + ": " + str(value))
                    contens.append(", ".join(tmpData))
            message = "\n".join(contens)
        elif alert["strategy"]["name"] == "spl_query":
            alert["result"]["hits"] = alert["result"]["hits"][0:max_result_size]
            alert["result"]["columns"] = alert["result"]["columns"][0:max_result_size]
            message = content(params, alert)

        if len(extendData) > 0:
            message = message + '\n' + extendData
    startTitle = "[{}]\n告警名称: ".format(sysTitle) + alert["name"] + "\n告警等级: {}".format(alertLevels.get(alert["strategy"]["trigger"].get("level", "low"))) + "\n告警时间: {}".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))) + "\n告警内容: 👇\n"
    logger.info("发送内容为:{}".format(startTitle + message))
    msgContexts = split_string_by_bytes(startTitle + message)
    if len(msgContexts) > 5:
        for i in range(0, 5):
            send_message(alertName=alert["name"], message=msgContexts[i], phones=phones, access_token=access_token, secret=secret)
    else:
        for message in msgContexts:
            send_message(alertName=alert["name"], message=message, phones=phones, access_token=access_token, secret=secret)
    logger.info("告警名称:{}, 推送完成...".format(alert["name"]))


def log_and_reply(log_level, comment):
    """
    既在日志中打印，又在执行结果中显示
    Args:
        log_level: 日志级别
        comment: 日志内容

    Returns:

    """
    global reply_content
    log_content = {
        logging.FATAL: logger.fatal,
        logging.ERROR: logger.error,
        logging.WARNING: logger.warning,
        logging.INFO: logger.info,
        logging.DEBUG: logger.debug
    }
    log_content.get(log_level)(comment)
    reply_content = '%s%s%s' % (reply_content, "\n", comment)


def execute_reply(params, alert):
    """
    获取执行结果的接口
    Args:
        params:
        alert:

    Returns:

    """
    logger.info("reply_content start")
    handle(params, alert)
    logger.info("reply_content: %s" % reply_content)
    return reply_content


def set_logger(reset_logger):
    """
    配置日志
    Args:
        reset_logger:

    Returns:

    """
    global logger
    logger = reset_logger