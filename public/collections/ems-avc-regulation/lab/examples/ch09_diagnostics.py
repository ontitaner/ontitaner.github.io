# @AI_GENERATED
"""ch09 示例：五类典型误区诊断引擎

主线场景：50MW/100MWh 储能电站运行三个月后收到"电压合格率不达标"罚单
"""
from lab.ems_lab.diagnostics import diagnose


def main():
    print("AVC 典型误区诊断  [主线: 50MW 储能电站, 运行第3个月]\n")

    scenarios = [
        (["死区 0.5kV", "合格范围 0.5kV", "边缘不动作", "VQR自统计99%调度94%"],
         "场景A: 死区=合格范围→合规链断裂"),
        (["NTP偏差5s", "时间对不上", "23:14:58和23:15:02各扣一次", "重复扣"],
         "场景B: NTP时间偏移→重复扣分"),
        (["SVG本地模式", "关口表Q与EMS不一致", "差6000kvar", "远方模式"],
         "场景C: SVG本地抢控→总Q失控"),
        (["积分饱和", "符号反转滞后90s", "电压偏高→偏低切换"],
         "场景D: PI积分饱和→反向调节滞后"),
        (["104参数禁止上传", "调度显示离线", "EMS显示RUNNING", "投运率0"],
         "场景E: 参数上传禁止→调度以为离线"),
    ]

    for events, title in scenarios:
        results = diagnose(events)
        print(f"--- {title} ---")
        for r in results:
            print(f"  根因: {r.root_cause[:60]}...")
            print(f"  证据: {r.evidence[:60]}...")
            print(f"  修复: {r.fix[:60]}...")
            print(f"  预计排查: {r.check_time_minutes} 分钟\n")


if __name__ == "__main__":
    main()
# @AI_GENERATED: end