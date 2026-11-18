"""第 07 章最小闭环：效率链 → 功率平衡 → 残差诊断。

输入：直流侧放电 1000 kW、站内负荷/辅助/损耗和并网点实测值
算法：PCS/变压器效率换算；PCC 功率平衡；计算残差
输出：交流侧功率、PCC 计算值、诊断嫌疑

运行：python examples/ch07_site_balance.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ems_lab.site import Stage, chain_from_dc, diagnose_balance, site_pcc_kw  # noqa: E402


def main():
    chain = chain_from_dc(1000, [Stage("PCS", 0.98, 0.975), Stage("变压器", 0.99)])
    p_bess_ac = chain.powers_kw[1]  # 980 kW：功率平衡必须使用 PCS 交流侧
    pcc = site_pcc_kw(300, p_bess_ac, 800, p_aux_kw=20, p_loss_kw=2)
    print(f"直流侧放电：1000.0 kW → PCS 交流侧：{p_bess_ac:.1f} kW")
    print(f"PCC 计算值：{pcc:.1f} kW（300 + 980 − 800 − 20 − 2）")

    normal = diagnose_balance(pcc, 300, p_bess_ac, 800, 20, 2)
    wrong_plane = diagnose_balance(pcc, 300, 1000, 800, 20, 2)
    print(f"正常诊断：{normal or '一致'}")
    print(f"把直流功率当交流功率：{wrong_plane}")
    assert abs(pcc - 458) < 1e-9
    assert normal == []
    # 单点残差可能与辅助负荷漏计等原因混淆，实际诊断要用多工况复核。
    assert wrong_plane
    print("自检通过")


if __name__ == "__main__":
    main()

