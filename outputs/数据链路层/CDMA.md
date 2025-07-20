<details>
<summary>📚 知识卡片: Code Division Multiple Access (CDMA)</summary>

**解释**: 一种多用户共享同一频率的通信技术，通过独特编码区分用户。

**示例**: 类似多个对话在同一房间进行，但使用不同语言避免混淆。

**有趣事实**: CDMA技术广泛应用于3G移动通信和军事通信中。
</details>

<details>
<summary>📚 知识卡片: Orthogonal Codes</summary>

**解释**: 相互无干扰的编码序列，确保CDMA中多用户传输的最小干扰。

**示例**: 类似不同频道的独立信号，互不影响。

**有趣事实**: 正交码的设计是CDMA实现高效频谱利用的关键。
</details>

<details>
<summary>📚 知识卡片: Chipping Sequence</summary>

**解释**: 用于编码数据的特定序列，每个用户在CDMA中拥有独特的Chipping Sequence。

**示例**: 类似不同用户的专属密码，用于区分信号。

**有趣事实**: 这些序列的设计使得多个用户可以在同一频率上同时传输数据而不互相干扰。
</details>

# Code Division Multiple Access (CDMA)

■ unique "code" assigned to each user; i.e., code set partitioning

* all users share same frequency, but each user has own "chipping" sequence (i.e., code) to encode data

<details>
<summary>📚 知识扩展</summary>

在CDMA中，每个用户被分配一个唯一的“码”，即Chipping Sequence。这种码分多址技术允许所有用户共享同一频率资源，但通过不同的编码序列来区分用户，从而实现多用户同时传输数据。
</details>

<details>
<summary>🎓 易化学习</summary>

想象一下，你和朋友们在同一个房间里用手机聊天，但你们使用不同的“暗号”（Chipping Sequence）来发送信息。这样，即使大家同时说话，也只有知道对应“暗号”的朋友才能听懂你的话。这就是CDMA的工作原理。
</details>

* allows multiple users to "coexist" and transmit simultaneously with minimal interference (if codes are "orthogonal")

<details>
<summary>📚 知识扩展</summary>

当CDMA中的编码序列是正交的时，多个用户可以在同一频率上同时传输数据，且相互之间的干扰最小。正交码的设计使得接收端能够准确分离出各个用户的信号。
</details>

<details>
<summary>🎓 易化学习</summary>

继续上面的比喻，如果大家的“暗号”设计得非常巧妙（正交码），那么即使同时说话，也不会互相干扰。就像在同一个房间里，大家用不同的语言聊天，彼此都能听懂自己朋友的话，而不会被其他人的声音打扰。
</details>

■ **encoding:** inner product:(original data)X (chipping sequence)

<details>
<summary>📚 知识扩展</summary>

在CDMA中，编码过程是通过将原始数据与Chipping Sequence进行内积运算实现的。这种编码方式使得每个用户的数据被独特地标记，从而在接收端可以通过相同的Chipping Sequence进行解码。
</details>

<details>
<summary>🎓 易化学习</summary>

想象一下，你要把一句话变成只有你知道的“暗号”。你会把这句话和你的“暗号”结合起来，形成一个新的信息。这个过程就像CDMA中的编码，原始数据和Chipping Sequence结合，生成可以传输的编码数据。
</details>

■ **decoding:** summed inner-product:(encoded data)X(chipping sequence)

<details>
<summary>📚 知识扩展</summary>

解码过程是通过将接收到的编码数据与Chipping Sequence再次进行内积运算来实现的。由于每个用户的Chipping Sequence是唯一的，因此可以准确地恢复出原始数据。
</details>

<details>
<summary>🎓 易化学习</summary>

继续上面的比喻，当你收到一个用“暗号”加密的信息时，你需要用同样的“暗号”来解密。就像你和朋友约定了一个秘密手势，只有你们俩知道，别人即使看到也不明白是什么意思。这就是CDMA的解码过程。
</details>