"""
validate_dbt_structure.py

Standalone structural validation for the dbt project - checks that every
{{ ref('model_name') }} in every .sql model resolves to an actual .sql
file, and that every schema/source/semantic-layer YAML file parses.
Used by .github/workflows/ci.yml's dbt-structure job, and by hand during
development (this sandbox could not install dbt itself - see repo-root
environment notes - so this script is how every ref/YAML check in this
repo's build history was actually verified).

Run from the repo root: python3 scripts/validate_dbt_structure.py
"""
from __future__ import annotations

import os
import re
import sys

import yaml

DBT_MODELS_DIR = "dbt/models"

TOP_LEVEL_YAML_FILES = [
    "dbt/models/staging/_sources.yml",
    "dbt/models/vault/_vault_schema.yml",
    "dbt/models/gold/_gold_schema.yml",
    "dbt/models/semantic/_semantic_models.yml",
    "dbt/models/semantic/_metrics.yml",
]

REF_PATTERN = re.compile(r"ref\('([a-z_0-9]+)'\)")


def find_sql_models(models_dir: str) -> set[str]:
    models = set()
    for root, _dirs, files in os.walk(models_dir):
        for f in files:
            if f.endswith(".sql"):
                models.add(f[:-4])
    return models


def find_all_refs(models_dir: str) -> set[str]:
    refs = set()
    for root, _dirs, files in os.walk(models_dir):
        for f in files:
            if f.endswith(".sql"):
                content = open(os.path.join(root, f)).read()
                refs.update(REF_PATTERN.findall(content))
    return refs


def find_embedded_staging_yaml(staging_dir: str) -> list[tuple[str, str]]:
    """Returns (filename, yaml_block_text) for every stg_*.sql file that
    embeds a {% set yaml_metadata %}...{% endset %} block."""
    blocks = []
    for fname in sorted(os.listdir(staging_dir)):
        if not fname.endswith(".sql"):
            continue
        path = os.path.join(staging_dir, fname)
        content = open(path).read()
        if "{% set yaml_metadata %}" not in content:
            continue
        start = content.find("{% set yaml_metadata %}") + len("{% set yaml_metadata %}")
        end = content.find("{% endset %}")
        blocks.append((fname, content[start:end].strip()))
    return blocks


def main() -> int:
    ok = True

    existing_models = find_sql_models(DBT_MODELS_DIR)
    all_refs = find_all_refs(DBT_MODELS_DIR)
    missing = all_refs - existing_models
    total_sql = sum(
        1
        for root, _dirs, files in os.walk(DBT_MODELS_DIR)
        for f in files
        if f.endswith(".sql")
    )

    print(f"Total SQL model files: {total_sql}")
    print(f"Total distinct refs: {len(all_refs)}")
    if missing:
        print(f"FAIL: unresolved refs: {sorted(missing)}")
        ok = False
    else:
        print("OK: all refs resolve")

    for f in TOP_LEVEL_YAML_FILES:
        try:
            yaml.safe_load(open(f).read())
            print(f"OK: {f}")
        except Exception as e:  # noqa: BLE001
            print(f"FAIL: {f} -> {e}")
            ok = False

    staging_dir = os.path.join(DBT_MODELS_DIR, "staging")
    embedded_blocks = find_embedded_staging_yaml(staging_dir)
    for fname, block in embedded_blocks:
        try:
            yaml.safe_load(block)
        except Exception as e:  # noqa: BLE001
            print(f"FAIL: embedded YAML in {fname} -> {e}")
            ok = False
    print(f"OK: {len(embedded_blocks)} embedded staging YAML blocks validated")

    # Cross-check every metric's measure/metric references actually exist.
    sem = yaml.safe_load(open("dbt/models/semantic/_semantic_models.yml").read())
    metrics = yaml.safe_load(open("dbt/models/semantic/_metrics.yml").read())
    all_measures = {
        meas["name"]
        for m in sem["semantic_models"]
        for meas in m.get("measures", [])
    }
    all_metric_names = {m["name"] for m in metrics["metrics"]}

    for metric in metrics["metrics"]:
        tp = metric.get("type_params", {})
        if metric["type"] == "simple":
            if tp.get("measure") not in all_measures:
                print(f"FAIL: metric {metric['name']} references unknown measure {tp.get('measure')}")
                ok = False
        elif metric["type"] == "ratio":
            if tp.get("numerator") not in all_measures:
                print(f"FAIL: metric {metric['name']} references unknown numerator {tp.get('numerator')}")
                ok = False
            if tp.get("denominator") not in all_measures:
                print(f"FAIL: metric {metric['name']} references unknown denominator {tp.get('denominator')}")
                ok = False
        elif metric["type"] == "derived":
            for mm in tp.get("metrics", []):
                if mm["name"] not in all_metric_names:
                    print(f"FAIL: derived metric {metric['name']} references unknown metric {mm['name']}")
                    ok = False
    print("OK: all metric measure/metric references resolve" if ok else "See FAILs above")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
