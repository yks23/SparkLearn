## Avoiding collisions (more)

idea: sender "reserves" channel use for data frames using small reservation packets

■ sender first transmits small request-to-send (RTS) packet to BS using CSMA

*  RTSs may still collide with each other (but they're short)
* ■ BS broadcasts clear-to-send CTS in response to RTS
* ■ CTS heard by all nodes
*  sender transmits data frame
*  other stations defer transmissions

<details>
<summary>📚 知识卡片: Collision Avoidance</summary>

**解释**: Techniques to prevent data packets from overlapping and being lost in networks.

**示例**: Using RTS/CTS handshake in Wi-Fi.

**有趣事实**: Inspired by traffic signals preventing car crashes.
</details>

<details>
<summary>📚 知识卡片: Request-to-Send (RTS)</summary>

**解释**: A small control packet sent to request permission to transmit data.

**示例**: Like raising your hand before speaking in a meeting.

**有趣事实**: Named by borrowing aviation terminology (Request to Send).
</details>

<details>
<summary>📚 知识卡片: Clear-to-Send (CTS)</summary>

**解释**: A response packet from the receiver allowing the sender to transmit data.

**示例**: Like getting approval to proceed with a project.

**有趣事实**: Acts as a virtual "green light" for data transmission.
</details>

<details>
<summary>📚 知识卡片: CSMA (Carrier Sense Multiple Access)</summary>

**解释**: Protocol where devices listen before transmitting to avoid collisions.

**示例**: Like checking both ways before crossing the street.

**有趣事实**: Used in early Ethernet networks (1970s).
</details>

---

### 难度评分
- **第一段**: ★★☆☆☆  
  （介绍核心概念，术语较基础）

- **第二段**: ★★★☆☆  
  （涉及RTS/CTS握手机制，需理解CSMA和广播原理）

---

<details>
<summary>📚 知识扩展</summary>

**RTS/CTS握手机制背景**:  
在Wi-Fi等无线环境中，设备通过发送RTS（请求发送）包预约信道。接收方（如基站BS）回复CTS（清除发送）包，告知其他设备“该信道已被占用”。这一机制减少了数据帧碰撞的概率，但RTS/CTS本身仍可能冲突（因它们更短，冲突损失更小）。

**相关概念**:  
- **隐藏终端问题**: 两个无法直接通信的设备通过同一基站传输时可能产生干扰。  
- **信道预留**: RTS/CTS通过“预约”信道时间，降低长数据帧冲突风险。

**应用场景**:  
用于高密度无线环境（如会议室Wi-Fi），或物联网设备密集的场景。
</details>

<details>
<summary>🎓 易化学习</summary>

想象一下教室场景：  
1. **举手提问**: 学生A（发送方）先举手（发送RTS），向老师（基站BS）请求发言。  
2. **老师允许**: 老师点头并宣布“允许发言”（发送CTS），其他学生必须安静（defer transmissions）。  
3. **发言**: 学生A开始回答问题（发送数据帧），其他学生保持沉默。  

**为什么有效**?  
- RTS/CTS像“预约”发言机会，减少多人同时说话的混乱。  
- 即使举手动作（RTS）可能撞车（冲突），但耗时短，影响小。
</details>