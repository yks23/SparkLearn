## Avoiding collisions (more)

idea: sender "reserves" channel use for data frames using small reservation packets

■ sender first transmits small request-to-send (RTS) packet to BS using CSMA

*  RTSs may still collide with each other (but they're short)
* ■ BS broadcasts clear-to-send CTS in response to RTS
* ■ CTS heard by all nodes
*  sender transmits data frame
*  other stations defer transmissions

<details>
<summary>📚 知识卡片: Request-to-Send (RTS)</summary>

**解释**: RTS 是发送方发送的请求发送包，用于预留信道。

**示例**: 在无线网络中，设备发送 RTS 包以请求权限发送数据。

**有趣事实**: RTS 包通常很小，以减少碰撞的影响。
</details>

<details>
<summary>📚 知识卡片: Clear-to-Send (CTS)</summary>

**解释**: CTS 是基站（BS）对 RTS 的响应，表示允许发送数据。

**示例**: 当 BS 收到 RTS 后，会广播 CTS 包。

**有趣事实**: CTS 包被所有节点听到，确保其他节点暂停发送。
</details>

<details>
<summary>📚 知识卡片: Carrier Sense Multiple Access (CSMA)</summary>

**解释**: CSMA 是一种网络协议，设备在发送前先检测信道是否空闲。

**示例**: 设备在发送 RTS 前使用 CSMA 检测信道。

**有趣事实**: CSMA 是许多无线网络的基础机制。
</details>

<details>
<summary>📚 知识扩展</summary>

RTS/CTS 机制是无线网络中避免碰撞的重要方法。RTS 和 CTS 包都很小，即使发生碰撞，影响也较小。BS 广播 CTS 后，所有节点都会知道信道已被预留，从而避免冲突。这种机制在高负载网络中特别有效，因为它减少了数据帧碰撞的可能性。
</details>

<details>
<summary>🎓 易化学习</summary>

想象一下，RTS 就像是一个“预约”信号，发送方先发送一个简短的预约请求（RTS），基站收到后回复一个“确认”信号（CTS）。其他设备听到 CTS 后，就知道这个信道已经被占用了，不会干扰发送方的数据传输。这样，发送方就可以安心地发送数据，而不用担心碰撞了。
</details>