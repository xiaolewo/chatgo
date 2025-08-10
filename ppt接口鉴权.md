接口鉴权
创建 API Token 接口用于生成调用鉴权 Token，支持限制生成次数与数据隔离，通过 Header 或 URL 拼接 Token 实现鉴权。

创建接口 token
post
https://open.docmee.cn/api/user/createApiToken

请求 header

Api-Key 在开放平台获取 获取 API-KEY

请求 body

{
// 用户ID（自定义用户ID，非必填，建议不超过32位字符串）
// 第三方用户ID，不同uid创建的token数据会相互隔离，主要用于数据隔离
"uid": null,
// 限制 token 最大生成PPT次数（数字，为空则不限制，为0时不允许生成PPT，大于0时限制生成PPT次数）
// UI iframe 接入时强烈建议传 limit 参数，避免 token 泄露照成损失！
"limit": null,
// 过期时间，单位：小时
// 默认两小时过期，最大可设置为48小时
"timeOfHours": 2
}

响应 body

{
"data": {
"token": "sk_xxx", // token (调用api接口鉴权用，请求头传token)
"expireTime": 7200 // 过期时间（秒）
},
"code": 0,
"message": "操作成功"
}

请求示例

curl -X POST --location 'https://open.docmee.cn/api/user/createApiToken' \
--header 'Content-Type: application/json' \
--header 'Api-Key: xxx' \
--data '{"uid": "xxx","limit": 10}'

注意：该接口请在服务端调用，同一个 uid 创建 token 时，之前通过该 uid 创建的 token 会在 10 秒内过期

场景说明：在 UI 集成中，为防止 token 滥用，limit 参数可以让第三方集成商维护自己平台用户的使用次数，未注册用户访问时可以创建 limit 为 0 的 token ，用户能使用但生成不了 PPT，UI 中监听次数用完的事件指导用户登录，登录用户访问时可以根据系统 vip 级别限制和维护系统用户 limit 次数

API 接口鉴权
请求 Header

token 通过 createApiToken 接口创建的 token，如果是服务端调用也可直接使用 API-KEY 作为 token

接口请求示例

curl --location 'https://open.docmee.cn/api/ppt/xxx' \ --header 'token: xxx'

封面图片资源访问，需要在 url 上拼接 ?token=xxx
