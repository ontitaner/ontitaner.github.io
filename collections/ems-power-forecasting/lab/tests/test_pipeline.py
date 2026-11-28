# @AI_GENERATED
"""第 11 章一致性测试：锚定正文手算数值。

主案例三点流水线：GHI=[800, nan, 820]、T_amb=20、时标 [660, 675, 690]
-> P_hat=[18.154, 18.394, 18.633]、status=[valid, filled, valid]；
契约校验对齐点通过、时标错位 727.5 拦截。
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from ems_lab.pipeline import (  # noqa: E402
    ForecastRecord,
    run_forecast_pipeline,
    validate_contract,
)


def _run_main():
    return run_forecast_pipeline(
        [800.0, float("nan"), 820.0], [20.0, 20.0, 20.0], [660.0, 675.0, 690.0]
    )


def test_pipeline_records():
    records = _run_main()
    assert len(records) == 3
    # 11:00 GHI=800 -> 18.154（复用 05 章短测主案例）
    assert records[0].p_hat == pytest.approx(18.154, abs=1e-9)
    assert records[0].status == "valid"
    # 11:15 GHI 缺测 -> 回填 810 -> 18.394
    assert records[1].p_hat == pytest.approx(18.394, abs=1e-3)
    assert records[1].status == "filled"
    # 11:30 GHI=820 -> 18.633
    assert records[2].p_hat == pytest.approx(18.633, abs=1e-3)
    assert records[2].status == "valid"


def test_contract_aligned():
    report = validate_contract(_run_main())
    assert all(r["aligned"] for r in report)
    assert all(r["unit_ok"] for r in report)
    assert all(r["ok"] for r in report)


def test_contract_timestamp_misaligned():
    # 12:07:30 = 727.5 分钟，偏移 7.5 > 2.5 -> 时标错位，契约拦截
    r = validate_contract([ForecastRecord(727.5, 18.154, "valid")])[0]
    assert not r["aligned"]
    assert not r["ok"]


def test_contract_bad_unit_and_status():
    bad_unit = ForecastRecord(660.0, 18.154, "valid", unit="kW")
    assert not validate_contract([bad_unit])[0]["unit_ok"]
    bad_status = ForecastRecord(660.0, 18.154, "unknown")
    assert not validate_contract([bad_status])[0]["status_ok"]


def test_contract_negative_p_hat():
    neg = ForecastRecord(660.0, -1.0, "valid")
    assert not validate_contract([neg])[0]["p_hat_ok"]


def test_invalid_length():
    with pytest.raises(ValueError):
        run_forecast_pipeline([800.0, 810.0], [20.0], [660.0, 675.0])
    with pytest.raises(ValueError):
        validate_contract([ForecastRecord(660.0, 18.154, "valid")], dt=0.0)