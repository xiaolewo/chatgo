获取模版
获取模板过滤选项
接口说明： 获取查询模版的过滤选项

get
https://open.docmee.cn/api/ppt/template/options

响应

{
"data": {
"category": [
// 类目筛选
{ "name": "全部", "value": "" },
{ "name": "年终总结", "value": "年终总结" },
{ "name": "教育培训", "value": "教育培训" },
{ "name": "医学医疗", "value": "医学医疗" },
{ "name": "商业计划书", "value": "商业计划书" },
{ "name": "企业介绍", "value": "企业介绍" },
{ "name": "毕业答辩", "value": "毕业答辩" },
{ "name": "营销推广", "value": "营销推广" },
{ "name": "晚会表彰", "value": "晚会表彰" },
{ "name": "个人简历", "value": "个人简历" }
],
"style": [
// 风格筛选
{ "name": "全部", "value": "" },
{ "name": "扁平简约", "value": "扁平简约" },
{ "name": "商务科技", "value": "商务科技" },
{ "name": "文艺清新", "value": "文艺清新" },
{ "name": "卡通手绘", "value": "卡通手绘" },
{ "name": "中国风", "value": "中国风" },
{ "name": "创意时尚", "value": "创意时尚" },
{ "name": "创意趣味", "value": "创意趣味" }
],
"themeColor": [
// 主题颜色筛选
{ "name": "全部", "value": "" },
{ "name": "橙色", "value": "#FA920A" },
{ "name": "蓝色", "value": "#589AFD" },
{ "name": "紫色", "value": "#7664FA" },
{ "name": "青色", "value": "#65E5EC" },
{ "name": "绿色", "value": "#61D328" },
{ "name": "黄色", "value": "#F5FD59" },
{ "name": "红色", "value": "#E05757" },
{ "name": "棕色", "value": "#8F5A0B" },
{ "name": "白色", "value": "#FFFFFF" },
{ "name": "黑色", "value": "#000000" }
]
},
"code": 0,
"message": "ok"
}

分页查询 PPT 模板
接口说明： 分页查询 PPT 模版

post
https://open.docmee.cn/api/ppt/templates

参数

{
"page": 1,
"size": 10,
"filters": {
"type": 1, // 模板类型（必传）：1系统模板、4用户自定义模板
"category": null, // 类目筛选
"style": null, // 风格筛选
"themeColor": null // 主题颜色筛选
}
}

响应

{
"code": 0,
"total": 1,
"data": [
{
"id": "xxx", // 模板ID
"type": 1, // 模板类型：1大纲完整PPT、4用户模板
"coverUrl": "https://xxx.png", // 封面（需要拼接?token=${token}访问）
"category": null, // 类目
"style": null, // 风格
"themeColor": null, // 主题颜色
"subject": "", // 主题
"num": 20, // 模板页数
"createTime": "2024-01-01 10:00:00"
}
],
"message": "操作成功"
}

请求示例

curl -X POST --location 'https://open.docmee.cn/api/ppt/templates' \
--header 'Content-Type: application/json' \
--header 'token: {token}' \
--data '{"page": 1, "size":10, "filters": { "type": 1 }}'

封面图片资源访问，需要在 url 上拼接 ?token=xxx

模板接口支持国际化，在请求 URL 上传 lang 参数，示例：/api/ppt/templates?lang=zh-CN

国际化语种支持：zh,zh-Hant,en,ja,ko,ar,de,fr,it,pt,es,ru
