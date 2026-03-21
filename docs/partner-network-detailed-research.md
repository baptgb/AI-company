# Claude/Anthropic Partner Network 详细调研报告

> 调研日期：2026-03-21
> 调研人：partner-researcher
> 数据来源：Anthropic官网、Claude Partner页面、第三方分析文章、官方条款文档

---

## 一、Claude Partner Network（合作伙伴网络）

### 1.1 基本信息

| 项目 | 详情 |
|------|------|
| 发布日期 | 2026年3月12日 |
| 资金承诺 | 2026年初始$1亿，承诺未来追加 |
| 会员费用 | **免费** |
| 申请入口 | https://claude.com/partners → 跳转至 https://partnerportal.anthropic.com/s/partner-registration |
| 官方公告 | https://www.anthropic.com/news/claude-partner-network |

### 1.2 申请条件

**明确要求：必须是"组织"（organization），不接受个人开发者。**

> 原文："Any organization that is bringing Claude to market is eligible to join the Claude Partner Network."
> 第三方分析明确指出："Individual freelancers and businesses without a client base or delivery capability are not the target audience."

**目标对象**：
- 大型管理咨询公司（Accenture、Deloitte、Cognizant、Infosys等已加入）
- 专业AI服务公司
- 技术咨询/集成商
- 帮助企业实施Claude的任何组织

**关键资质要求**（非官方硬性，但分析文章总结）：
- 已有客户基础和交付能力
- 有Claude实施经验或AI解决方案经验
- 企业级销售能力
- 技术团队具备API和AI工作流能力

**是否需要注册公司？**
- 官方未明确要求特定公司形式
- 但用语始终是"organization"、"companies"、"enterprises"
- **实际判断：至少需要以某种商业实体身份申请，不接受纯个人**

### 1.3 $1亿资金分配

**不是投资、不是grants、不是credits。是运营支持资金。**

具体用途：
| 用途 | 说明 |
|------|------|
| 培训和销售赋能 | Anthropic Academy课程、销售playbook |
| 市场开发和联合营销 | 共同推广活动、品牌曝光 |
| 技术支持团队扩展 | 计划将合作伙伴面向团队扩大5倍 |
| 专用技术资源 | 配备Applied AI工程师、技术架构师 |
| 国际化支持 | 本地化go-to-market支持 |

**重要：这$1亿不是直接发给合作伙伴的现金，而是Anthropic用于建设合作伙伴支持体系的投入。**

### 1.4 合作伙伴获得什么

1. **Partner Portal访问权**：
   - Anthropic Academy培训材料
   - Anthropic自用的销售playbook
   - 联合营销文档

2. **Services Partner Directory上线**：
   - 合格合作伙伴进入官方目录
   - 企业客户可通过目录找到你

3. **Claude Certified Architect认证**：
   - 第一项认证：Claude Certified Architect, Foundations
   - 考试费$99/次
   - **前5000名合作伙伴公司员工免费参加**
   - 所有13门Anthropic Academy课程免费

4. **技术支持**：
   - 专用Applied AI工程师
   - 技术架构师协助
   - 优先技术支持通道

### 1.5 合作伙伴分类

| 类别 | 说明 |
|------|------|
| Cloud Partners | 在AWS、Google Cloud、Microsoft平台提供Claude |
| Services Partners | 提供AI策略、咨询和Claude实施的公司 |
| Powered by Claude Directory | 用Claude构建产品的公司 |

### 1.6 个人开发者/小团队成功案例

**未找到确切信息。** 目前公开报道的合作伙伴均为大型/中型组织。没有个人开发者或2-3人小团队成功加入的公开案例。

### 1.7 风险与批评

- **供应商依赖**：绑定Claude意味着受制于平台变化、定价调整和模型迭代
- **早期生态**：2026年3月刚启动，目录流量和联合销售基础设施需要时间成熟
- **无保证收入**：提供的是杠杆而非线索（leads），结果取决于自身销售能力

---

## 二、Claude Code Plugin Marketplace（插件市场）

### 2.1 官方插件目录

| 项目 | 详情 |
|------|------|
| 官方目录 | https://github.com/anthropics/claude-plugins-official |
| 提交入口 | https://clau.de/plugin-directory-submission |
| 浏览安装 | https://claude.com/plugins |
| 文档 | https://code.claude.com/docs/en/plugin-marketplaces |

### 2.2 个人开发者能否提交？

**可以。** 官方明确表示：
> "Third-party partners can submit plugins for inclusion in the marketplace."
> 使用了"partners and the community"的表述，包含社区个人开发者。

**不需要公司身份即可提交插件。**

### 2.3 提交要求

**插件结构要求**：
```
my-plugin/
├── .claude-plugin/
│   ├── plugin.json          # 必需：名称、描述、版本
│   └── marketplace.json     # 市场发布元数据
├── skills/                  # 技能文件
├── commands/                # 命令文件
├── agents/                  # Agent文件
├── hooks/                   # Hook配置
└── README.md                # 文档
```

**plugin.json必需字段**：
```json
{
  "name": "your-plugin-name",        // kebab-case
  "description": "插件描述",
  "version": "1.0.0"                 // 语义化版本
}
```

### 2.4 审核流程

1. 通过提交表单提交插件
2. Anthropic进行**基础自动化审核**
3. 通过审核后加入目录
4. 想获得"**Anthropic Verified**"徽章需要额外的质量和安全审核

**审核标准**：
- 质量标准（功能完整、文档齐全）
- 安全标准（无恶意代码、数据安全）

**审核时间**：未找到官方明确的时间承诺。

**费用**：**未提及任何费用，应为免费提交。**

### 2.5 分发方式

| 方式 | 说明 | 适合场景 |
|------|------|---------|
| 官方目录提交 | 提交至anthropics/claude-plugins-official | 最大曝光 |
| 自建Marketplace | 创建marketplace.json + GitHub托管 | 自主控制 |
| npm包分发 | 作为npm包发布 | 开发者生态 |
| 社区目录 | claudemarketplaces.com 等第三方 | 补充渠道 |

### 2.6 自建Marketplace流程（推荐）

1. 创建GitHub仓库
2. 编写`.claude-plugin/marketplace.json`
3. 添加插件目录和文件
4. 用户通过`/plugin marketplace add owner/repo`安装
5. 支持版本管理、自动更新

**这是最灵活的分发方式，个人开发者完全可以独立完成。**

---

## 三、Anthropic Startup Program（创业项目）

### 3.1 基本信息

| 项目 | 详情 |
|------|------|
| 申请入口 | https://claude.com/programs/startups |
| 官方条款 | https://www.anthropic.com/startup-program-official-terms |
| 申请方式 | Airtable表单，滚动审核 |
| 审核周期 | 约2周 |

### 3.2 获得什么

| 收益 | 详情 |
|------|------|
| API Credits | 最高$25,000（约83亿输入token或16.7亿输出token，按Sonnet 4.5费率） |
| 优先速率限制 | Priority rate limits |
| 资源访问 | 特定资源和支持 |
| 社区活动 | Office hours、社区活动 |
| 技术支持 | 直接与Anthropic团队沟通 |

**Credits有效期：发放日起12个月，不可延期。**

### 3.3 申请资格

**需要以公司（Company）身份申请。**

> 官方条款用语："the Company on whose behalf an application is being submitted"

**评审考量因素**：
- 业务增长（business traction）
- 投资和融资情况
- Claude集成和使用情况
- 最终由Anthropic全权决定

**地区限制（不合格）**：
- 中国、白俄罗斯、古巴、伊朗、缅甸、朝鲜、俄罗斯、苏丹、叙利亚
- 克里米亚、顿涅茨克、卢甘斯克

### 3.4 个人开发者能否申请？

**官方条款要求以"Company"身份提交，但未定义公司最低规模。**

- 有分析指出"solo developer testing an idea"可能获得$300-$1,000
- 但官方语言始终指向公司实体
- **建议：至少需要一个商业实体（如美国LLC、个体工商户等）**

---

## 四、Anthology Fund（Menlo Ventures + Anthropic）

### 4.1 基本信息

| 项目 | 详情 |
|------|------|
| 基金规模 | $1亿（Menlo Ventures + Anthropic联合） |
| 投资范围 | 种子轮到扩张阶段 |
| 最低投资 | $100,000起 |
| 附加福利 | $25,000-$30,000 Anthropic API Credits |
| 申请入口 | https://menlovc.com/anthology-fund-application/ |
| 审核周期 | 滚动审核，约2周内回复 |

### 4.2 投资方向

1. AI基础设施和开发者工具
2. 前沿AI应用（生物、医疗、法律、金融、供应链、云、网络安全）
3. 消费级AI解决方案
4. 信任和安全工具
5. 最大化社会效益的AI应用（教育、就业、无障碍）

### 4.3 个人开发者能否申请？

- 内容始终围绕"startups"和"founders"
- **未明确排除个人开发者，但也未明确包含**
- 不要求必须构建在Claude上（但使用Anthropic技术可能加分）
- **实际判断：这是VC投资，需要有公司实体接收投资**

### 4.4 第一批投资案例

2024年12月公布了首批18家创业公司入选。具体名单未在本次调研范围内详细获取。

---

## 五、其他平台对比：个人开发者上架难度

### 5.1 对比表

| 平台 | 需要公司吗？ | 费用 | 个人开发者友好度 |
|------|------------|------|----------------|
| **Claude Code Plugin** | **不需要** | 免费 | 高 |
| **VS Code Marketplace** | **不需要** | 免费 | 高 |
| **npm** | **不需要** | 免费 | 高 |
| **PyPI** | **不需要** | 免费 | 高 |
| **GitHub Sponsors** | **不需要** | 免费（GitHub收0-6%手续费） | 高 |
| Claude Partner Network | 需要组织身份 | 免费 | 低 |
| Anthropic Startup Program | 需要公司身份 | 免费 | 中（但需公司） |
| Anthology Fund | 需要公司实体 | 免费 | 低（VC投资） |

### 5.2 各平台详情

**VS Code Marketplace**：
- 创建Publisher身份即可（可以用个人名/品牌名）
- 不需要公司，不需要付费
- 流程：注册Microsoft账号 → 创建Publisher → 打包vsix → 发布
- 参考：https://code.visualstudio.com/api/working-with-extensions/publishing-extension

**npm**：
- 注册npm账号即可发布
- 不需要公司
- 流程：npm adduser → npm publish

**PyPI**：
- 注册PyPI账号即可
- 不需要公司
- 支持package-specific token增强安全性

**GitHub Sponsors**：
- 个人即可申请（任何开源贡献者）
- 需要在支持的地区
- 需要2FA、银行和税务信息
- **注意：中国大陆在支持地区列表中，但需确认最新状态**

---

## 六、中国开发者特别注意事项

### 6.1 Anthropic对中国的政策

**这是最关键的风险因素。**

2025年9月，Anthropic宣布：
> 禁止向中国、俄罗斯、伊朗、朝鲜等国家实体控制的公司销售产品。

具体限制：
- **超过50%由中国公司直接或间接控制的实体**被禁止使用
- 不仅限于中国境内公司，全球范围内受中国实体控制的公司都受限
- Startup Program条款明确列出中国为不合格地区

### 6.2 对本项目的影响

| 场景 | 可行性 | 说明 |
|------|--------|------|
| 以中国个人/公司身份申请Partner Network | **不可行** | 明确受限地区 |
| 以中国公司身份申请Startup Program | **不可行** | 条款明确排除 |
| 以中国公司申请Anthology Fund | **不可行** | VC投资受同样限制 |
| 发布Claude Code Plugin（开源） | **可行** | Plugin提交无国籍限制 |
| 在npm/PyPI发布包 | **可行** | 无国籍限制 |
| VS Code Marketplace发布 | **可行** | 无国籍限制 |
| GitHub Sponsors | **可能可行** | 需确认中国大陆支持状态 |
| 注册海外公司（美国LLC）后申请 | **可能可行但有风险** | 见下文分析 |

### 6.3 海外公司路径分析

**如果考虑注册美国LLC**：

| 项目 | 详情 |
|------|------|
| 推荐州 | Wyoming（无州所得税、低费用、隐私保护强） |
| 注册费用 | $50-$500（州注册费） |
| 注册代理 | 约$39-$125/年（如Northwest Registered Agent） |
| EIN获取 | 致电IRS +1(267)941-1099，通常当天获得 |
| 银行开户 | Mercury、Relay、Wise Business等支持远程验证 |
| 总启动成本 | 约$200-$800 |
| 时间 | 3-10个工作日（可加急） |
| 年度维护 | $50-$200/年 |

**关键风险**：
- Anthropic的限制针对"超过50%由中国实体控制"的公司
- 如果LLC的实际受益人（beneficial owner）是中国公民，是否会触发限制——**这一点Anthropic政策中未完全明确**
- 建议在申请前咨询法律意见
- 在Anthropic的KYC（了解客户）流程中可能被要求披露最终受益人

---

## 七、推荐商业化路径

### 7.1 不需要公司即可立即执行的路径

| 步骤 | 行动 | 预计时间 |
|------|------|---------|
| 1 | 在GitHub上发布AI Team OS开源版本 | 1-2周 |
| 2 | 将核心功能打包为Claude Code Plugin | 1周 |
| 3 | 提交至官方Plugin目录（https://clau.de/plugin-directory-submission） | 提交即日 |
| 4 | 自建Plugin Marketplace（GitHub仓库托管） | 1-2天 |
| 5 | 在npm发布相关工具包 | 1天 |
| 6 | 在VS Code Marketplace发布配套扩展（如有） | 1周 |
| 7 | 设置GitHub Sponsors接受赞助 | 1天 |
| 8 | 通过开源建立品牌和用户基础 | 持续进行 |

### 7.2 需要公司但个人可操作的路径

| 步骤 | 行动 | 预计时间 | 成本 |
|------|------|---------|------|
| 1 | 注册美国Wyoming LLC | 3-10天 | $200-$800 |
| 2 | 获取EIN，开设银行账户 | 1-2周 | 免费-$50 |
| 3 | 以LLC身份申请Anthropic Startup Program | 1天申请+2周等待 | 免费 |
| 4 | 以LLC身份申请Claude Partner Network | 1天申请 | 免费 |
| 5 | 获取Claude Certified Architect认证 | 准备1-2周 | $99（合作伙伴可能免费） |
| 6 | 如获得Startup Credits，加速产品开发 | - | - |
| 7 | 产品成熟后申请Anthology Fund | 待定 | 免费 |

### 7.3 可并行的步骤

```
第1周：
├── [并行] 开源发布 + Plugin开发
├── [并行] 注册Wyoming LLC（如决定走公司路径）
└── [并行] 完成Anthropic Academy培训

第2-3周：
├── [并行] 提交Plugin至官方目录
├── [并行] LLC注册完成后申请Startup Program
├── [并行] 申请Partner Network
└── [并行] 考取Claude Certified Architect

第4周+：
├── 根据审批结果调整策略
├── 积累用户和案例
└── 评估Anthology Fund申请时机
```

### 7.4 最快上架/获得合作资格的时间线

| 里程碑 | 最快时间 |
|--------|---------|
| Plugin自建Marketplace上线 | **1-2天** |
| Plugin提交官方目录 | **当天提交，审核时间未知** |
| npm/PyPI包发布 | **当天** |
| VS Code扩展发布 | **1-2天** |
| Partner Network申请提交 | **当天**（需有组织身份） |
| Startup Program审核通过 | **2-4周**（需有公司身份） |

---

## 八、关键结论

### 确定的信息

1. **Claude Partner Network免费加入，但需要组织身份**——个人开发者不能直接申请
2. **$1亿是Anthropic的运营投入**，不是发给合作伙伴的现金/credits/投资
3. **Claude Code Plugin可以由个人开发者免费提交**——这是最友好的官方渠道
4. **Startup Program需要公司身份**，China是受限地区
5. **Anthology Fund是VC投资**，需要公司实体，最低投资$10万
6. **VS Code/npm/PyPI/GitHub Sponsors对个人开发者完全开放**

### 未找到确切信息

1. Partner Network是否有组织规模最低要求（如最少几人）——**未明确**
2. Plugin官方目录审核的具体时间承诺——**未公开**
3. 以个人注册的海外LLC申请时，受益人国籍是否会被审查——**政策未完全明确**
4. 个人开发者或2-3人小团队成功加入Partner Network的案例——**未找到**
5. Startup Program对"solo developer"的具体态度——**条款暗示需要公司但未100%明确排除个体**

---

## 九、Sources

- [Anthropic官方公告：Claude Partner Network](https://www.anthropic.com/news/claude-partner-network)
- [Claude Partners页面](https://claude.com/partners)
- [Claude Partner Network是否值得加入（分析）](https://www.lowcode.agency/blog/claude-partner-network-worth-it)
- [Anthropic Startup Program条款](https://www.anthropic.com/startup-program-official-terms)
- [Claude Startup Program](https://claude.com/programs/startups)
- [Menlo Ventures Anthology Fund](https://menlovc.com/anthology-fund/)
- [Claude Code Plugin Marketplace文档](https://code.claude.com/docs/en/plugin-marketplaces)
- [官方Plugin目录（GitHub）](https://github.com/anthropics/claude-plugins-official)
- [Claude Plugins浏览页面](https://claude.com/plugins)
- [Anthropic Development Partner Program](https://support.claude.com/en/articles/11174108-about-the-development-partner-program)
- [Claude Certified Architect认证指南](https://www.lowcode.agency/blog/how-to-become-claude-certified-architect)
- [VS Code Extension发布指南](https://code.visualstudio.com/api/working-with-extensions/publishing-extension)
- [Anthropic地区限制政策](https://www.anthropic.com/news/updating-restrictions-of-sales-to-unsupported-regions)
- [Partner Network资金分析](https://www.channelinsider.com/ai/anthropic-claude-partner-network-launch/)
- [Startup Program申请攻略](https://aicreditmart.com/ai-credits-providers/anthropic-startup-program-how-to-get-25k-in-credits-2026/)
- [美国LLC注册指南（非居民）](https://stripe.com/resources/more/how-to-open-an-llc-in-the-usa-for-nonresidents)
