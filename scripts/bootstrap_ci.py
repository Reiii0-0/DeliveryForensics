import urllib.request
import json
import numpy as np

def query_ch(query):
    req = urllib.request.Request('http://clickhouse:8123/?user=default&password=dustiniapassword', data=query.encode('utf-8'))
    with urllib.request.urlopen(req) as response:
        return response.read().decode('utf-8')

data_str = query_ch("SELECT stage1_hours, stage2_hours, stage3_days, dateDiff('day', order_purchase_timestamp, order_estimated_delivery_date) as sla, is_late FROM dustinia.fact_deliveries FORMAT JSONEachRow")
lines = data_str.strip().split('\n')
records = [json.loads(line) for line in lines if line]

baseline_ontime = [1 if r['is_late'] == 0 else 0 for r in records]
sim_ontime = [1 if (float(r['stage1_hours']) + 0.8 * float(r['stage2_hours']) + float(r['stage3_days']) * 24) / 24.0 <= float(r['sla']) else 0 for r in records]

baseline_arr = np.array(baseline_ontime)
sim_arr = np.array(sim_ontime)

baseline_otdr = baseline_arr.mean()
simulated_otdr = sim_arr.mean()

n_bootstrap = 10000
np.random.seed(42)
diffs = []

indices = np.arange(len(records))
for _ in range(n_bootstrap):
    sample_idx = np.random.choice(indices, size=len(records), replace=True)
    b_mean = baseline_arr[sample_idx].mean()
    s_mean = sim_arr[sample_idx].mean()
    diffs.append(s_mean - b_mean)

ci_lo, ci_hi = np.percentile(diffs, [2.5, 97.5])

print(f"Baseline OTDR: {baseline_otdr:.4f}")
print(f"Simulated OTDR: {simulated_otdr:.4f}")
print(f"Improvement: {simulated_otdr - baseline_otdr:.4f} [95% CI: {ci_lo:.4f}, {ci_hi:.4f}]")
