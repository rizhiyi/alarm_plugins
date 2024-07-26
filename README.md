# 1. 前言

日志易所用插件均为python语言所写，其对编码以及缩进有着严格的要求，因而建议使用专业的代码编辑器修改，常见编辑器有：

1. notepad++

   官网：https://notepad-plus-plus.org/downloads/

2. vs code

   官网：https://code.visualstudio.com/download

3. Linux下的vi、vim编辑器

**PS: **请勿使用Windows默认文本编辑器编辑修改脚本，否则会造成上传插件无法验证通过

## 1.1. 基本参数

每个插件都需要填写相关参数信息方可推送数据，具体参数请根据2-4章节说明即可

## 1.2. HTTP代理

每个插件内置了代理配置，如下:

```python
proxies = {
  'http': '',
  'https': '',
}
```

增加该配置用以解决客户现场日志易主机无法直连互联网，需要走一层HTTP代理，按需填写即可，不涉及代理则无需填写

配置样例如下，统一格式为`http://${ip}:${port}`：

```python
proxies = {
  'http': 'http://1.1.1.1:3128',
  'https': 'http://1.1.1.1:3128',
}
```

**PS: **当前企业内部设计http正向代理大部分来自squid提供的服务，少数可能自研，但是涉及客户提供的代理信息一般就只有ip和端口俩项

## 1.3. 插件类型

以日志易为维度大致有3类插件：

1. Yottaweb插件

   用以推送实际业务监控告警

2. manager插件

   用以推送日志易平台自身的监控

3. Soar插件

   可以在【执行脚本】算子引用



以推送类型大致有3类告警：

1. 企业微信
2. 钉钉
3. 飞书

具体说明请参阅对应章节，以下是针对每种插件文件名的作用描述：

| 序号 | 文件名                       | 类型     | 描述                 |
| ---- | ---------------------------- | -------- | -------------------- |
| 1    | DingTalkJobNoticeManager.py  | 钉钉     | manager版本工作通知  |
| 2    | DingTalkJobNoticeSoar.py     | 钉钉     | soar版本工作通知     |
| 3    | DingTalkJobNoticeYottaweb.py | 钉钉     | yottaweb版本工作通知 |
| 4    | DingTalkWebhookManager.py    | 钉钉     | manager版本群消息    |
| 5    | DingTalkWebhookSoar.py       | 钉钉     | soar版本群消息       |
| 6    | DingTalkWebhookYottaweb.py   | 钉钉     | yottaweb版本群消息   |
| 7    | FeishuApplicationManager.py  | 飞书     | manager版本应用消息  |
| 8    | FeishuApplicationSoar.py     | 飞书     | soar版本应用消息     |
| 9    | FeishuApplicationYottaweb.py | 飞书     | yottaweb版本应用消息 |
| 10   | FeishuWebhookManager.py      | 飞书     | manager版本群消息    |
| 11   | FeishuWebhookSoar.py         | 飞书     | soar版本群消息       |
| 12   | FeishuWebhookYottaweb.py     | 飞书     | yottaweb版本群消息   |
| 13   | WeworkApplicationManager.py  | 企业微信 | manager版本应用消息  |
| 14   | WeworkApplicationSoar.py     | 企业微信 | soar版本应用消息     |
| 15   | WeworkApplicationYottaweb.py | 企业微信 | yottaweb版本应用消息 |
| 16   | WeworkWebhookManager.py      | 企业微信 | manager版本群消息    |
| 17   | WeworkWebhookSoar.py         | 企业微信 | soar版本群消息       |
| 18   | WeworkWebhookYottaweb.py     | 企业微信 | yottaweb版本群消息   |

## 1.4. 使用说明

### 1.4.1. Yottaweb插件

1. 进去【监控】页面，在【其他】-->【告警插件】页面进行上传即可

   ![image-20240411114214590](https://s3.johnwick.app/img/windows/2024/04/11/image-20240411114214590.png)

   ![image-20240411114246138](https://s3.johnwick.app/img/windows/2024/04/11/image-20240411114246138.png)

2. 在具体的监控配置中【添加告警方式】引入导入插件，配置好相关参数即可

   ![image-20240411114411283](https://s3.johnwick.app/img/windows/2024/04/11/image-20240411114411283.png)

3. 具体的参数填写说明请查阅相关章节

### 1.4.2. Manager插件

1. 登录manager，按照下图指引上传即可

   ![image-20240411114056545](https://s3.johnwick.app/img/windows/2024/04/11/image-20240411114056545.png)

   ![](https://s3.johnwick.app/img/windows/2024/04/16/202404161520820.png)

2. 在【告警规则查询】页面修改相应的规则，添加插件即可

   ![image-20240411114601967](https://s3.johnwick.app/img/windows/2024/04/11/image-20240411114601967.png)

   ![image-20240411114621720](https://s3.johnwick.app/img/windows/2024/04/11/image-20240411114621720.png)

3. 具体的参数填写说明请查阅相关章节

### 1.4.3. Soar插件

1. 将脚本传到soar节点的任意路径

2. soar剧本添加一个【字段操作组件】算子，获取必要的威胁字段

   | 字段名称   | 描述     |
   | ---------- | -------- |
   | srcAddr    | 来源IP   |
   | dstAddr    | 目标IP   |
   | threatName | 告警名称 |
   | threatDesc | 告警描述 |

   ![image-20240424100926442](https://s3.johnwick.app/img/windows/2024/04/24/202404241009607.png)

3. 在合适的位置添加【执行脚本】算子，配置使用的shell脚本语言，一下是参考样例

   ```shell
   # 获取告警描述
   threatDesc=`GetJsonFieldValue kv_json .threat_data[0].srcAddr`
   # 获取告警名称
   threatName=`GetJsonFieldValue kv_json .threat_data[0].srcAddr`
   # 保存字段变量
   SaveFieldValue threatDesc $threatDesc
   SaveFieldValue threatName $threatName
   
   # 执行脚本并将返回结果存放于info变量，变量以实际脚本要求为准
   info=`/opt/rizhiyi/python/bin/python /data/rizhiyi/soar/script/WeworkApplicationSoar.py --alert_name '$threatName' --alert_msg '$data' --mobiles 11111111111`
   ```
4. 具体的脚本参数填写说明请查阅相关章节
   

## 1.5. 日志路径

1. Yottaweb插件

   运行所产生的日志统一存放在cruxee机器的/data/rizhiyi/logs/cruxee/plugins路径，文件名以上传显示的名称一致，如下

   ![image-20240411151240837](https://s3.johnwick.app/img/windows/2024/04/11/image-20240411151240837.png)

2. Manager插件

   运行所产生的日志存放于: /data/rizhiyi/logs/plugin.log

3. Soar插件

   运行所产生的日志存放于soar节点机器: /data/rizhiyi/logs/soar/

# 2. 企业微信

| 告警类型 | 描述                                           | 官方文档                                                 |
| -------- | ---------------------------------------------- | -------------------------------------------------------- |
| 群机器人 | 推送至企业微信群，需要提前创建群聊             | https://developer.work.weixin.qq.com/document/path/99110 |
| 应用消息 | 推送至个人微信，需要企业管理员提前创建相关应用 | https://developer.work.weixin.qq.com/document/path/90236 |

## 2.1. 群机器人

### 2.1.1. 效果

![image-20240411160219276](https://s3.johnwick.app/img/windows/2024/04/11/image-20240411160219276.png)

### 2.1.2. 参数说明

webhook_key：在企业微信群添加完机器人后会得到一个Webhook地址，其有个参数key，=号右侧为我们需要的key值，将其填入脚本中即可

具体获取方式请查阅2.1.3章节

### 2.1.3. 如何获取

1. 按需建立相关企业群
2. 群管理中添加群机器人，完成后点击机器人即可看到webhook地址，如下图

​	![image-20240411112024971](https://s3.johnwick.app/img/windows/2024/04/11/image-20240411112024971.png)

### 2.1.4. 插件使用

#### 2.1.4.1. Yottaweb插件

1. 使用编辑器打开脚本，根据2.1.3章节获取到的相关信息填入脚本，webhook_key参数仅用于当监控项中未配置key时则采用该参数进行推送，属于兜底策略

   ![image-20240417094117748](https://s3.johnwick.app/img/windows/2024/04/17/202404170941889.png)

2. 根据1.4.1章节上传插件

3. 监控告警推送引用插件相关参数配置

   **(可选)自定义机器人Key**：由于监控可能涉及多个部门，且每个部门都有相关微信群，该配置用以覆盖该情况，注意只能填写一个key，不填写则默认使用脚本参数配置的key，样例如下

   ```
   https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=1edadadad48-8142-47ec-996e-fbdadadad56ed
   ```

   **(可选)接收人手机号**：如果需要监控推送@指定相关人员，则在该项填入手机号即可

   ![image-20240417094256262](https://s3.johnwick.app/img/windows/2024/04/17/202404170942353.png)

#### 2.1.4.2. Manager插件

1. 根据1.4.2章节上传插件

2. 打开插件引用并配置Webhook Key

   ![image-20240411154757360](https://s3.johnwick.app/img/windows/2024/04/11/image-20240411154757360.png)

   ![image-20240411154835662](https://s3.johnwick.app/img/windows/2024/04/11/image-20240411154835662.png)

3. 【告警规则查询】页面将需要监控的配置项设置推送，如有需要可配置指定接收人手机号

   ![image-20240411154923383](https://s3.johnwick.app/img/windows/2024/04/11/image-20240411154923383.png)

   ![image-20240411154954405](https://s3.johnwick.app/img/windows/2024/04/11/image-20240411154954405.png)

   ![image-20240411155133000](https://s3.johnwick.app/img/windows/2024/04/11/image-20240411155133000.png)

#### 2.1.4.3. Soar插件

1. 使用编辑器打开脚本，根据2.1.3章节获取到的相关信息填入脚本，webhook_key参数仅用于当监控项中未配置key时则采用该参数进行推送，属于兜底策略

   ![image-20240424102041287](https://s3.johnwick.app/img/windows/2024/04/24/202404241020390.png)

2. 按照1.4.3章节上传并配置算子

3. 脚本执行说明

   以下是脚本使用样例

   ```
   /opt/rizhiyi/python/bin/python /data/rizhiyi/soar/python/WeworkWebhookSoar.py --alert_name '告警测试' --alert_msg '测试' --mobiles 1111111,222222 --key xxxxxxxxxxxxxx
   ```

   详细参数说明如下

   | 参数             | 说明                                                 |
   | ---------------- | ---------------------------------------------------- |
   | alert_name(必填) | 告警名称, 建议以单引号限定, 否则遇到空格会报错       |
   | alert_msg(必填)  | 告警信息, 建议以单引号限定, 否则遇到空格会报错       |
   | mobiles(选填)    | 手机号, 多手机以,(逗号)分割                          |
   | key(选填)        | 机器人webhook key，与脚本参数webhook_key不能同时为空 |

## 2.2. 应用消息

### 2.2.1. 效果

![image-20240412091156081](https://s3.johnwick.app/img/windows/2024/04/12/image-20240412091156081.png)

### 2.2.2. 参数说明

> 官方描述文档：https://developer.work.weixin.qq.com/document/path/90665

1. corpid

   每个企业都拥有唯一的corpid

2. secret

   企业应用里面用于保障数据安全的“钥匙”，每一个应用都有一个独立的访问密钥

3. agent_id

   每个应用都有唯一的agentid

4. userid

   每个成员都有唯一的userid，即所谓“账号”

### 2.2.3. 如何获取

> 网页管理后台入口：https://work.weixin.qq.com/wework_admin
>
> 官方描述文档：https://developer.work.weixin.qq.com/document/path/90665

1. corpid

   管理后台【我的企业】－【企业信息】下查看【企业ID】（需要有管理员权限）

   ![image-20240411170851724](https://s3.johnwick.app/img/windows/2024/04/11/image-20240411170851724.png)

2. secret

   在【管理后台】->【应用管理】->【应用】->【自建】，点进某个应用，即可看到，同agentid且配套使用

   ![image-20240411171059453](https://s3.johnwick.app/img/windows/2024/04/11/image-20240411171059453.png)

   ![image-20240411171122161](https://s3.johnwick.app/img/windows/2024/04/11/image-20240411171122161.png)

3. agent_id

   在【管理后台】->【应用管理】->【应用】->【自建】，点进某个应用，即可看到，同secret且配套使用

4. userid(用户id)

   在【管理后台】->【通讯录】->点进某个成员的详情页，可以看到

   ![image-20240411171349796](https://s3.johnwick.app/img/windows/2024/04/11/image-20240411171349796.png)

### 2.2.4. 插件使用

#### 2.2.4.1. Yottaweb插件

1. 使用编辑器打开脚本，根据2.2.3章节获取到的相关信息填入脚本

   ![image-20240416161443577](https://s3.johnwick.app/img/windows/2024/04/16/202404161614689.png)

2. 根据1.4.1章节上传插件

3. 监控告警推送引用插件相关参数配置

   **(二选一)填入用户ID, 多用户ID以,(逗号)分割：**2.2.2章节中的userid参数

   **(二选一)填入手机号：**可从平台已有用户信息引入也可手动输入手机号

   **PS：**俩个选项均不能留空，否则不允许发送

   ![image-20240416161903141](https://s3.johnwick.app/img/windows/2024/04/16/202404161619262.png)

#### 2.2.4.2. Manager插件

1. 根据1.4.2章节上传插件并将插件功能【开启】

2. 根据2.2.3章节获取的相关参数填入到配置项

   ![image-20240416162221950](https://s3.johnwick.app/img/windows/2024/04/16/202404161622083.png)

3. 最后根据1.4.2章节针对相关告警规则进行绑定推送渠道，并配置接收人信息，参数配置同2.2.4.1章节

   **PS：**注意多个接收人要以英文逗号(,)分割，否则无法推送成功

   ![image-20240416162405624](https://s3.johnwick.app/img/windows/2024/04/16/202404161624727.png)

#### 2.2.4.3. Soar插件

1. 使用编辑器打开脚本，根据2.2.3章节获取到的相关信息填入脚本

   ![image-20240424102711034](https://s3.johnwick.app/img/windows/2024/04/24/202404241027139.png)

2. 按照1.4.3章节上传并配置算子

3. 脚本执行说明

   以下是脚本使用样例

   ```shell
   /opt/rizhiyi/python/bin/python /data/rizhiyi/soar/python/WeworkApplicationSoar.py --alert_name '告警测试' --alert_msg '测试' --users_ids 1111111,222222 --mobiles 1111111,222222
   ```

   | 参数             | 说明                                                   |
   | ---------------- | ------------------------------------------------------ |
   | alert_name(必填) | 告警名称, 建议以单引号限定, 否则遇到空格会报错         |
   | alert_msg(必填)  | 告警信息, 建议以单引号限定, 否则遇到空格会报错         |
   | users_ids(选填)  | 用户ID, 多用户ID以,(逗号)分割, 与mobiles参数只能选一个 |
   | mobiles(选填)    | 手机号, 多手机以,(逗号)分割, 与users_ids参数只能选一个 |

# 3. 钉钉

| 告警类型     | 描述                                                         | 官方文档                                                     |
| ------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| 自定义机器人 | 通过 Webhook 接入自定义服务，使用自定义机器人，支持在企业内部群和普通钉钉群内发送群消息，不支持发送单聊消息 | https://open.dingtalk.com/document/orgapp/robot-overview     |
| 工作通知     | 以某个应用的名义推送到员工的工作通知消息，例如生日祝福、入职提醒等 | https://open.dingtalk.com/document/isvapp/send-job-notification |

## 3.1. 自定义机器人

### 3.1.1. 效果

![image-20240412122112324](https://s3.johnwick.app/img/windows/2024/04/12/image-20240412122112324.png)

### 3.1.2. 参数说明

1. acces_token

   群管理创建完机器人后会得到一个webhook地址，样例如下：

   ```
   https://oapi.dingtalk.com/robot/send?access_token=59e6cf04a5021c4470a2040c50d0202
   ```

   其中的`access_token`就是需要的信息

2. 加签

   > 参考：https://developers.dingtalk.com/document/robots/customize-robot-security-settings

   钉钉机器人为了避免滥用，增加了三种安全配置，常用的有加签、IP地址，其中加签由于需要代码特殊处理，因而需要拿到该参数该参数

   **PS：**根据客户现场实际调整，建议优先使用IP地址 (段)，其次为加签作为机器人的安全设置

### 3.1.3. 如何获取

> 官方描述文档
>
> 如何创建自定义机器人：https://open.dingtalk.com/document/orgapp/custom-bot-creation-and-installation
>
> 获取自定义机器人WebHook地址：https://open.dingtalk.com/document/orgapp/obtain-the-webhook-address-of-a-custom-robot
> 

1. 首先需要建立相关钉钉群，外部群或者内部群
2. 群设置中添加机器人，操作如下截图

​	![image-20240412103028965](https://s3.johnwick.app/img/windows/2024/04/12/image-20240412103028965.png)

​	![image-20240412103107462](https://s3.johnwick.app/img/windows/2024/04/12/image-20240412103107462.png)

3. 添加完成后在Webhook栏可以看到参数`access_token`，在安全设置栏可以配置IP地址以及加签秘钥

![image-20240416164552101](https://s3.johnwick.app/img/windows/2024/04/16/202404161645223.png)




### 3.1.4. 插件使用

#### 3.1.4.1. Yottaweb插件

1. 使用编辑器打开脚本，根据3.1.3章节获取到的相关信息填入脚本，webhook_access_token以及webhook_secret参数仅用于当监控项中未配置时则采用该参数进行推送，属于兜底策略

   ![image-20240417094346930](https://s3.johnwick.app/img/windows/2024/04/17/202404170943016.png)

2. 根据1.4.1章节上传插件并添加插件到相关监控

3. 监控告警推送引用插件相关参数配置

   **(可选)自定义机器人AccessToken**：机器人token，获取方式参考3.1.3章节；由于监控可能涉及多个部门，且每个部门都有相关钉钉群，该配置用以覆盖该情况，注意只能填写一个token，不填写则默认使用脚本参数配置的token

   **(可选)加签密钥**：安全设置中的加签秘钥，获取方式参考3.1.3章节，若客户现场不涉及无需填写

   **(可选)接收人手机号, 用以@：**当需要推送的消息@群成员的话可以填入手机号

   ![image-20240417094506108](https://s3.johnwick.app/img/windows/2024/04/17/202404170945199.png)

#### 3.1.4.2. Manager插件

1. 根据1.4.2章节上传插件并将插件功能【开启】

2. 根据3.1.3章节获取的相关参数填入到配置项

   **Access_token：**机器人token，获取方式参考3.1.3章节

   **加签密钥(Secret), 可选**：安全设置中的加签秘钥，获取方式参考3.1.3章节，若客户现场不涉及无需填写

   ![image-20240416165522362](https://s3.johnwick.app/img/windows/2024/04/16/202404161655513.png)

3. 最后根据1.4.2章节针对相关告警规则进行绑定推送渠道

   当需要推送的消息@群成员的话可以填入手机号

   **PS：**多用手机号请以英文逗号(,)分割

​	![image-20240416165744039](https://s3.johnwick.app/img/windows/2024/04/16/202404161657157.png)

#### 3.1.4.3. Soar插件

1. 使用编辑器打开脚本，根据3.1.3章节获取到的相关信息填入脚本，webhook_access_token以及webhook_secret参数仅用于当监控项中未配置时则采用该参数进行推送，属于兜底策略

   ![image-20240424103036983](https://s3.johnwick.app/img/windows/2024/04/24/202404241030095.png)

2. 按照1.4.3章节上传并配置算子

3. 脚本执行说明

   以下是脚本使用样例

   ```shell
   /opt/rizhiyi/python/bin/python /data/rizhiyi/soar/python/DingTalkWebhookSoar.py --alert_name '告警测试' --alert_msg '测试' --access_token xxxx --secret xxxx --mobiles 1111111,222222
   ```

   | 参数               | 说明                                                         |
   | ------------------ | ------------------------------------------------------------ |
   | alert_name(必填)   | 告警名称, 建议以单引号限定, 否则遇到空格会报错               |
   | alert_msg(必填)    | 告警信息, 建议以单引号限定, 否则遇到空格会报错               |
   | access_token(选填) | 自定义机器人AccessToken, 与脚本参数webhook_access_token不能同时为空 |
   | secret(选填)       | 加签密钥, 如有加签, 与脚本参数webhook_secret不能同时为空     |
   | mobiles(选填)      | 手机号, 多手机以,(逗号)分割                                  |

## 3.2. 工作通知

### 3.2.1. 效果

![image-20240416165906168](https://s3.johnwick.app/img/windows/2024/04/16/202404161659300.png)

### 3.2.2. 参数说明

1. AgentId

   原企业内部应用AgentId

2. ClientID

   原 AppKey 和 SuiteKey)

3. ClientSecret

   原 AppSecret 和 SuiteSecret

### 3.2.3. 如何获取

> 官方描述文档：https://open.dingtalk.com/document/orgapp/overview-of-development-process

1. 创建一个应用并发布上线，详细参考官方描述文档，此处不做介绍

2. 在应用后台https://open-dev.dingtalk.com/fe/app#/corp/app，找到发布的应用，在【凭证与基础信息】栏找到相关参数信息

   ![image-20240416170733660](https://s3.johnwick.app/img/windows/2024/04/16/202404161707795.png)

### 3.2.4. 插件使用

#### 3.2.4.1. Yottaweb插件

1. 使用编辑器打开脚本，根据3.2.3章节获取到的相关信息填入脚本

   ![image-20240416171237145](https://s3.johnwick.app/img/windows/2024/04/16/202404161712278.png)

2. 监控告警推送引用插件相关参数配置

   **接收人手机号：**可从平台已有用户信息引入也可手动输入手机号

   ![image-20240416171314200](https://s3.johnwick.app/img/windows/2024/04/16/202404161713319.png)

#### 3.2.4.2. Manager插件

1. 根据1.4.2章节上传插件并将插件功能【开启】

2. 根据3.2.3章节获取的相关参数填入到配置项

   ![image-20240416171503321](https://s3.johnwick.app/img/windows/2024/04/16/202404161715474.png)

3. 最后根据1.4.2章节针对相关告警规则进行绑定推送渠道

   **@指定接收人[手机号, 多个以,号分割]：**不可省略，必须填入接收人手机号

   ![image-20240416171547841](https://s3.johnwick.app/img/windows/2024/04/16/202404161715972.png)

#### 3.2.4.3. Soar插件

1. 使用编辑器打开脚本，根据3.2.3章节获取到的相关信息填入脚本

   ![image-20240424103314117](https://s3.johnwick.app/img/windows/2024/04/24/202404241033222.png)

2. 按照1.4.3章节上传并配置算子

3. 脚本执行说明

   以下是脚本使用样例

   ```shell
   /opt/rizhiyi/python/bin/python /data/rizhiyi/soar/python/DingTalkJobNoticeSoar.py --alert_name '告警测试' --alert_msg '测试' --mobiles 1111111,222222
   ```

   | 参数             | 说明                                           |
   | ---------------- | ---------------------------------------------- |
   | alert_name(必填) | 告警名称, 建议以单引号限定, 否则遇到空格会报错 |
   | alert_msg(必填)  | 告警信息, 建议以单引号限定, 否则遇到空格会报错 |
   | mobiles(选填)    | 手机号, 多手机以,(逗号)分割                    |

# 4. 飞书

| 告警类型     | 描述                                                         | 官方文档                                                     |
| ------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| 自定义机器人 | 通过 Webhook 接入自定义服务，使用自定义机器人，支持能在当前群聊中使用的机器人 | https://open.feishu.cn/document/client-docs/bot-v3/bot-overview |
| 工作通知     | 以某个应用的名义推送到员工的工作通知消息，例如生日祝福、入职提醒等 | https://open.feishu.cn/document/client-docs/bot-v3/bot-overview |

## 4.1. 自定义机器人

### 4.1.1. 效果

![image-20240412174537357](https://s3.johnwick.app/img/windows/2024/04/12/image-20240412174537357.png)
### 4.1.2. 参数说明

1. WebhookToken

   机器人token，通过该token可以实现推送消息到机器人

2. 签名校验

   机器人的安全设置，该参数用以对当前推送的数据进行加签用以后台校验数据推送的有效性

### 4.1.3. 如何获取

> 官方文档：https://open.feishu.cn/document/client-docs/bot-v3/add-custom-bot

1. 邀请自定义机器人进群。

   a. 进入目标群组，在群组右上角点击更多按钮，并点击 **设置**。

   ![img](https://sf3-cn.feishucdn.com/obj/open-platform-opendoc/0704e334f450754076202b574be3dff1_kQEGlTTPj7.png?height=1242&lazyload=true&maxWidth=600&width=1824)

   b. 在右侧 **设置** 界面，点击 **群机器人**。

   ![img](https://sf3-cn.feishucdn.com/obj/open-platform-opendoc/8ddf497adeeb5e42d4faf91a0955649f_3PaZ3J9uwz.png?height=1240&lazyload=true&maxWidth=600&width=1810)

   c. 在 **群机器人** 界面点击 **添加机器人**。

   d. 在 **添加机器人** 对话框，找到并点击 **自定义机器人**。

   ![img](https://sf3-cn.feishucdn.com/obj/open-platform-opendoc/a9f4e16ea91fd15a272b0ba926e4c2fd_k0hrjUtKqR.png?height=1106&lazyload=true&maxWidth=600&width=1652)

   e. 设置自定义机器人的头像、名称与描述，并点击 **添加**。

   ![img](https://sf3-cn.feishucdn.com/obj/open-platform-opendoc/71f2339063c24779f13a9710bb4a0f6e_cVn7wSbnq2.png?height=1144&lazyload=true&maxWidth=600&width=1656)

2. 获取自定义机器人的 webhook 地址，并点击 **完成**。

   机器人对应的 **webhook 地址** 格式如下：

   ```
   https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxxxxxxxxxxx
   ```

   xxxxxxxxxxxxxxxxx则是webhook token

3. 签名校验

   机器人安全设置中存在【签名校验】的方式推送消息，若客户现场设计该配置则同样需要拿到该信息

   ![img](https://sf3-cn.feishucdn.com/obj/open-platform-opendoc/39d1233fc3276c71f6fce9707abf05c9_YdZveIV7gm.png?height=1134&lazyload=true&maxWidth=600&width=1654)

### 4.1.4. 插件使用

#### 4.1.4.1. Yottaweb插件

1. 使用编辑器打开脚本，根据4.1.3章节获取到的相关信息填入脚本，webhook_token以及webhook_secret参数仅用于当监控项中未配置时则采用该参数进行推送，属于兜底策略

   ![image-20240417094631912](https://s3.johnwick.app/img/windows/2024/04/17/202404170946001.png)

2. 根据1.4.1章节上传插件并添加插件到相关监控

3. 监控告警推送引用插件相关参数配置

   **(可选)自定义机器人WebhookToken**：机器人token，获取方式参考4.1.3章节；由于监控可能涉及多个部门，且每个部门都有相关钉钉群，该配置用以覆盖该情况，注意只能填写一个token，不填写则默认使用脚本参数配置的token

   **(可选)签名校验**：安全设置中的加签秘钥，获取方式参考4.1.3章节，若客户现场不涉及无需填写

   ![image-20240417094648929](https://s3.johnwick.app/img/windows/2024/04/17/202404170946013.png)

#### 4.1.4.2. Manager插件

1. 根据1.4.2章节上传插件并将插件功能【开启】

2. 根据3.1.3章节获取的相关参数填入到配置项

   **群机器人Webhook的Token：**机器人token，获取方式参考4.1.3章节

   **(可选)签名校验**：安全设置中的加签秘钥，获取方式参考4.1.3章节，若客户现场不涉及无需填写

![image-20240416174203886](https://s3.johnwick.app/img/windows/2024/04/16/202404161742053.png)

3. 最后根据1.4.2章节针对相关告警规则进行绑定推送渠道即可，无需其他配置

#### 4.1.4.3. Soar插件

1. 使用编辑器打开脚本，根据4.1.3章节获取到的相关信息填入脚本，webhook_token以及webhook_secret参数仅用于当监控项中未配置时则采用该参数进行推送，属于兜底策略

   ![image-20240424103841884](https://s3.johnwick.app/img/windows/2024/04/24/202404241038000.png)

2. 按照1.4.3章节上传并配置算子

3. 脚本执行说明

   以下是脚本使用样例

   ```shell
   /opt/rizhiyi/python/bin/python /data/rizhiyi/soar/python/FeishuWebhookSoar.py --alert_name '告警测试' --alert_msg '测试' --webhoook_token xxxx --sign_secret xxxx
   ```

   | 参数                 | 说明                                                         |
   | -------------------- | ------------------------------------------------------------ |
   | alert_name(必填)     | 告警名称, 建议以单引号限定, 否则遇到空格会报错               |
   | alert_msg(必填)      | 告警信息, 建议以单引号限定, 否则遇到空格会报错               |
   | webhoook_token(选填) | 自定义机器人AccessToken, 与脚本参数webhook_token不能同时为空 |
   | sign_secret(选填)    | 签名校验, 如有签名, 与脚本参数webhook_secret不能同时为空     |

## 4.2. 应用机器人

### 4.2.1. 效果

![image-20240412185018465](https://s3.johnwick.app/img/windows/2024/04/12/image-20240412185018465.png)

### 4.2.2. 参数说明

1. AppId

   应用id

2. AppSecret

   应用秘钥

### 4.2.3. 如何获取

1. 创建应用并赋予相关权限，参考官方文档：https://open.feishu.cn/document/home/introduction-to-custom-app-development/self-built-application-development-process

2. 登录[开发者后台](https://open.feishu.cn/app/)，选择指定的自建应用。

3. 在 **基础信息** > **凭证与基础信息** 页面，获取应用凭证 **App ID** 和 **App Secret**。

   ![img](https://sf3-cn.feishucdn.com/obj/open-platform-opendoc/dea746f60b87470418f560b0bf4b3d20_yqW2dd4uel.png?height=794&lazyload=true&maxWidth=600&width=2882)

### 4.2.4. 插件使用

#### 4.2.4.1. Yottaweb插件

1. 使用编辑器打开脚本，根据3.2.3章节获取到的相关信息填入脚本

   ![image-20240416175614017](https://s3.johnwick.app/img/windows/2024/04/16/202404161756155.png)

2. 监控告警推送引用插件相关参数配置

   **(二选一)用户邮箱：**可从平台已有用户邮箱引入也可手动输入邮箱

   **(二选一)手机号：**可从平台已有用户手机号引入也可手动输入手机号

![image-20240416175539688](https://s3.johnwick.app/img/windows/2024/04/16/202404161755833.png)

#### 4.2.4.2. Manager插件

1. 根据1.4.2章节上传插件并将插件功能【开启】

2. 根据4.2.3章节获取的相关参数填入到配置项

   ![image-20240416180050496](https://s3.johnwick.app/img/windows/2024/04/16/202404161800662.png)

3. 最后根据1.4.2章节针对相关告警规则进行绑定推送渠道

   可填入手机号或者邮箱用以推送到指定接收人

   ![image-20240416180209077](https://s3.johnwick.app/img/windows/2024/04/16/202404161802203.png)

#### 4.2.4.3. Soar插件

1. 使用编辑器打开脚本，根据3.2.3章节获取到的相关信息填入脚本

   ![image-20240424104304223](https://s3.johnwick.app/img/windows/2024/04/24/202404241043336.png)

2. 按照1.4.3章节上传并配置算子

3. 脚本执行说明

   以下是脚本使用样例

   ```shell
   /opt/rizhiyi/python/bin/python /data/rizhiyi/soar/python/FeishuApplicationSoar.py --alert_name '告警测试' --alert_msg '测试' --mobiles 1111111,222222 --emails xxx@qq.com
   ```

   | 参数             | 说明                                                  |
   | ---------------- | ----------------------------------------------------- |
   | alert_name(必填) | 告警名称, 建议以单引号限定, 否则遇到空格会报错        |
   | alert_msg(必填)  | 告警信息, 建议以单引号限定, 否则遇到空格会报错        |
   | mobiles(选填)    | 手机号, 多手机以,(逗号)分割，与emails参数不能同时为空 |
   | emails(选填)     | 邮箱, 多邮箱以,(逗号)分割，与mobiles参数不能同时为空  |

# 5. 插件获取

| 人员类型 | URL                                                          |
| -------- | ------------------------------------------------------------ |
| 日志易   | http://192.168.40.123/chen.zhangpeng/alarm_plugin/-/tree/master/%E9%80%9A%E7%94%A8%E6%8F%92%E4%BB%B6 |
| 合作伙伴 | https://github.com/rizhiyi/alarm_plugins                     |

