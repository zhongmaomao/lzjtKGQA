# 问答接口
```
http请求方式: GET
http://lzjtanswer.zhinengwenda-test.svc.cluster.hz:31540/api/lzjt-zhinengwenda/kgqa
```
## url条件参数
|参数|是否必须|说明|
|----|----|----|
|question|是|用户输入问句|

## 返回json参数

|参数|说明|
|----|----|
|code|状态 1:成功   0:失败|
|msg|提示信息|
|question|去除敏感词后的问题文本|
|answer|回复文本

## 示例
"http://127.0.0.1:5000/api/lzjt-zhinengwenda/kgqa?question=傻子，有哪些人驾驶过桂B11555公交车？"  [GET]
```json
{   
    "answer":"驾驶过车辆桂B11555的司机有:曾禹,郭志军",
    "code":"1",
    "msg":"查询成功",
    "question":"**，有哪些人驾驶过桂B11555公交车？"
}
```