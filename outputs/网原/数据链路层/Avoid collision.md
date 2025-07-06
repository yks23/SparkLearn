## Avoiding collisions (more)

idea: sender "reserves" channel use for data frames using small reservation packets

■ sender first transmits small request-to-send (RTS) packet to BS using CSMA

· RTSs may still collide with each other (but they're short)

* ■ BS broadcasts clear-to-send CTS in response to RTS
* ■ CTS heard by all nodes
*  sender transmits data frame
*  other stations defer transmissions

---

### 知识卡片

<details>
<summary>📚 知识卡片: CSMA</summary>

**解释**: Carrier Sense Multiple Access（载波监听多路访问），一种网络协议，节点在发送前监听信道。

**示例**: 如同多人讨论时，先听是否有人说话再发言。

**有趣事实**: CSMA是早期以太网的核心机制之一。
</details>

<details>
<summary>📚 知识卡片: RTS</summary>

**解释**: Request-to-Send（请求发送），用于预约信道的小数据包。

**示例**: 像预约座位前先询问“这里有人吗？”。

**有趣事实**: RTS机制显著减少了碰撞窗口时间。
</details>

<details>
<summary>📚 知识卡片: CTS</summary>

**解释**: Clear-to-Send（清除发送），基站对RTS的响应，表示允许发送数据。

**示例**: 相当于管理员批准预约后发放的通行证。

**有趣事实**: CTS广播确保所有节点都能获知信道状态。
</details>

<details>
<summary>📚 知识卡片: Collision</summary>

**解释**: 碰撞，指多个信号同时传输导致互相干扰的现象。

**示例**: 类似两人同时说话导致都听不清。

**有趣事实**: 以太网早期采用随机重传策略解决碰撞。
</details>

---

### 难度评分与扩展

#### 段落难度评分：★★★☆（中等）  
**高难度内容**：RTS/CTS握手机制、CSMA协议、信道预留逻辑  

<details>
<summary>📚 知识扩展</summary>

RTS/CTS机制通过两次握手（RTS→CTS→Data）减少隐藏终端问题。CSMA的核心是“先听后说”，但无法完全避免碰撞。早期以太网使用CSMA/CD（冲突检测），而无线网络因信号传播延迟改用CSMA/CA（冲突避免）。RTS包虽小，但仍可能碰撞，因此需配合随机退避算法。
</details>

<details>
<summary>🎓 易化学习</summary>

想象一下教室场景：  
1. **RTS**：学生A举手问老师：“我可以发言吗？”（短提问）  
2. **CTS**：老师点头并宣布：“允许发言！”（全班都能听到）  
3. **Data**：学生A开始讲话，其他学生保持安静。  
如果多个学生同时举手（RTS碰撞），只需快速重试，因为提问很短。
</details>