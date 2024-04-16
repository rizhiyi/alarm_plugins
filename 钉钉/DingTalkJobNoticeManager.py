# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name   :     DingTalkJobNoticeManager
   Description :     工作通知_Manager版
   Company     :     AlphaBrock
   Author      :     jcciam@outlook.com
   Date        :     2024/4/12
-------------------------------------------------
"""
import json
import logging.config
from datetime import datetime

import requests
from common.plugin_util import convert_config

###########公共参数##############################################
# 前置http代理, 适用于无法直连互联网, 需要过一层代理，不涉及留空即可
proxies = {
  'http': '',
  'https': '',
}
url_prefix = "https://oapi.dingtalk.com"
################################################################

logger = logging.getLogger(__name__)


META = {
    "name": "DingTalkJobNoticeManager",
    "version": 1,
    "alias": "钉钉-工作通知",
    "configs": [
        {
          "name": "phones",
          "alias": "@指定接收人[手机号, 多个以,号分割]",
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
            "name": "AgentId",
            "alias": "企业内部应用AgentId",
            "presence": True,
            "value_type": "string",
            "default_value": "",
            "style": {
                "rows": 1,
                "cols": 60
            }
        },{
            "name": "ClientId",
            "alias": "应用ID (原 AppKey 和 SuiteKey)",
            "presence": True,
            "value_type": "string",
            "default_value": "",
            "style": {
                "rows": 1,
                "cols": 60
            }
        },{
            "name": "ClientSecret",
            "alias": "应用秘钥 (原 AppSecret 和 SuiteSecret)",
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


def get_access_token(ClientId, ClientSecret):
    """
    获取access_token,每次运行都会获取一个
    @return:
    """
    url = url_prefix + "/gettoken"
    params = {
        "appkey": ClientId,
        "appsecret": ClientSecret
    }

    try:
        response = requests.get(url, params=params, verify=False, timeout=30, proxies=proxies)
        logger.info(response.text)
        text = response.json()
        if text["errcode"] == 0:
            access_token = text["access_token"]
            logger.info("获取access token: %s" % access_token)
            return access_token
        return None
    except Exception as e:
        logger.error("获取access token异常, %s" % e)
        return None


def get_userid_by_mobile(access_token, phones):
    """
    通过手机号获取钉钉中的userid
    @param access_token:
    @param phone:
    @return:
    """
    userids = []
    url = url_prefix + "/topapi/v2/user/getbymobile?access_token={}".format(access_token)
    header = {
        "Content-Type": "application/json"
    }
    for phone in phones:
        data = {
            "mobile": phone
        }
        try:
            response = requests.post(url, json=data, headers=header, verify=False, timeout=30, proxies=proxies)
            logger.info(response.text)
            text = response.json()
            if text["errcode"] == 0:
                userids.append(text["result"]["userid"])
        except Exception as e:
            logger.error("获取userid异常, %s" % e)
        finally:
            return userids


def send_message(AgentId, access_token, userid_list, message, title):
    """
    发送工作消息
    @param access_token:
    @param userid_list:
    @param message:
    @return:
    """
    userid_list = ",".join(userid_list)
    url = url_prefix + "/topapi/message/corpconversation/asyncsend_v2?access_token={}".format(access_token)
    header = {
        "Content-Type": "application/json"
    }
    data = {
        "msg": {
            "msgtype": "text",
            "text": {
                "content": "[日志平台Manager]\n" + "告警名称:  " + title + '\n' + message
            }
        },
        "agent_id": AgentId,
        "userid_list": userid_list
    }
    try:
        response = requests.post(url=url, json=data, headers=header, verify=False, timeout=30, proxies=proxies)
        logger.info(response.text)
        text = response.json()
        if text["errcode"] == 0:
            logger.info("告警:{}, 推送成功, 推送内容:{}".format(title, json.dumps(data, ensure_ascii=False)))
        else:
            logger.warning("告警:{}, 推送失败, 推送内容:{}".format(title, json.dumps(data, ensure_ascii=False)))
    except Exception as e:
        logger.error("告警:{}, 推送异常:{}, 推送内容:{}".format(title, e, json.dumps(data, ensure_ascii=False)))


def handle(meta, alert):
    param_configs = meta.get("param_configs")
    param_configs = convert_config(param_configs)
    logger.info("param_configs:{}".format(param_configs))
    AgentId = param_configs.get("AgentId", "")
    ClientId = param_configs.get("ClientId", "")
    ClientSecret = param_configs.get("ClientSecret", "")
    if not AgentId or not ClientId or not ClientSecret:
        logger.error("AgentId或ClientId或ClientSecret不能为空")
        return False

    configs = meta.get("configs")
    configs = convert_config(configs)
    phones = configs.get("phones", "").replace("，", "").split(",")

    title, content = gen_content(alert)
    access_token = get_access_token(ClientId, ClientSecret)
    if access_token:
        userid_list = get_userid_by_mobile(access_token, phones)
        if len(userid_list) > 0:
            send_message(AgentId, access_token, userid_list, content, title)
        else:
            logger.warning("根据输入手机号:{}, 无法查询相关用户".format(phones))
    else:
        logger.error("获取AccessToken异常, 不进行推送")