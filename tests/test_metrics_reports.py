from tests.conftest import create_user


def test_metrics_log_event_and_ledger(test_db):
    from core.services.metrics_service import log_event, log_economy_ledger
    from core.database.connection import fetch_all

    create_user("u1", "甲")
    log_event("test_action", user_id="u1", success=True, ts=1234567890)
    log_economy_ledger(
        user_id="u1",
        module="test",
        action="test",
        delta_copper=10,
        delta_gold=2,
        delta_exp=5,
        ts=1234567890,
    )

    events = fetch_all("SELECT event, user_id FROM event_logs WHERE event = %s", ("test_action",))
    ledgers = fetch_all("SELECT module, action, user_id FROM economy_ledger WHERE module = %s", ("test",))
    assert events and events[0]["user_id"] == "u1"
    assert ledgers and ledgers[0]["action"] == "test"


def test_generate_reports_guardrails(test_db):
    from core.services.metrics_service import log_event, log_economy_ledger
    from core.database.connection import fetch_all
    from scripts import generate_reports as gr

    create_user("u1", "甲")
    report_date = "2026-03-16"
    start_ts, end_ts = gr._parse_date(report_date)

    # shop buy fail rate
    log_event("shop_buy", user_id="u1", success=False, ts=start_ts + 10)
    log_event("shop_buy", user_id="u1", success=True, ts=start_ts + 20)

    # copper ratio alert
    log_economy_ledger(user_id="u1", module="hunt", action="hunt", delta_copper=100, ts=start_ts + 10)
    log_economy_ledger(user_id="u1", module="shop", action="shop_buy", delta_copper=-10, ts=start_ts + 20)

    economy = gr._economy_summary(start_ts, end_ts)
    funnels = gr._action_funnels(start_ts, end_ts)
    event_meta = gr._event_meta_summary(start_ts, end_ts)
    gacha = gr._gacha_health(start_ts, end_ts)
    alerts = gr._guardrails(report_date, economy, funnels, event_meta, gacha)

    metrics = {a["metric"] for a in alerts}
    assert "copper_net_ratio" in metrics
    assert "shop_buy_fail_rate" in metrics

    stored = fetch_all("SELECT metric FROM guardrail_alerts")
    stored_metrics = {row["metric"] for row in stored}
    assert "copper_net_ratio" in stored_metrics
    assert "shop_buy_fail_rate" in stored_metrics
