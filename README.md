# Bus_Notification
demo project  

## Goal
Send a notification when bus arrives at 3 to 5 stops ahead target station.

# To do

- [x]  Bus API
- [ ]  搞懂公車路線
- [x]  Cloud maching
- [ ]  Event queue
- [ ]  Notification queue
- [ ]  先做MVP
---
- [ ]  Mock API
- [ ]  Notification system
- [ ]  Log and status report
- [ ]  Multiple user
- [ ]  Stress test
- [ ]  Visualize
- [ ]  Something extra(?)


# System diagram
```
+-----------+            +---------------+          +----------------------+
|           |            |               |          |                      |
|  TDX API  |    <---    | Python Script |   --->   | Telegram / something |
|           |   polling  |               |          |                      |
+-----------+            +---------------+          +----------------------+

```
# Progress

完成API剖析&local建表


# Thought
設計一個雙向結構來記錄站點關係?

> 以往返方向分別記錄站次就好 API有提供行進方向 問題可以被簡化  

用地理圍欄作為觸發通知依據? X

> 雖然有GPS資料 但不要好了 3~5站的距離不算遠 但不能排除S型遊走在分界邊緣時的多次觸發  
更何況API提供的到站預估時間可能比較直觀  

使用者自訂車號、路線的狀況

> 我們大概需要"車號/方向/時間(?)"  
目前(2023/12)台北市營運中的路線大約280條  
還在稍微建個表可以處理的範圍  
使用者介面要想想看怎麼比較方便  

 "多人使用" 的狀況

> 考慮到現實層面 70(人)*280(路線)*2(雙向)*3(重疊通知數)*20%(實際轉換率)  
好像不適合這樣算 先放一邊處理重要的事

處理邊界條件  
如果輸入的站點是起始站? 沒有前3~5站的狀況怎麼辦

> 目前先注重在符合條件的站點  
我們還是可以用發車時間+平均到站時間來給出到站提醒

> Event driven
使用event queue / notification queue 來增加擴充性

# Relative work
TDX運輸資料流通服務  
https://tdx.transportdata.tw/  

公車API動態資料使用注意事項  
https://ptxmotc.gitbooks.io/ptx-api-documentation/content/api-zi-liao-shi-yong-zhu-yi-shi-xiang/buslive.html  

路線簡圖  
https://ebus.gov.taipei/MapOverview?nid=0100067200

大台北公車  
https://ebus.gov.taipei/EBus/VsSimpleMap?routeid=0100067200&gb=1#
