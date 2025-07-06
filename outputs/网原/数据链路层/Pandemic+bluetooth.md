## Pandemic + Bluetooth

![Alice and Bob meet each other for the first time and have a 10-minute conversation.

![Bob is positively diagnosed for COVID-19 and enters the test result in an app from a public health authority.

![Their phones exchange anonymous identifier beacons (which change frequently).

![A few days later\cdots](images_Pandemic+bluetooth/page_1_img_4.png)

](images_Pandemic+bluetooth/page_1_img_3.png)

](images_Pandemic+bluetooth/page_1_img_2.png)

](images_Pandemic+bluetooth/page_1_img_1.png)

<details>
<summary>📚 知识卡片: 匿名标识符（Anonymous Identifier）</summary>

**解释**: 用于识别设备但不暴露用户身份的临时标识符，常用于保护隐私的场景。

**示例**: 蓝牙设备广播的匿名标识符会定期更换，避免长期追踪。

**有趣事实**: 苹果的"Find My"功能使用类似技术保护用户隐私。
</details>

<details>
<summary>📚 知识卡片: 蓝牙信标（Bluetooth Beacon）</summary>

**解释**: 通过蓝牙低功耗（BLE）技术广播的无线信号，用于近距离设备交互。

**示例**: 商场导航应用通过接收特定信标实现室内定位。

**有趣事实**: 蓝牙信标技术最初由苹果公司在2013年推出iBeacon协议普及。
</details>

---

Apps can only get more information via user consent

![With Bob's consent, his phone uploads the last 14 days of keys for his broadcast beacons to the cloud.

![\sim 14 day temporary store

![图片_1_7](images_Pandemic+bluetooth/page_1_img_7.png)

](images_Pandemic+bluetooth/page_1_img_6.png)

](images_Pandemic+bluetooth/page_1_img_5.png)

<details>
<summary>📚 知识扩展</summary>

蓝牙密钥分发机制是接触追踪系统的核心：当用户确诊后，其设备会将过去14天生成的滚动密钥（Rolling Proximity Identifiers, RPIs）上传至服务器。其他用户设备可通过比对本地存储的密钥与确诊者上传的密钥，判断是否曾接触。这种设计平衡了隐私保护与公共卫生需求，类似"数字接触日记"的概念。
</details>

<details>
<summary>🎓 易化学习</summary>

想象每个手机都在不断广播"动态密码"，这些密码每15分钟变化一次。如果某人确诊，会把最近两周的"密码本"上传到云端。其他手机可以检查自己记录的"密码本"是否有匹配，就像查字典一样判断是否接触过确诊者。所有密码都是临时的且匿名的，不会暴露个人信息。
</details>

<details>
<summary>📚 知识卡片: 滚动密钥（Rolling Proximity Identifier）</summary>

**解释**: 定期自动变更的加密标识符，用于蓝牙接触追踪以避免长期追踪。

**示例**: 每15分钟生成一个新密钥，每天产生约100个独立标识。

**有趣事实**: RPIs借鉴了TOR浏览器的临时电路技术原理实现隐私保护。
</details>

<details>
<summary>📚 知识卡片: 临时存储（Temporary Store）</summary>

**解释**: 数据短期保存机制，用于限制信息留存时间以降低隐私风险。

**示例**: 公共卫生系统通常设置14天数据保留期，超过后自动删除。

**有趣事实**: 欧盟GDPR规定医疗数据存储不得超过实现目的所需时长。
</details>