## Network-layer services and protocols

##### ■ transport segment from sending to receiving host

*  sender: encapsulates segments into datagrams, passes to link layer
*  receiver:delivers segments to transport layer protocol
* ■ network layer protocols in every  *Internet device:*  hosts, routers

<details>
<summary>📚 知识卡片: Transport Segment</summary>

**解释**: 传输层数据段，是传输层协议（如TCP/UDP）处理的数据单元。

**示例**: 在HTTP请求中，传输层数据段包含应用层数据和端口信息。

**有趣事实**: 传输层数据段的封装和解封装是网络通信的核心过程之一。
</details>

<details>
<summary>📚 知识卡片: Encapsulation</summary>

**解释**: 封装是指将数据包装在协议头部的过程，以便在网络中传输。

**示例**: 传输层数据段被封装在IP数据报中，然后通过链路层传输。

**有趣事实**: 封装是网络分层模型的基础，每一层都添加自己的头部信息。
</details>

<details>
<summary>📚 知识卡片: Datagram</summary>

**解释**: 数据报是网络层的基本传输单位，包含网络层头部和上层数据。

**示例**: IP数据报是网络层传输的基本单元，包含目的地址和源地址。

**有趣事实**: 数据报是无连接的，每个数据报独立路由，可能经过不同路径。
</details>

<details>
<summary>📚 知识卡片: Link Layer</summary>

**解释**: 链路层负责物理网络中的数据帧传输，处理硬件地址和错误检测。

**示例**: 以太网帧是链路层的数据单元，包含MAC地址和数据。

**有趣事实**: 链路层协议因物理介质不同而异，如以太网、Wi-Fi等。
</details>

<details>
<summary>📚 知识卡片: Internet Device</summary>

**解释**: 互联网设备包括主机和路由器，它们都运行网络层协议。

**示例**: 个人电脑、服务器和路由器都是互联网设备。

**有趣事实**: 所有互联网设备都必须遵守网络层协议才能互相通信。
</details>

<details>
<summary>📚 知识卡片: Host</summary>

**解释**: 主机是网络中的终端设备，如电脑、手机等，能够发送和接收数据。

**示例**: 你的电脑就是一个主机，可以访问互联网。

**有趣事实**: 主机通常同时运行多个协议栈，如TCP/IP协议栈。
</details>

<details>
<summary>📚 知识卡片: Router</summary>

**解释**: 路由器是网络层设备，负责在不同网络之间转发数据包。

**示例**: 家庭路由器连接互联网和家庭网络，转发数据包。

**有趣事实**: 路由器使用路由表来决定数据包的最佳路径。
</details>

---

### 难度评分
1. **第一段**: ★★☆（中等）
2. **第二段**: ★★★（较高）
3. **第三段**: ★★★（较高）

---

<details>
<summary>📚 知识扩展</summary>

网络层协议（如IP）是互联网的核心，负责数据包的寻址和路由。所有互联网设备（主机和路由器）都必须实现网络层协议。路由器通过检查IP数据报的头部字段（如目的地址）来决定如何转发数据包，这是实现全球互联的关键机制。
</details>

<details>
<summary>🎓 易化学习</summary>

想象一下，网络层就像快递系统：  
- **数据报** = 包裹  
- **路由器** = 快递公司的分拣中心  
- **IP地址** = 收件人地址  
路由器检查包裹上的地址，决定把它送到哪个分拣中心（下一台路由器），直到最终送到收件人手里。
</details>

---

## 完整文档（含批注）

## Network-layer services and protocols

##### ■ transport segment from sending to receiving host

*  sender: encapsulates segments into datagrams, passes to link layer
*  receiver:delivers segments to transport layer protocol
* ■ network layer protocols in every  *Internet device:*  hosts, routers

<details>
<summary>📚 知识卡片: Transport Segment</summary>

**解释**: 传输层数据段，是传输层协议（如TCP/UDP）处理的数据单元。

**示例**: 在HTTP请求中，传输层数据段包含应用层数据和端口信息。

**有趣事实**: 传输层数据段的封装和解封装是网络通信的核心过程之一。
</details>

<details>
<summary>📚 知识卡片: Encapsulation</summary>

**解释**: 封装是指将数据包装在协议头部的过程，以便在网络中传输。

**示例**: 传输层数据段被封装在IP数据报中，然后通过链路层传输。

**有趣事实**: 封装是网络分层模型的基础，每一层都添加自己的头部信息。
</details>

<details>
<summary>📚 知识卡片: Datagram</summary>

**解释**: 数据报是网络层的基本传输单位，包含网络层头部和上层数据。

**示例**: IP数据报是网络层传输的基本单元，包含目的地址和源地址。

**有趣事实**: 数据报是无连接的，每个数据报独立路由，可能经过不同路径。
</details>

<details>
<summary>📚 知识卡片: Link Layer</summary>

**解释**: 链路层负责物理网络中的数据帧传输，处理硬件地址和错误检测。

**示例**: 以太网帧是链路层的数据单元，包含MAC地址和数据。

**有趣事实**: 链路层协议因物理介质不同而异，如以太网、Wi-Fi等。
</details>

<details>
<summary>📚 知识卡片: Internet Device</summary>

**解释**: 互联网设备包括主机和路由器，它们都运行网络层协议。

**示例**: 个人电脑、服务器和路由器都是互联网设备。

**有趣事实**: 所有互联网设备都必须遵守网络层协议才能互相通信。
</details>

<details>
<summary>📚 知识卡片: Host</summary>

**解释**: 主机是网络中的终端设备，如电脑、手机等，能够发送和接收数据。

**示例**: 你的电脑就是一个主机，可以访问互联网。

**有趣事实**: 主机通常同时运行多个协议栈，如TCP/IP协议栈。
</details>

<details>
<summary>📚 知识卡片: Router</summary>

**解释**: 路由器是网络层设备，负责在不同网络之间转发数据包。

**示例**: 家庭路由器连接互联网和家庭网络，转发数据包。

**有趣事实**: 路由器使用路由表来决定数据包的最佳路径。
</details>

---

### 难度评分
1. **第一段**: ★★☆（中等）
2. **第二段**: ★★★（较高）
3. **第三段**: ★★★（较高）

---

<details>
<summary>📚 知识扩展</summary>

网络层协议（如IP）是互联网的核心，负责数据包的寻址和路由。所有互联网设备（主机和路由器）都必须实现网络层协议。路由器通过检查IP数据报的头部字段（如目的地址）来决定如何转发数据包，这是实现全球互联的关键机制。
</details>

<details>
<summary>🎓 易化学习</summary>

想象一下，网络层就像快递系统：  
- **数据报** = 包裹  
- **路由器** = 快递公司的分拣中心  
- **IP地址** = 收件人地址  
路由器检查包裹上的地址，决定把它送到哪个分拣中心（下一台路由器），直到最终送到收件人手里。
</details>

---