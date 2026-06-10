from datetime import date

from db.repository import create_bean, create_brew_log, list_beans, list_brew_logs
from db.session import init_db
from services.udp_receiver import compute_flow_rate, parse_payload


def run() -> None:
    init_db()

    weight_only_payload = "1.250,12.30"
    weight_only_point = parse_payload(weight_only_payload)
    assert weight_only_point is not None
    assert weight_only_point.temp_kettle == 0.0

    payload = "1.250,12.30,91.20,88.10,brewing"
    point = parse_payload(payload)
    assert point is not None
    assert point.state == "brewing"

    flow = compute_flow_rate([
        point,
        parse_payload("2.250,18.30,91.00,87.90,brewing"),
    ])
    assert flow > 0

    beans = list_beans(include_archived=True)
    if beans:
        bean_id = beans[0].id
    else:
        bean = create_bean(
            name="SmokeTest Bean",
            roaster="Local",
            process="Washed",
            roast_level="Medium",
            roast_date=date.today(),
        )
        bean_id = bean.id

    log = create_brew_log(
        bean_id=bean_id,
        days_from_roast=0,
        elapsed_time_total=30.0,
        max_weight=200.0,
        powder_weight=15.0,
        extract_weight=210.0,
        tds=1.35,
        yield_ey=(210.0 * 1.35) / 15.0,
        brew_ratio=14.0,
        grind_size="Medium-Fine",
        dripper="V60",
        acidity=3,
        sweetness=4,
        body=3,
        rating=4,
        notes="smoke test",
        timeseries_json=[
            {"elapsed": 0.0, "weight": 0.0, "temp_kettle": 92.0, "temp_dripper": 30.0, "flow_rate": 0.0, "state": "waiting"},
            {"elapsed": 1.0, "weight": 8.0, "temp_kettle": 91.8, "temp_dripper": 55.0, "flow_rate": 8.0, "state": "brewing"},
        ],
    )

    assert log.id is not None
    logs = list_brew_logs()
    assert len(logs) >= 1

    print("smoke_test: OK")


if __name__ == "__main__":
    run()
