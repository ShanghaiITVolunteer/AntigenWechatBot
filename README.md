# AntigenWechatBot 

AntigenWechatBot is a wechat bot that aims enpowering the primary-level government workers. It is designed during the pandemic in Shanghai, and contains different functions that can automate basic jobs of the primary-level government workers, for example, antigen information collection, pandemic information delivery and group purchase announcement.

AntigenWechatBot是一个用于为基层干部（居委会干部）赋能的微信机器人。我们在上海疫情期间开始开发这款软件。它包含但不限于以下功能：抗原数据采集，疫情信息分发和团购信息宣传。

## Story:

Currently in our neighbourhood, the number of primary-level government workers are limited, but too many neighbours to serve. Because of the lack of usage of information and computer technologies, their work are also unefficient. As a primary-level worker as example, during this pandemic, he should organize group purchase and ask for voluteers to help move the goods to every family in this community, deliver antigen testings and collect antigen testing results, organize nucleic acid test, send out information in every single wechat group for each building (due to the number limit of wechat group). Many of these things are repeated, wasting their time in those simple affairs, and doesn't have time to think about higher-level issues, and doesn't have enough backup for potential crisis. 

以我们小区为例，我们的基层工作者和居委会人员人数非常有限，但是却要服务大量的居民。与此同时，由于信息服务和计算机技术在基层工作中的缺失，相关工作人员的工作效率却又比较低下。以一个基层工作者的工作为例，他需要组织团购并组织志愿者分发团购货品，分发抗原并统计抗原结果，组织核酸检测，在每个楼栋群里分发小区信息（检测、团购、疫情状况），且因为微信群人数上限为500人，远小于一个小区的总人数，故他们有大量的群聊需要管理。这些繁杂而重复的事务浪费了他们大量的时间，让他们陷在琐碎中不能自拔，而没有时间思考更重要的事，也对未来可能出现的危机缺乏冗余。

Computer and information technologies can help this a lot, as most of the things are repeatable, and already based on smart devices. With the help of wechat bot, Users have little learning cost and can solve the majority of the problems mentioned above.

幸运的是，信息技术可以帮助解决上述可重复的问题。居民们已有的生活习惯已经基于智能设备，只要使用微信机器人，用户可以在极低的学习成本下摆脱大量重复工作。

## Demand:
An automatic wechat bot that   

    1. Deliver pandemic news and group purchase notice                         分发疫情信息以及团购信息  
    
    2. Remind neighbours to do antigen testing and collect antigen results     提醒居民做抗原测试及采集抗原测试结果  
    

## Plan for Deliver news:
### Phase 1:
An wechat bot that can deliver news to all the related inhabitants, where the worker send a information to the bot in a private chat, and the bot will deliver this message to all the wechat groups for each building. Information includes nucleic acid test arrangement, volunteer recruitment and group purchase notice. Daily pandemic newsletter should also be included.

第一阶段的微信机器人将用于发送信息给所有居民。居委会工作人员仅需要将需要转发的信息私聊发送给微信机器人，微信机器人会将信息分发给每一个楼栋群。分发的信息包括但不限于核酸采样通知，志愿者招募以及团购信息。疫情周报也需要被囊括其中。

```mermaid
graph LR
  subgraph 楼栋群
  楼栋A
  楼栋B
  楼栋C
  end
  居委会 == 发送信息 ==> 微信机器人
  微信机器人 == 传达信息 ==> 楼栋A
  微信机器人 == 传达信息 ==> 楼栋B
  微信机器人 == 传达信息 ==> 楼栋C
```

# Phase1.5:
Integrated ASR function.
This is mainly for special users, such as elderly users, who can generally only send voice (still in Shanghainese)

增加ASR功能用于服务特殊用户，诸如老人或只能发送语音信息的人（上海话）

### Phase 2:
Add very simple question-answer bot. In this phase, we do not want NLP technology include, but set some special keyword, like daily-report, so that the user can type the keyword in the chat box and the bot will automatically reply with the answer.

一个简单的问答机器人，用于帮人快速定位错过的信息。用户可以输入给定的关键词，如疫情日报，并得到相应的预存的回答。用户仅需在所有注册的楼栋群内发送关键词即可获得答案。此阶段不支持模糊查询。

```mermaid
graph LR
  居委会 == 设置关键词及答案 ==> 微信机器人
  居民 == 聊天框内发送关键词 ==> 微信机器人
  微信机器人 == 输出答案 ==> 居民
```

### Phase 2.1:
Should be done in parallel as phase 2. Daily report auto-generate program.

应和第二阶段同时开发：日报自动生成器。采集居委会在第一阶段中就会发送的信息，自动生成日报。

```mermaid
graph LR
  subgraph 楼栋群
  楼栋A
  楼栋B
  楼栋C
  end
  居委会 == 发送信息 ==> 微信机器人
  微信机器人 == 存储信息并生成日报 ==> 日报
  微信机器人 == 传达信息 ==> 楼栋A
  微信机器人 == 传达信息 ==> 楼栋B
  微信机器人 == 传达信息 ==> 楼栋C
```

### Phase 3.1:
Add all group purchase information into the message-deliver bot.

团购信息整合入微信机器人。此处为工地，暂无满意的系统设计。

### Phase 3.2:
Question-answering bot uses NLP technology so that users do not need to remember the keywords and more questions can be answered. Involve answer database so that workers do not need to answer same questions from different sources multiple times.

NLP技术支持的微信问答机器人，可以存储居委会对已有的问题的回答，分析问题的相似性并对相似的问题给出回到。此处为工地，暂无满意的系统设计。

## Plan for antigen:
### Phase 1:
Given a time period of antigen self-testing, the bot will send message to the chat to remind people to do the antigen testing. Every user can upload images, and the bot will collect the image and generate a file after every room has its own image. When someone doesn't finish the antigen, the bot will automatically remind the user to upload the testing result every several minutes. An administrator should be elected in each building that responsible for checking the file and report the result of the file to the primary-level government workers.

给定一段抗原测试时间，微信机器人会提醒人们去做抗原测试。每个用户可以自动提交图片，然后当所有人提交完毕后，机器人将整理好图片顺序并生成一份总结文档。若有人临期仍然没有完成，机器人将每隔一段时间进行提醒。每栋楼需选出一个代表检查文档中是否全阴，并将结果提交给居委会。

```mermaid
sequenceDiagram
    participant a as 居委会
    participant b as 微信机器人
    participant c as 居民
    participant d as 楼组长
    a->>+b: 发送测试安排
    b->>+c: 提醒测试
    c-->>-b: 发送抗原图片
    b->>+d: 发送全楼抗原文档
    d-->>-a: 审核并提交楼栋抗原结果
```

PS. Advantage is that the administrator will no longer need to check if everyone has uploaded the image or not, nor worrying about the unsorted room numbers. It will reduce the administrator's work from $O(N^2)$ to $O(N)$.

PS. 这个项目的优势在于楼组长将不必要看是否每个人都已经完成抗原检测，并且也不会受困于错序的居民上传顺序。楼组长的工作时间将从$O(N^2)$降至$O(N)$.
    
### Phase 2:
Add Computer Vision technologies into the wechat bot that can automatically do the job of the building administrator. In this case, no worker is needed in this system and all the process can be done automatically.

添加计算机视觉技术，可以自动检测抗原结果，从此整个抗原检测结果检测无需任何人工加入。

```mermaid
sequenceDiagram
    participant a as 居委会
    participant b as 微信机器人
    participant c as 居民
    a->>+b: 发送测试安排
    b->>+c: 提醒测试
    c-->>-b: 发送抗原图片
    b->>-a: 自动识别并提交抗原结果
```

## Something more to mention...
This automatic bot is not aimed to replace the warm connection between primary-level workers and inhabitants in the community. On the contrary, the bot is aimed to help reduce the waste of time on repeat affairs, so that primary-level workers can have more time to figure out the high-level demand of the inhabitants, and finally better serve the people. We would like to enhance the connection between primary-level government workers and the people, so that help Shanghai to have joint effort to overcome the pandemic!

还有一些想说的话。这个bot的目的不是用冷冰冰的机器来取代基层工作者和人民之间的联系。与之相反，我们旨在将基层工作者从重复、繁杂、琐碎的工作中解放出来，让他们更有动力去深入了解人民的高层次需求，以建立更温暖更友善的联系，并更好的服务于人民，建立鱼水情。我相信，只有增强这种联系，我们上海才能共同努力，一起克服这如洪水猛兽般的疫情！
