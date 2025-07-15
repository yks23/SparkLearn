# 6.1 Introduction to the Link Layer

Let's begin with some important terminology. We'll find it convenient in this chapter to refer to any device that runs a link-layer (i.e., layer 2) protocol as a **node**. Nodes include hosts, routers, switches, and WiFi access points (discussed in **Chapter 7**). We will also refer to the communication channels that connect adjacent nodes along the communication path as **links**. In order for a datagram to be transferred from source host to destination host, it must be moved over each of the *individual links* in the end-to-end path. As an example, in the company network shown at the bottom of **Figure 6.1**, consider sending a datagram from one of the wireless hosts to one of the servers. This datagram will actually pass through six links: a WiFi link between sending host and WiFi access point, an Ethernet link between the access point and a link-layer switch; a link between the link-layer switch and the router, a link between the two routers; an Ethernet link between the router and a link-layer switch; and finally an Ethernet link between the switch and the server. Over a given link, a transmitting node encapsulates the datagram in a **link-layer frame** and transmits the frame into the link.

<details>
<summary>📚 知识卡片: Node</summary>

**解释**: 运行链路层协议的设备，包括主机、路由器、交换机和WiFi接入点。

**示例**: 智能手机、电脑、路由器等都可以是节点。

**有趣事实**: 在网络中，节点就像快递站点，负责数据的中转和处理。
</details>

<details>
<summary>📚 知识卡片: Link</summary>

**解释**: 连接相邻节点的通信信道，数据包通过这些链路逐段传输。

**示例**: WiFi连接、以太网电缆、光纤等都是链路的例子。

**有趣事实**: 链路可以是有线的（如网线）或无线的（如WiFi信号）。
</details>

<details>
<summary>📚 知识卡片: Link-Layer Frame</summary>

**解释**: 数据报在链路层传输时封装的帧结构，包含源地址、目的地址和数据。

**示例**: 以太网帧是最常见的链路层帧类型。

**有趣事实**: 链路层帧类似于快递包裹，里面装着要运送的数据（数据报）。
</details>

---

In order to gain further insight into the link layer and how it relates to the network layer, let's consider a transportation analogy. Consider a travel agent who is planning a trip for a tourist traveling from Princeton, New Jersey, to Lausanne, Switzerland. The travel agent decides that it is most convenient for the tourist to take a limousine from Princeton to JFK airport, then a plane from JFK airport to Geneva's airport, and finally a train from Geneva's airport to Lausanne's train station. Once the travel agent makes the three reservations, it is the responsibility of the Princeton limousine company to get the tourist from Princeton to JFK; it is the responsibility of the airline company to get the tourist from JFK to Geneva; and it is the responsibility of the Swiss train service to get the tourist from Geneva to Lausanne. Each of the three segments of the trip is "direct" between two "adjacent" locations. Note that the three transportation segments are managed by different companies and use entirely different transportation modes (limousine, plane, and train). Although the transportation modes are different, they each provide the basic service of moving passengers from one location to an adjacent location. In this transportation analogy, the tourist is a datagram, each transportation segment is a link, the transportation mode is a link-layer protocol, and the

<details>
<summary>📚 知识扩展</summary>

在计算机网络中，链路层（Link Layer）是OSI模型的第二层，负责直接连接相邻节点的数据传输。它通过定义帧结构、物理地址（如MAC地址）和介质访问控制（MAC）协议，确保数据在物理介质上可靠传输。链路层协议的例子包括以太网、WiFi和PPP。链路层的核心功能包括：

1. **帧封装**：将网络层的数据报封装为链路层帧，添加源地址、目的地址和校验信息。
2. **物理寻址**：使用MAC地址标识链路上的设备。
3. **错误检测**：通过校验和（如CRC）检测传输中的比特错误。
4. **介质访问控制**：协调多个设备共享同一物理介质时的传输（如CSMA/CD在以太网中）。

链路层与网络层的关系类似于“局部运输”与“全局物流”：网络层规划端到端的路径（如选择路由），而链路层负责在每一段直接连接的链路上实际传输数据。例如，网络层决定“从A到B经过C”，而链路层负责“A到C的直接传输”和“C到B的直接传输”。
</details>

<details>
<summary>🎓 易化学习</summary>

想象一下，数据包（像游客）需要从起点到终点，但中间需要换乘不同交通工具。链路层就像每次换乘的“短途运输”：

- **游客** = 数据包  
- **每次换乘的路段** = 链路（比如从机场到车站的公路）  
- **交通工具** = 链路层协议（比如汽车、火车、飞机）  
- **司机/航空公司** = 链路层设备（比如交换机、路由器）  

每个路段（链路）由不同公司（设备）管理，用不同工具（协议）运输，但目标都是把游客（数据包）送到下一个地点（相邻节点）。链路层不关心最终目的地，只负责当前这一段的运输。
</details>

---

![Figure 6.1 Six link-layer hops between wireless host and server](images_wangyuan_output/page_2_img_1.png)