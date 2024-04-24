# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name   :     WeworkApplicationYottaweb.py
   Description :     企业微信应用告警推送
   Author      :     chen.fei
   Email       :     jcciam@outlook.com
   Date        :     2024/4/11 10:13
-------------------------------------------------
"""
import logging
import time
import json
import requests
from html import unescape
from django.template import Context, Template

###########公共参数##############################################
# 企业id
corpid = ""
# 应用秘钥
secret = ""
# 应用id
agentid = ""
# 单条最大消息大小
max_message_size = 2048
# 事件数统计、SPL统计以及拓展搜索最大结果行数
max_result_size = 20
# 前置http代理, 适用于无法直连互联网, 需要过一层代理，不涉及留空即可
proxies = {
  'http': '',
  'https': '',
}
url_prefix = "https://qyapi.weixin.qq.com/cgi-bin"
################################################################


reply_content = ""
ONLINE_CONTENT = """{% if alert.strategy.name == "count" and alert.result.hits %}{% for item in alert.result.hits %}原始日志{{forloop.counter}} :  {{item.raw_message}}
 {% endfor %}{% elif alert.strategy.name == "spl_query" %}{% for result_row in alert.result.hits %}{% for k in alert.result.columns %}{% for rk, rv in result_row.items %}{% if rk == k.name %}{{k.name}}:  {{rv}}
{% endif %}{% endfor %}{% endfor %}{% endfor %}{% endif %}"""

META = {
    "name": "WeworkApplication",
    "version": 1,
    "alias": "企业微信-应用消息告警",
    "configs": [
        {
            "name": "user_id",
            "alias": "(二选一)用户ID, 多用户ID以,(逗号)分割",
            "presence": False,
            "value_type": "string",
            "default_value": "",
            "style": {
                "rows": 1,
                "cols": 15
            }
        },
        {
            "name": "phones",
            "alias": "(二选一)手机号",
            "presence": False,
            "value_type": "string",
            "input_type": "phone",
            "default_value": "",
            "style": {
                "rows": 1,
                "cols": 15
            }
        },
        {
            "name": "msg_content",
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


def _get_token():
    """
    获取access token
    Returns:

    """
    try:
        url = url_prefix + "/gettoken?corpid={}&corpsecret={}".format(corpid, secret)
        resp = requests.get(url, verify=False, timeout=30, proxies=proxies)
        if resp.status_code == 200:
            resp_json = resp.json()
            if resp_json["errcode"] == 0:
                access_token = resp_json["access_token"]
                logger.info("获取Token成功, access_token: {}".format(access_token))
                return access_token
            errmsg = resp_json["errmsg"]
            log_and_reply(logging.ERROR, "获取Token失败! errmsg: {}".format(errmsg))
            return None
        logger.error("获取Token失败! response: {}".format(resp.text))
    except Exception as ex:
        logger.error("获取Token异常! exception: {}".format(ex))
    log_and_reply(logging.ERROR, "获取Token异常! exception: {}".format(ex))
    return None


def _get_user_id(phones, access_token):
    """
    根据手机号获取用户ID
    Returns:

    """
    user_ids = []
    try:
        url = url_prefix + "/user/getuserid?access_token={}".format(access_token)
        for phone in phones:
            body = {
                "mobile": phone
            }
            resp = requests.post(url, json=body, verify=False, timeout=30, proxies=proxies)
            if resp.status_code == 200:
                resp_json = resp.json()
                if resp_json["errcode"] == 0:
                    user_ids.append(resp_json["userid"])
                else:
                    logger.error("获取{}用户ID失败, 详情:{}".format(phone, resp_json["errmsg"]))
    except Exception as e:
        logger.error("获取UserID异常! exception: {}".format(e))
    finally:
        return "|".join(user_ids)


def send_message(alertName, users, message, access_token):
    """
    @param users: 接收消息的成员
    @param message: 消息内容
    @param access_token: access_token
    @return:
    """
    url = url_prefix + "/message/send?access_token={}".format(access_token)
    payload = {
        "touser": users,
        "msgtype": "text",
        "agentid": agentid,
        "text": {
            "content": message
        }
    }
    try:
        response = requests.post(url, data=json.dumps(payload), verify=False, timeout=30, proxies=proxies)
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
    extendData = ""
    is_alert_recovery = alert["is_alert_recovery"]
    if is_alert_recovery:
        message = unescape(alert['name'] + "告警已恢复")
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
                if data.get("raw_message"):
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
    startTitle = "[日志平台]\n告警名称: " + alert["name"] + "\n告警等级: {}".format(alertLevels.get(alert["strategy"]["trigger"].get("level", "low"))) + "\n告警时间: {}".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))) + "\n告警内容: 👇\n"

    logger.info("推送内容为:{}".format(startTitle+message))
    msgContexts = split_string_by_bytes(startTitle + message)

    users_id = params.get("configs")[0].get("value").replace("，", ",")
    mobiles = params.get("configs")[1].get("value").strip(',')
    logger.info("推送用户id为:{}, 手机号为:{}".format(users_id, mobiles))

    if len(users_id) == 0 and len(mobiles) == 0:
        log_and_reply(logging.ERROR, "未输入用户ID或者手机号, 不允许发送告警")
        return False
    access_token = _get_token()
    if access_token:
        users_str = ""
        if len(users_id) > 0:
            if users_id == "all":
                users_str = "@all"
            else:
                users_str = "|".join(users_id.split(","))
        elif len(mobiles) > 0:
            try:
                users_str = _get_user_id(mobiles.split(','), access_token)
                if len(users_str) == 0:
                    logger.error("获取用户id失败, 不执行发送")
                    log_and_reply(logging.ERROR, "获取用户id失败, 不执行发送")
                    return False
            except Exception as e:
                log_and_reply(logging.ERROR, "请输入正确手机号, 多个手机号请以逗号分割")
                return False

        if len(msgContexts) > 5:
            for i in range(0, 5):
                send_message(alertName=alert["name"], users=users_str, message=msgContexts[i], access_token=access_token)
        else:
            for message in msgContexts:
                send_message(alertName=alert["name"], users=users_str, message=message, access_token=access_token)
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

