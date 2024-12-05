# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name   :     FeishuApplicationYottaweb
   Description :     飞书-应用机器人告警
   Company     :     AlphaBrock
   Author      :     jcciam@outlook.com
   Date        :     2024/4/12
-------------------------------------------------
"""
import logging
import time
import json
import requests
from html import unescape
from django.template import Context, Template

###########公共参数##############################################
# 日志平台名称
sysTitle = "日志平台"
# 应用id
AppId = ""
# 应用秘钥
AppSecret = ""
# 单条最大消息大小
max_message_size = 2048
# 事件数统计、SPL统计以及拓展搜索最大结果行数
max_result_size = 20
# 前置http代理, 适用于无法直连互联网, 需要过一层代理，不涉及留空即可
proxies = {
  'http': '',
  'https': '',
}
url_prefix = "https://open.feishu.cn/open-apis"
################################################################


reply_content = ""
ONLINE_CONTENT = """{% if alert.strategy.name == "count" and alert.result.hits %}{% for item in alert.result.hits %}原始日志{{forloop.counter}} :  {{item.raw_message}}
 {% endfor %}{% elif alert.strategy.name == "spl_query" %}{% for result_row in alert.result.hits %}{% for k in alert.result.columns %}{% for rk, rv in result_row.items %}{% if rk == k.name %}{{k.name}}:  {{rv}}
{% endif %}{% endfor %}{% endfor %}{% endfor %}{% endif %}"""

META = {
    "name": "FeishuApplication",
    "version": 1,
    "alias": "飞书-应用机器人告警",
    "configs": [
        {
            "name": "email",
            "alias": "(二选一)用户邮箱",
            "presence": False,
            "value_type": "string",
            "input_type": "email_account_group",
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
            "input_type": "phone_account_group",
            "default_value": "",
            "style": {
                "rows": 1,
                "cols": 15
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
    if len(encoded_string) <= 2048:
        return [string]

    parts = []
    current_bytes = 0
    current_part = ""

    for char in string:
        encoded_char = char.encode('utf-8')
        char_bytes = len(encoded_char)

        # 如果当前部分加上当前字符的字节长度不超过指定字节长度，则将当前字符添加到当前部分中
        if current_bytes + char_bytes <= 2048:
            current_part += char
            current_bytes += char_bytes
        else:
            parts.append(current_part)
            current_part = char
            current_bytes = char_bytes

    parts.append(current_part)

    return parts


def get_tenant_access_token():
    """
    获取tenant_access_token
    Returns:

    """
    try:
        url = url_prefix + "/auth/v3/tenant_access_token/internal"
        headers = {
            "Content-Type": "application/json; charset=utf-8"
        }
        data = {
            "app_id": AppId,
            "app_secret": AppSecret
        }
        response = requests.post(url, headers=headers, json=data, verify=False, timeout=30, proxies=proxies)
        logger.info(response.text)
        text = response.json()
        if text["code"] == 0:
            return text["tenant_access_token"]
        return None
    except Exception as ex:
        logger.error("获取tenant_access_token异常! exception: {}".format(ex))
        return None


def get_open_id(tenant_access_token, mobiles: list, emails: list):
    """
    通过手机号或者邮箱查询用户ID
    @param tenant_access_token:
    @param mobiles:
    @return:
    """
    open_ids = []
    try:
        url = url_prefix + "/contact/v3/users/batch_get_id?user_id_type=open_id"
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": "Bearer {}".format(tenant_access_token)
        }
        payload = {
            "include_resigned": True,
            "mobiles": mobiles,
            "emails": emails
        }
        response = requests.post(url, headers=headers, json=payload, verify=False, timeout=30, proxies=proxies)
        logger.info(response.text)
        text = response.json()
        if text["code"] == 0:
            for user_list in text["data"]["user_list"]:
                if user_list.get("user_id"):
                    open_ids.append(user_list.get("user_id"))
    except Exception as ex:
        logger.error("获取tenant_access_token异常! exception: {}".format(ex))
    finally:
        logger.info("mobiles:{}, emails:{}, open_ids:{}".format(mobiles, emails, open_ids))
        return open_ids


def send_message(tenant_access_token, open_ids: list, alertName, message):
    """
    推送消息
    @param tenant_access_token:
    @param open_ids:
    @param alertName:
    @param message:
    @return:
    """
    url = url_prefix + "/im/v1/messages?receive_id_type=open_id"
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": "Bearer {}".format(tenant_access_token)
    }
    for receive_id in open_ids:
        payload = {
          "receive_id": receive_id,
          "msg_type": "text",
          "content": json.dumps({"text": message})
        }
        try:

            response = requests.post(url, headers=headers, json=payload, verify=False, timeout=30, proxies=proxies)
            log_and_reply(logging.INFO, response.text)
            logger.info("告警名称:{}, 告警内容:{}, 推送返回结果:{}".format(alertName, message, response.text))
        except Exception as ex:
            logger.error("告警名称:{}, 发送异常, 详情:{}".format(alertName, ex))


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
                if data.get("raw_message") and data.get("ip") and data.get("hostname"):
                    contens.append("IP地址:" + data.get("ip") + ", 主机名:" + data.get("hostname") + ", 原始日志:" + data.get("raw_message") + "\n")
                else:
                    tmpData = []
                    for key, value in data.items():
                        tmpData.append(key + ": " + str(value))
                    contens.append(", ".join(tmpData))
            message = "\n".join(contens)
        elif alert["strategy"]["name"] == "spl_query" and alert["result"].get("hits"):
            alert["result"]["hits"] = alert["result"]["hits"][0:max_result_size]
            alert["result"]["columns"] = alert["result"]["columns"][0:max_result_size]
            message = content(params, alert)

        if message == "":
            log_and_reply(logging.WARNING, "统计结果为空, 请确认查询条件后重试...")
            return


        if len(extendData) > 0:
            message = message + '\n' + extendData
    startTitle = "[{}]\n告警名称: ".format(sysTitle) + alert["name"] + "\n告警等级: {}".format(alertLevels.get(alert["strategy"]["trigger"].get("level", "low"))) + "\n告警时间: {}".format(time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))) + "\n告警内容: 👇\n"

    logger.info("推送内容为:{}".format(startTitle + unescape(message)))
    msgContexts = split_string_by_bytes(startTitle + unescape(message))

    emails = params.get("configs")[0].get("value").strip(',')
    mobiles = params.get("configs")[1].get("value").strip(',')
    logger.info("推送用户邮箱为:{}, 手机号为:{}".format(emails, mobiles))

    if len(emails) == 0 and len(mobiles) == 0:
        log_and_reply(logging.ERROR, "未输入用户邮箱或者手机号, 不允许发送告警")
        return
    tenant_access_token = get_tenant_access_token()
    if tenant_access_token:
        open_ids = get_open_id(tenant_access_token, mobiles.split(","), emails.split(","))
        if len(open_ids) > 0:
            if len(msgContexts) > 5:
                for i in range(0, 5):
                    send_message(tenant_access_token=tenant_access_token, open_ids=open_ids, alertName=alert["name"], message=msgContexts[i])
            else:
                for message in msgContexts:
                    send_message(tenant_access_token=tenant_access_token, open_ids=open_ids, alertName=alert["name"], message=message)
        else:
            logger.warning("根据手机号或者邮箱查询无相关用户open_id, mobiles:{}, emails:{}".format(mobiles, emails))
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

