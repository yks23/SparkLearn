## Code Division Multiple Access (CDMA)

■ unique "code" assigned to each user;i.e.,code set partitioning

* all users share same frequency, but each user has own "chipping" sequence (i.e., code) to encode data
* allows multiple users to "coexist" and transmit simultaneously with minimal interference (if codes are "orthogonal")
* ■encoding:inner product:(original data)X(chipping sequence)

■ decoding:summed inner-product:(encoded data)X (chipping sequence)

<details>
<summary>📚 知识卡片: Code Division Multiple Access (CDMA)</summary>

**解释**: 一种多址通信技术，通过为每个用户分配唯一代码实现共享频段通信。

**示例**: 在手机通信中，多个用户可以同时使用同一频率进行通话。

**有趣事实**: CDMA技术被广泛应用于3G网络，提高了频谱利用率和通信安全性。
</details>

<details>
<summary>📚 知识卡片: chipping sequence</summary>

**解释**: 用于编码数据的伪随机序列，每个用户有独特的序列。

**示例**: 在CDMA中，用户A可能使用[1, -1, 1, -1]作为其chipping sequence。

**有趣事实**: 这些序列设计得几乎互不干扰，类似于给每个用户分配了独特的"密码"。
</details>

<details>
<summary>📚 知识扩展</summary>

CDMA的核心技术是使用正交或准正交的扩频码序列。这些序列经过精心设计，使得不同用户的信号在接收端可以很容易地区分开来，即使它们在同一频率上传输。这种技术大大提高了频谱效率，允许更多用户在同一频段上通信而不会相互干扰。
</details>

<details>
<summary>🎓 易化学习</summary>

想象一下在一个嘈杂的派对上，每个人都用不同的暗号说话。CDMA就像给每个人一个独特的"暗号"（chipping sequence），这样即使大家同时说话，你也能根据暗号识别出你想听的人的声音。接收方只需要知道这个暗号，就可以从混合的声音中提取出特定的对话。
</details>

<details>
<summary>📚 知识卡片: orthogonal codes</summary>

**解释**: 互相正交的编码序列，理想情况下彼此之间的内积为零。

**示例**: Walsh码是常用的正交码之一，在CDMA系统中用于区分不同用户。

**有趣事实**: 正交码的使用可以完全消除多用户间的干扰，但实际中由于信道特性，通常只能达到准正交。
</details>

<details>
<summary>📚 知识扩展</summary>

正交编码是CDMA系统的基石。在理想情况下，使用正交码的用户可以在同一频率上无干扰地通信。然而，在实际无线环境中，由于多径效应等因素，完全的正交性很难实现。因此，系统设计者会采用各种技术来逼近这种理想状态，如使用伪随机序列和功率控制等。
</details>

<details>
<summary>🎓 易化学习</summary>

把正交码想象成一组互不干扰的"频道"。就像电视的不同频道一样，虽然所有节目都通过同一个大频道广播，但你的电视机可以选择特定频道观看。在CDMA中，每个用户的正交码就像他们的专属频道，让他们能在同一频率上和平共处。
</details>

<details>
<summary>📚 知识卡片: inner product</summary>

**解释**: 两个向量的点积运算，用于CDMA中的编码过程。

**示例**: 如果数据向量是[1, 0, 1]，chipping sequence是[1, -1, 1]，则内积为1*1 + 0*(-1) + 1*1 = 2。

**有趣事实**: 内积运算的结果可以看作是原始数据与chipping sequence的"匹配度"。
</details>

<details>
<summary>📚 知识扩展</summary>

内积是线性代数中的基本运算，在CDMA中起着关键作用。它不仅用于数据编码，也用于解码过程。通过计算接收信号与各个用户chipping sequence的内积，可以恢复出原始数据。这个过程类似于用钥匙开锁——只有正确的chipping sequence（钥匙）才能打开对应的数据（锁）。
</details>

<details>
<summary>🎓 易化学习</summary>

想象你在超市扫描商品条形码。内积就像扫描过程：你把商品条码（数据）和扫描仪的光线模式（chipping sequence）对准，然后得到一个数字（内积结果）。在CDMA中，这个过程帮助接收方识别和提取特定用户的数据。
</details>