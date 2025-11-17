"""
基于企业生命周期的Alpha信号实现
根据"Theodosia Konstantinidi (2022) - Firm Life Cycle, Expectation Errors and Future Stock Returns"论文
"""

# Alpha 1: 现金流生命周期信号
# 基于Dickinson(2011)现金流模式的生命周期分类
alpha_1 = """
# 现金流生命周期信号 - 做多成熟期企业，做空引入期企业
divide(
  add(
    ts_mean(fnd7_ointfund_qfcnao, 252),  # 经营现金流均值（252天）
    ts_mean(fnd7_ointfund_qfcnvi, 252)   # 投资现金流均值（252天）
  ),
  abs(ts_mean(fnd7_ointfund_qfcnif, 252))  # 融资现金流绝对值均值
)
"""

# Alpha 2: 分析师预测误差修正信号
# 利用分析师预测误差捕捉预期错误
alpha_2 = """
# 分析师预测误差修正信号
subtract(
  ts_mean(anl14_median_cfps_fy1, 63),  # 未来一年现金流预测中位数（63天均值）
  ts_mean(anl14_actvalue_cfps_fy0, 63)  # 实际现金流（63天均值）
)
"""

# Alpha 3: 盈利不确定性信号
# 引入期企业盈利不确定性更高，成熟期企业更稳定
alpha_3 = """
# 盈利不确定性信号
divide(
  ts_std_dev(anl14_median_cfps_fy1, 252),  # 现金流预测标准差（252天）
  abs(ts_mean(anl14_median_cfps_fy1, 252))  # 现金流预测均值绝对值
)
"""

# Alpha 4: 复合生命周期信号
# 结合现金流模式和分析师预测的复合信号
alpha_4 = """
# 复合生命周期信号
multiply(
  # 现金流稳定性信号
  inverse(ts_std_dev(fnd7_ointfund_qfcnao, 252)),
  # 分析师预测准确性信号  
  inverse(abs(subtract(
    anl14_median_cfps_fy1,
    anl14_actvalue_cfps_fy0
  ))),
  # 盈利增长稳定性信号
  inverse(ts_std_dev(anl14_median_cfps_fy1, 126))
)
"""

# Alpha 5: 机构持股修正信号
# 低机构持股的引入期企业更容易被高估
alpha_5 = """
# 机构持股修正信号
multiply(
  # 现金流生命周期信号
  divide(
    add(fnd7_ointfund_qfcnao, fnd7_ointfund_qfcnvi),
    abs(fnd7_ointfund_qfcnif)
  ),
  # 机构持股修正（低机构持股权重更高）
  inverse(rank(ts_mean(oth401_game_eps_sur_vol, 63)))
)
"""

# Alpha 6: 盈利公告效应增强信号
# 成熟期企业在盈利公告日有正向反应，引入期企业有负向反应
alpha_6 = """
# 盈利公告效应增强信号
ts_delta(
  multiply(
    # 基础生命周期信号
    divide(
      add(fnd7_ointfund_qfcnao, fnd7_ointfund_qfcnvi),
      abs(fnd7_ointfund_qfcnif)
    ),
    # 盈利质量信号
    divide(fnd7_ointfund_qfcnao, fnd7_ointfund_qfcnvi)
  ),
  5  # 5天变化，捕捉盈利公告效应
)
"""

# Alpha 7: 现金流质量增强信号
# 结合现金流质量和分析师覆盖度的信号
alpha_7 = """
# 现金流质量增强信号
multiply(
  # 经营现金流质量（经营现金流/总现金流）
  divide(
    fnd7_ointfund_qfcnao,
    add(
      abs(fnd7_ointfund_qfcnao),
      abs(fnd7_ointfund_qfcnvi),
      abs(fnd7_ointfund_qfcnif)
    )
  ),
  # 分析师覆盖度信号（分析师数量越多，信息越充分）
  ts_mean(anl14_numofests_cfps_fy1, 63)
)
"""

# Alpha 8: 生命周期动量信号
# 结合生命周期和价格动量的复合信号
alpha_8 = """
# 生命周期动量信号
multiply(
  # 生命周期信号
  divide(
    add(fnd7_ointfund_qfcnao, fnd7_ointfund_qfcnvi),
    abs(fnd7_ointfund_qfcnif)
  ),
  # 价格动量信号（252天收益率）
  ts_delta(close, 252)
)
"""

# Alpha 9: 现金流持续性信号
# 关注现金流的持续性和稳定性
alpha_9 = """
# 现金流持续性信号
divide(
  # 现金流持续性（长期均值/短期波动）
  ts_mean(fnd7_ointfund_qfcnao, 252),
  add(
    ts_std_dev(fnd7_ointfund_qfcnao, 63),  # 短期波动
    0.001  # 避免除零
  )
)
"""

# Alpha 10: 综合生命周期评分
# 结合多个维度的综合生命周期评分
alpha_10 = """
# 综合生命周期评分
add(
  # 现金流模式得分
  multiply(2, divide(
    add(fnd7_ointfund_qfcnao, fnd7_ointfund_qfcnvi),
    abs(fnd7_ointfund_qfcnif)
  )),
  # 预测准确性得分
  multiply(-1, abs(subtract(
    anl14_median_cfps_fy1,
    anl14_actvalue_cfps_fy0
  ))),
  # 现金流稳定性得分
  multiply(1.5, inverse(ts_std_dev(fnd7_ointfund_qfcnao, 252))),
  # 分析师共识得分
  multiply(0.5, ts_mean(anl14_numofests_cfps_fy1, 63))
)
"""

# 所有alpha表达式列表
ALPHA_EXPRESSIONS = {
    "alpha_1_cash_flow_lifecycle": alpha_1,
    "alpha_2_analyst_forecast_error": alpha_2,
    "alpha_3_earnings_uncertainty": alpha_3,
    "alpha_4_composite_lifecycle": alpha_4,
    "alpha_5_institutional_ownership": alpha_5,
    "alpha_6_earnings_announcement": alpha_6,
    "alpha_7_cash_flow_quality": alpha_7,
    "alpha_8_lifecycle_momentum": alpha_8,
    "alpha_9_cash_flow_persistence": alpha_9,
    "alpha_10_comprehensive_score": alpha_10
}

def get_alpha_expression(alpha_name):
    """获取指定的alpha表达式"""
    return ALPHA_EXPRESSIONS.get(alpha_name, "")

def get_all_alpha_names():
    """获取所有alpha名称列表"""
    return list(ALPHA_EXPRESSIONS.keys())

def print_alpha_expression(alpha_name):
    """打印指定的alpha表达式"""
    expression = get_alpha_expression(alpha_name)
    if expression:
        print(f"{alpha_name}:")
        print(expression.strip())
        print("-" * 50)
    else:
        print(f"Alpha '{alpha_name}' not found.")

if __name__ == "__main__":
    # 测试打印所有alpha表达式
    for alpha_name in get_all_alpha_names():
        print_alpha_expression(alpha_name)