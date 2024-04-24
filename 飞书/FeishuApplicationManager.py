# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name   :     FeishuApplicationManager
   Description :     飞书-应用机器人告警Manager
   Company     :     AlphaBrock
   Author      :     jcciam@outlook.com
   Date        :     2024/4/12
-------------------------------------------------
"""
import logging.config
from datetime import datetime
import json
import requests
from common.plugin_util import convert_config

###########公共参数##############################################
# 前置http代理, 适用于无法直连互联网, 需要过一层代理，不涉及留空即可
proxies = {
    'http': '',
    'https': '',
}
url_prefix = "https://open.feishu.cn/open-apis"
################################################################

logger = logging.getLogger(__name__)

META = {
    "name": "FeishuApplicationManager",
    "version": 1,
    "alias": "飞书-应用机器人告警",
    "configs": [
        {
            "name": "mobiles",
            "alias": "@指定接收人[手机号, 多个以,号分割]",
            "value_type": "string",
            "default_value": "",
            "style": {
                "rows": 1,
                "columns": 15
            }
        }, {
            "name": "emails",
            "alias": "邮箱[多个以,号分割]",
            "value_type": "string",
            "default_value": "",
            "style": {
                "rows": 1,
                "columns": 15
            }
        }
    ],
    "param_configs": [
        {
            "name": "AppId",
            "alias": "应用ID(AppId)",
            "presence": True,
            "value_type": "string",
            "default_value": "",
            "style": {
                "rows": 1,
                "cols": 60
            }
        }, {
            "name": "AppSecret",
            "alias": "应用密钥(AppSecret)",
            "presence": True,
            "value_type": "string",
            "default_value": "",
            "style": {
                "rows": 1,
                "cols": 60
            }
        }
    ]
}


def gen_content(alert):
    final_alert = {}
    module = alert.get("Module", "")
    type = alert.get("Type", "")
    ip = alert.get("Ip", "")
    alarm_time = alert.get("Time", "")
    if alarm_time == "":
        alarm_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    detail = alert.get("Detail", "")
    recovery = alert.get("Recover", "")
    if recovery == "True" or recovery == True:
        recovery = u"恢复"
        recoveryString = u"告警已恢复: "
    else:
        recovery = u""
        recoveryString = u""

    if module != "" and ip != "":
        title = u"%s %s %s%s通知" % (ip, module, type, recovery)
        content = u"%s告警类型: %s\n告警模块: %s\n告警IP: %s\n告警时间: %s\n告警详情: %s" % (recoveryString, type, module, ip, alarm_time, detail)
    elif ip != "":
        title = u"%s %s%s通知" % (ip, type, recovery)
        content = u"%s告警类型: %s\n告警IP: %s\n告警时间: %s\n告警详情: %s" % (recoveryString, type, ip, alarm_time, detail)
    else:
        title = u"%s%s通知" % (type, recovery)
        content = u"%s告警类型: %s\n告警时间: %s\n告警详情: %s" % (recoveryString, type, alarm_time, detail)

    return title, content


def get_tenant_access_token(AppID, AppSecret):
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
            "app_id": AppID,
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
        logger.info("mobiles:{}, open_ids:{}".format(mobiles, open_ids))
        return open_ids


def send_message(tenant_access_token, open_ids: list, title, message):
    message = "[日志平台Manager]\n" + "告警名称:  " + title + '\n' + message

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
            logger.info("告警名称:{}, 告警内容:{}, 推送返回结果:{}".format(title, message, response.text))
        except Exception as ex:
            logger.error("告警名称:{}, 发送异常, 详情:{}".format(title, ex))


def handle(meta, alert):
    param_configs = meta.get("param_configs")
    param_configs = convert_config(param_configs)
    AppId = param_configs.get("AppId", "")
    AppSecret = param_configs.get("AppSecret", "")
    if not AppId or not AppSecret:
        logger.error("AppId或AppSecret不能为空")
        return False

    configs = meta.get("configs")
    configs = convert_config(configs)
    mobiles = configs.get("mobiles", "").replace("，", "")
    emails = configs.get("emails", "").replace("，", "")

    if len(mobiles) == 0 and len(emails) == 0:
        logger.error("手机号和邮箱不能同时为空")
        return False

    tenant_access_token = get_tenant_access_token(AppId, AppSecret)
    if tenant_access_token:
        title, content = gen_content(alert)
        logger.info("mobiles:{}, Title:{}, Content:{}, emails:{}".format(mobiles, title, content, emails))
        open_ids = get_open_id(tenant_access_token, mobiles.split(","), emails.split(","))
        if len(open_ids) > 0:
            send_message(tenant_access_token, open_ids, title, content)
        else:
            logger.warning("根据手机号或者邮箱查询无相关用户open_id, mobiles:{}, emails:{}".format(mobiles, emails))
