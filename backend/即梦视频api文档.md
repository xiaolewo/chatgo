即梦3 视频生成
POST
{{BASE_URL}}/jimeng/submit/videos
最后修改时间：
29 天前
请求参数
Header 参数
Content-Type
string
必需
示例值:
application/json
Authorization
string
可选
默认值:
Bearer {{YOUR_API_KEY}}
Body 参数
application/json
prompt
string
必需
image_url
string
图生视频必带
可选
duration
integer
枚举值 5, 10
必需
aspect_ratio
string
必需
枚举值 "1:1", "21:9", "16:9", "9:16", "4:3", "3:4"
cfg_scale
number
0.5
必需
示例
{
"prompt": "string",
"image_url": "string",
"duration": 0,
"aspect_ratio": "string",
"cfg_scale": 0
}
示例代码
http.client
Requests
import http.client
import json

conn = http.client.HTTPSConnection("{{BASE_URL}}")
payload = json.dumps({
"prompt": "string",
"image_url": "string",
"duration": 0,
"aspect_ratio": "string",
"cfg_scale": 0
})
headers = {
'Authorization': 'Bearer {{YOUR_API_KEY}}',
'Content-Type': 'application/json'
}
conn.request("POST", "/jimeng/submit/videos", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))
返回响应
🟢200
成功
application/json
object

{0}
示例
{
"code": "success",
"message": "",
"data": "4596183399426" // 任务ID
}
