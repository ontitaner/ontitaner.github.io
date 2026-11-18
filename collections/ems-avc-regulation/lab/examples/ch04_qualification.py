# @AI_GENERATED
"""ch04 示例：24h 分钟级电压序列 → 电压合格率 VQR

主线场景：50MW/100MWh 储能电站
U_target=116.0 kV, 合格范围±0.5 kV
生成 1440 个分钟级数据点，注入 23:15 越限 5min
"""
import random
from lab.ems_lab.compliance import voltage_qualification_rate

U_TARGET = 116.0
BAND = 0.5


def main():
    random.seed(42)
    data = [U_TARGET + random.uniform(-0.3, 0.3) for _ in range(1440)]
    for i in range(1380, 1385):
        data[i] = U_TARGET + 0.65

    for i in range(1385, 1400):
        data[i] = U_TARGET + BAND + 0.1

    vqr = voltage_qualification_rate(data, target=U_TARGET, band=BAND)
    qualified = sum(1 for v in data if U_TARGET - BAND <= v <= U_TARGET + BAND)

    print(f"24h 分钟级电压合格率  [主线: 50MW, PCC=110kV, 合格范围±{BAND}kV]")
    print(f"  总采样: {len(data)} 点")
    print(f"  合格:   {qualified} 点")
    print(f"  越限:   {len(data) - qualified} 点 (23:15 注入)")
    print(f"  VQR = {vqr:.4f} = {vqr*100:.2f}%")

    if vqr < 0.99:
        print(f"  判定: VQR < 99% → 扣分，S_voltage = 100 − (0.99−{vqr:.4f})×500 = {100-(0.99-vqr)*500:.1f}")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end