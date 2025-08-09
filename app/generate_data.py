from __future__ import annotations

import csv
from pathlib import Path
import sys
from typing import List

from faker import Faker

from utils import DATA_DIR, WAITERS_CSV, TIPS_CSV, QRCODES_DIR
from components import generate_qr_png


def generate_waiters(n: int = 6) -> List[dict]:
    fake = Faker()
    waiters = []
    for i in range(1, n + 1):
        wid = f"W{i:03d}"
        waiters.append(
            {
                "waiter_id": wid,
                "name": fake.name(),
                "phone": fake.phone_number(),
            }
        )
    return waiters


def write_waiters(waiters: List[dict], *, force: bool = False) -> None:
    WAITERS_CSV.parent.mkdir(parents=True, exist_ok=True)
    if WAITERS_CSV.exists() and not force:
        print(f"Exists, keeping: {WAITERS_CSV}")
        return
    with WAITERS_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["waiter_id", "name", "phone"])
        writer.writeheader()
        writer.writerows(waiters)


def write_empty_tips(*, force: bool = False) -> None:
    TIPS_CSV.parent.mkdir(parents=True, exist_ok=True)
    if TIPS_CSV.exists() and not force:
        print(f"Exists, keeping: {TIPS_CSV}")
        return
    with TIPS_CSV.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["timestamp", "waiter_id", "amount", "rating", "feedback", "sentiment"],
        )
        writer.writeheader()


def generate_qrs_for_waiters(app_base_url: str, waiters: List[dict], *, force: bool = False) -> None:
    QRCODES_DIR.mkdir(parents=True, exist_ok=True)
    for w in waiters:
        url = f"{app_base_url}?waiter_id={w['waiter_id']}"
        target = QRCODES_DIR / f"{w['waiter_id']}.png"
        if force or not target.exists():
            generate_qr_png(url, target)
        else:
            print(f"Exists, keeping: {target}")


def main() -> None:
    force = "--force" in sys.argv
    print("Generating synthetic data..." + (" (force)" if force else ""))
    waiters = generate_waiters(6)
    write_waiters(waiters, force=force)
    write_empty_tips(force=force)
    # default base URL for local demo
    app_base_url = "http://localhost:8501/"
    generate_qrs_for_waiters(app_base_url, waiters, force=force)
    print(f"Created: {WAITERS_CSV}")
    print(f"Created: {TIPS_CSV}")
    print(f"QRs in: {QRCODES_DIR}")


if __name__ == "__main__":
    main()


