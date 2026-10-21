"""文档一致性测试：正文自包含代码的运行输出、图文数字标注。"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
BLOCK = re.compile(r"```python\n((?:(?!```).)*?)```\n\n运行输出[^\n]*：\n\n```text\n(.*?)```", re.S)


def _inline_examples():
    for md in sorted(ROOT.glob("[0-2][0-9]*_*.md")):
        for i, m in enumerate(BLOCK.finditer(md.read_text(encoding="utf-8"))):
            yield pytest.param(m.group(1), m.group(2), id=f"{md.stem.split('_')[0]}-{i}")


@pytest.mark.parametrize("code, expected", list(_inline_examples()))
def test_inline_example_output_matches_text(code, expected):
    """正文里“自包含代码 + 运行输出”成对出现时，实际运行输出必须与正文逐字一致。"""
    env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, encoding="utf-8", env=env)
    assert r.returncode == 0, r.stderr
    assert r.stdout == expected


def test_figure_numbers_match_annotation_tables():
    """有标注清单（img/*.json）的图：正文对照表中的数字与图上标注一一对应。"""
    sys.path.insert(0, str(ROOT / "figures"))
    from check_figure_numbers import check_file

    problems = [p for md in sorted(ROOT.glob("[0-2][0-9]*_*.md")) for p in check_file(md)]
    assert problems == []
def test_ch06_figure_manifests_present():
    """第06章三张正式配图必须有可解析的数字清单，避免检查器因缺JSON而跳过。"""
    expected = {
        "ch06_pwm.png",
        "ch06_pq_capability.png",
        "ch06_ride_through.png",
    }
    refs = set(re.findall(r"!\[[^\]]*\]\(img/(ch06_[^)]+\.png)\)",
                         (ROOT / "06_PCS与并网.md").read_text(encoding="utf-8")))
    assert refs == expected
    for figure in sorted(expected):
        manifest = ROOT / "img" / f"{Path(figure).stem}.json"
        assert manifest.exists(), f"缺少 {manifest.name}"
        data = json.loads(manifest.read_text(encoding="utf-8"))
        assert data["figure"] == figure
        assert data["numbers"], f"{manifest.name} 没有标注数字"


def test_ch07_figure_manifests_present():
    """第07章两张正式配图必须有可解析的数字清单。"""
    expected = {
        "ch07_efficiency_chain.png",
        "ch07_direction_test.png",
    }
    refs = set(re.findall(r"!\[[^\]]*\]\(img/(ch07_[^)]+\.png)\)",
                         (ROOT / "07_电站拓扑与功率平衡.md").read_text(encoding="utf-8")))
    assert refs == expected
    for figure in sorted(expected):
        manifest = ROOT / "img" / f"{Path(figure).stem}.json"
        assert manifest.exists(), f"缺少 {manifest.name}"
        data = json.loads(manifest.read_text(encoding="utf-8"))
        assert data["figure"] == figure
        assert data["numbers"], f"{manifest.name} 没有标注数字"


def _assert_figure_manifests(chapter: str, markdown_name: str, expected: set[str]):
    refs = set(re.findall(rf"!\[[^\]]*\]\(img/({chapter}_[^)]+\.png)\)",
                         (ROOT / markdown_name).read_text(encoding="utf-8")))
    assert refs == expected
    for figure in sorted(expected):
        manifest = ROOT / "img" / f"{Path(figure).stem}.json"
        assert manifest.exists(), f"缺少 {manifest.name}"
        data = json.loads(manifest.read_text(encoding="utf-8"))
        assert data["figure"] == figure
        assert data["numbers"], f"{manifest.name} 没有标注数字"


def test_ch08_figure_manifests_present():
    """第08章正式配图必须有可解析的数字清单。"""
    _assert_figure_manifests("ch08", "08_EMS系统架构与部署.md", {"ch08_timescales.png"})


def test_ch09_figure_manifests_present():
    """第09章两张正式配图必须有可解析的数字清单。"""
    _assert_figure_manifests("ch09", "09_EMS软件控制流水线.md",
                            {"ch09_limit_then_sum.png", "ch09_latency_budget.png"})


def test_ch10_figure_manifests_present():
    """第10章两张正式配图必须有可解析的数字清单。"""
    _assert_figure_manifests("ch10", "10_通信点表与数据质量.md",
                            {"ch10_word_order.png", "ch10_quality_timeline.png"})


def test_ch11_figure_manifests_present():
    """第11章正式配图必须有可解析的数字清单。"""
    _assert_figure_manifests("ch11", "11_控制基础函数.md", {
        "ch11_clamp.png", "ch11_deadband.png", "ch11_hysteresis.png", "ch11_ramp.png",
        "ch11_lowpass.png", "ch11_interp.png", "ch11_pi_converge.png", "ch11_pi_antiwindup.png",
    })


def test_ch12_figure_manifests_present():
    """第12章正式配图必须有可解析的数字清单。"""
    _assert_figure_manifests("ch12", "12_安全约束与可行域.md", {
        "ch12_feasible_domain.png", "ch12_load_drop.png", "ch12_soc_zones.png",
    })


def test_ch13_figure_manifests_present():
    """第13章正式配图必须有可解析的数字清单。"""
    _assert_figure_manifests("ch13", "13_峰谷套利与计划曲线.md", {
        "ch13_spread_profit.png", "ch13_tou_plan.png",
    })


def test_ch14_figure_manifests_present():
    """第14章正式配图必须有可解析的数字清单。"""
    _assert_figure_manifests("ch14", "14_需量管理.md", {
        "ch14_fixed_vs_sliding.png", "ch14_required_discharge.png", "ch14_peak_shaving.png",
    })


def test_ch15_figure_manifests_present():
    """第15章正式配图必须有可解析的数字清单。"""
    _assert_figure_manifests("ch15", "15_频率与一次调频.md", {
        "ch15_frequency_event.png", "ch15_frequency_layers.png", "ch15_droop.png", "ch15_rocof.png",
    })


def test_ch16_figure_manifests_present():
    """第16章正式配图必须有可解析的数字清单。"""
    _assert_figure_manifests("ch16", "16_AGC与调度考核.md", {
        "ch16_agc_tracking.png", "ch16_soc_depletion.png", "ch16_thermal_bess.png",
    })


def test_ch17_figure_manifests_present():
    """第17章正式配图必须有可解析的数字清单。"""
    _assert_figure_manifests("ch17", "17_无功电压与AVC.md", {
        "ch17_pu_scale.png", "ch17_voltage_rx.png", "ch17_modes_compare_fixed.png",
        "ch17_qu_droop.png", "ch17_avc_cycle.png", "ch17_pq_projection.png",
    })


def test_ch18_figure_manifests_present():
    """第18章正式配图必须有可解析的数字清单。"""
    _assert_figure_manifests("ch18", "18_命令仲裁与功率分配.md", {
        "ch18_limit_vs_project.png", "ch18_offline_realloc.png", "ch18_soc_balance.png",
    })


def test_ch19_figure_manifests_present():
    """第19章三张正式配图必须有可解析的数字清单。"""
    _assert_figure_manifests("ch19", "19_仿真与测试.md", {
        "ch19_load_drop.png", "ch19_timestamp_align.png", "ch19_meter_frozen.png",
    })


def test_ch20_figure_manifests_present():
    """第20章两张正式配图必须有可解析的数字清单。"""
    _assert_figure_manifests("ch20", "20_运维可观测性与安全.md", {
        "ch20_alarm_debounce.png", "ch20_limit_chain.png",
    })


def test_ch21_figure_manifests_present():
    """第21章两张正式配图必须有可解析的数字清单。"""
    _assert_figure_manifests("ch21", "21_综合项目.md", {
        "ch21_day.png", "ch21_compare.png",
    })


def test_local_markdown_links_resolve():
    """课程主目录中的本地 Markdown 链接必须指向现有文件。"""
    link_re = re.compile(r"(?<!!)!?\[[^\]]*\]\(([^)]+)\)")
    for md in sorted(ROOT.glob("*.md")):
        if md.name == "_写作规范.md":
            continue
        for raw_target in link_re.findall(md.read_text(encoding="utf-8")):
            target = raw_target.strip().split()[0].strip("<>")
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            relative = target.split("#", 1)[0]
            if relative:
                assert (md.parent / relative).exists(), f"{md.name}: 链接目标不存在 {target}"


def test_readme_lists_all_root_markdown_assets():
    """README必须覆盖根目录全部正式Markdown资产，避免目录与文件树漂移。"""
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    expected = [p.name for p in ROOT.glob("*.md") if p.name != "README.md"]
    missing = [name for name in expected if name not in readme]
    assert missing == []
    assert "_原稿备份_v1/05_SOC_SOH_SOP与能力模型.原稿.md" in readme


def test_lab_python_sources_have_no_ai_markers():
    """lab下作者Python源码不得残留AI生成标记。"""
    marker = "@" + "AI_GENERATED"
    end_marker = marker + ": end"
    problems = []
    for source in sorted((ROOT / "lab").rglob("*.py")):
        text = source.read_text(encoding="utf-8")
        if marker in text or end_marker in text:
            problems.append(str(source.relative_to(ROOT)))
    assert problems == []



