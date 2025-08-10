生成 PPT 相关接口
AI PPT - V2
创建任务
接口说明： 调用此接口可获得一个 任务 ID，即开启了一个生成 PPT 的任务，后续不管是生成大纲内容还是修改大纲内容都需要此任务 ID。

post
https://open.docmee.cn/api/ppt/v2/createTask

multipart/form-data

参数 类型 是否必传 说明
type 1|2|3|4|5|6|7 是 类型：1.智能生成（主题、要求）2.上传文件生成 3.上传思维导图生成 4.通过 word 精准转 ppt 5.通过网页链接生成 6.粘贴文本内容生成
7.Markdown 大纲生成
content String 否 内容：
type=1 用户输入主题或要求（不超过 1000 字符）
type=2、4 不传
type=3 幕布等分享链接
type=5 网页链接地址（http/https）
type=6 粘贴文本内容（不超过 20000 字符）
type=7 大纲内容（markdown）
file File[] 否 文件列表（文件数不超过 5 个，总大小不超过 50M）：
type=1 上传参考文件（非必传，支持多个）
type=2 上传文件（支持多个）
type=3 上传思维导图（xmind/mm/md）（仅支持一个）
type=4 上传 word 文件（仅支持一个）
type=5、6、7 不传

支持格式：doc/docx/pdf/ppt/pptx/txt/md/xls/xlsx/csv/html/epub/mobi/xmind/mm
响应：

{
"data": {
"id": "xxx" // 任务ID
},
"code": 0,
"message": "操作成功"
}

获取生成选项
接口说明： 调用此接口来获得调用生成大纲内容需要使用的相关选项。

get
https://open.docmee.cn/api/ppt/v2/options

该接口支持国际化，URL 携带 lang 参数指定。

响应

{
"data": {
"lang": [
// 语种
{ "name": "简体中文", "value": "zh" },
{ "name": "繁體中文", "value": "zh-Hant" },
{ "name": "English", "value": "en" },
{ "name": "日本語", "value": "ja" },
{ "name": "한국어", "value": "ko" },
{ "name": "Français", "value": "fr" },
{ "name": "Русский", "value": "ru" },
{ "name": "العربية", "value": "ar" },
{ "name": "Deutsch", "value": "de" },
{ "name": "Español", "value": "es" },
{ "name": "Italiano", "value": "it" },
{ "name": "Português", "value": "pt" }
],
"scene": [
// 场景
{ "name": "通用场景", "value": "通用场景" },
{ "name": "教学课件", "value": "教学课件" },
{ "name": "工作总结", "value": "工作总结" },
{ "name": "工作计划", "value": "工作计划" },
{ "name": "项目汇报", "value": "项目汇报" },
{ "name": "解决方案", "value": "解决方案" },
{ "name": "研究报告", "value": "研究报告" },
{ "name": "会议材料", "value": "会议材料" },
{ "name": "产品介绍", "value": "产品介绍" },
{ "name": "公司介绍", "value": "公司介绍" },
{ "name": "商业计划书", "value": "商业计划书" },
{ "name": "科普宣传", "value": "科普宣传" },
{ "name": "公众演讲", "value": "公众演讲" }
],
"audience": [
// 受众
{ "name": "大众", "value": "大众" },
{ "name": "学生", "value": "学生" },
{ "name": "老师", "value": "老师" },
{ "name": "上级领导", "value": "上级领导" },
{ "name": "下属", "value": "下属" },
{ "name": "面试官", "value": "面试官" },
{ "name": "同事", "value": "同事" }
]
},
"code": 0,
"message": "ok"
}

生成大纲内容
接口说明： 生成当前任务的大纲及内容

post
https://open.docmee.cn/api/ppt/v2/generateContent

参数

{
"id": "xxx", // 任务ID
"stream": true, // 是否流式（默认 true）
"length": "medium", // 篇幅长度：short/medium/long => 10-15页/20-30页/25-35页
"scene": null, // 演示场景：通用场景、教学课件、工作总结、工作计划、项目汇报、解决方案、研究报告、会议材料、产品介绍、公司介绍、商业计划书、科普宣传、公众演讲 等任意场景类型。
"audience": null, // 受众：大众、学生、老师、上级领导、下属、面试官、同事 等任意受众类型。
"lang": null, // 语言: zh/zh-Hant/en/ja/ko/ar/de/fr/it/pt/es/ru
"prompt": null // 用户要求（小于50字）
}

特别提醒

参数prompt只会在 创建的任务类型为 1 (智能生成), 2 (上传文件生成), 5 (通过网页链接生成), 6 (粘贴文本内容生成) 这些类型时生效，其他类型会忽略该字段

流式响应 event-stream

{ "text": "#", "status": 3 }

{ "text": " ", "status": 3 }

{ "text": "主题", "status": 3 }

...

{
"text": "",
"status": 4,
"result": { // 最终markdown结构树
"level": 1,
"name": "主题",
"children": [
{
"level": 2,
"name": "章节",
"children": [
{
"level": 3,
"name": "页面标题",
"children": [
{
"level": 4,
"name": "内容标题",
"children": [
{
"level": 0,
"name": "内容"
}
]
}
]
}
]
}
]
}
}

非流式响应（application/json）：

{
"code": 0,
"data": {
"text": "# 主题\n## 章节\n### 页面标题\n#### 内容标题\n- 内容", // markdown 文本
"result": {
// markdown 结构树
"level": 1,
"name": "主题",
"children": [
{
"level": 2,
"name": "章节",
"children": [
{
"level": 3,
"name": "页面标题",
"children": [
{
"level": 4,
"name": "内容标题",
"children": [
{
"level": 0,
"name": "内容"
}
]
}
]
}
]
}
]
}
},
"message": "ok"
}

修改大纲内容
接口说明： 根据用户指令（question）修改大纲内容。

post
https://open.docmee.cn/api/ppt/v2/updateContent

参数

{
"id": "xxx", // 任务ID
"stream": true, // 是否流式（默认 true）
"markdown": "# 主题\n## 章节\n### 页面标题\n#### 内容标题\n- 内容", // 大纲内容markdown
"question": null // 用户修改建议
}

响应 event-stream 或 application/json，结构同生成大纲内容

生成 PPT
接口说明： 根据 markdown 格式的 PPT 大纲与内容生成 PPT 作品。

post
https://open.docmee.cn/api/ppt/v2/generatePptx

参数

{
"id": "xxx", // 任务ID
"templateId": "xxx", // 模板ID（调用模板接口获取）
"markdown": "# 主题\n## 章节\n### 页面标题\n#### 内容标题\n- 内容" // 大纲内容markdown
}

响应

{
"code": 0,
"data": {
"pptInfo": {
// ppt信息
"id": "xxx", // ppt id
"subject": "xxx", // 主题
"coverUrl": "https://xxx.png", // 封面
"templateId": "xxx", // 模板ID
"pptxProperty": "xxx", // PPT数据结构（json gzip base64）
"userId": "xxx", // 用户ID
"userName": "xxx", // 用户名称
"companyId": 1000,
"updateTime": null,
"createTime": "2024-01-01 10:00:00"
}
},
"message": "操作成功"
}
