# CLAUDE.md

## Project Goal
对客户支持工单进行分级，标出风险、下一步和需要人工确认的问题。

## Working Constraints
- 不得输出客户手机号、邮箱或订单号。
- 不得承诺退款。

## Human Confirmation Rules
- 涉及退款、赔偿或客户身份信息 -> ask_confirmation

## Output Expectations
- Format: markdown
- Language: zh-CN
- Max words: 140
- Section: 工单级别
- Section: 风险信号
- Section: 下一步
- Section: 人工确认

## Verification
- All sections must be present

