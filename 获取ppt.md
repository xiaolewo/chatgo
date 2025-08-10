获取 PPT
获取 PPT 列表
接口说明： 分页查询您的 PPT 作品列表

post
https://open.docmee.cn/api/ppt/listPptx

参数

{
"page": 1,
"size": 10
}

响应

{
"code": 0,
"total": 1,
"data": [
{
"id": "xxx", // ppt id
"subject": "xxx", // 主题
"coverUrl": "https://xxx.png", // 封面
"templateId": "xxx", // 模板ID
"userId": "xxx", // 用户ID
"userName": "xxx", // 用户名称
"companyId": 1000,
"updateTime": null,
"createTime": "2024-01-01 10:00:00"
}
],
"message": "操作成功"
}

请求示例

curl -X POST --location 'https://open.docmee.cn/api/ppt/listPptx' \
--header 'Content-Type: application/json' \
--header 'token: {token}' \
--data '{"page": 1, "size": 10}'

加载 PPT 数据
接口说明： 加载一个 PPT 的完整数据内容

get
https://open.docmee.cn/api/ppt/loadPptx?id=

响应

{
"code": 0,
"data": {
"pptInfo": {
// ppt信息
// 数据同 generatePptx 生成PPT 接口结构...
"id": "xxx", // ppt id
"subject": "xxx", // 主题
"coverUrl": "https://xxx.png", // 封面
"templateId": "xxx", // 模板ID
"pptxProperty": "xxx", // PPT数据结构（json 数据通过 gzip 压缩 base64 编码返回，具体解码和数据结构请见【PPT前端渲染】部分讲解）
"userId": "xxx", // 用户ID
"userName": "xxx", // 用户名称
"companyId": 1000,
"updateTime": null,
"createTime": "2024-01-01 10:00:00"
}
},
"message": "操作成功"
}

请求示例

curl -X GET --location 'https://open.docmee.cn/api/ppt/loadPptx?id=xxx' \ --header
'token: {token}'

加载 PPT 大纲内容
接口说明： 获取生成 PPT 所使用的大纲内容

post
https://open.docmee.cn/api/ppt/loadPptxMarkdown

请求

{
"id": "xxx", // pptId
"format": "tree" // 输出格式：text 大纲文本； tree 大纲结构树
}

响应

{
"code": 0,
"data": {
"markdownText": "# 主题\n## 章节标题\n### 页面标题\n#### 内容标题\n- 文本内容...", // 大纲markdown文本（当 format 为 text 时返回）
"markdownTree": {
// 大纲结构树（当 format 为 tree 时返回）
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
"name": "文本内容..."
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
"message": "操作成功"
}

请求示例

curl -X POST --location 'https://open.docmee.cn/api/ppt/loadPptxMarkdown' \
--header 'Content-Type: application/json' \
--header 'token: {token}' \
--data '{"id": "xxx", "format": "tree"}'

下载 PPT
接口说明： 下载 PPT 到本地

post
https://open.docmee.cn/api/ppt/downloadPptx

请求

{
"id": "xxx",
"refresh": false
}

响应

{
"code": 0,
"data": {
"id": "xxx",
"name": "xxx",
"subject": "xxx",
"fileUrl": "https://xxx" // 文件链接（有效期：2小时）
},
"message": "操作成功"
}

请求示例

curl -X POST --location 'https://open.docmee.cn/api/ppt/downloadPptx' \
--header 'Content-Type: application/json' \
--header 'token: {token}' \
--data '{"id":"xxx"}'

下载-智能动画 PPT
接口说明： 给 PPT 自动加上动画再下载到本地

get
https://open.docmee.cn/api/ppt/downloadWithAnimation?type=1&id=xxx

URL 请求

参数 类型 描述
type number 动画类型，1 依次展示（默认）；2 单击展示
id string PPT ID
响应（application/octet-stream）

文件数据流

请求示例

curl -X GET --location
'https://open.docmee.cn/api/ppt/downloadWithAnimation?type=1&id=xxx' \ --header
'token: {token}'

该接口会在原有的 PPT 元素对象上智能添加动画效果（元素入场动画 & 页面切场动画）

动画类型介绍：

1 依次展示，表示上一个元素动画结束后立马展示下一个元素动画

2 单击展示，表示在内容页，上一项内容展示完成后需要单击才会展示下一项内容，其他页面效果同依次展示。
