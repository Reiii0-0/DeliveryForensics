-- 19. N-Tier Forensic Risk Attribution - MV Version
-- Goal: Attribute delay probability using handoff-specific entropy.
SELECT
    seller_state,
    customer_state,
    round(entropyMerge(prep_entropy_state), 4) AS seller_prep_chaos,
    round(entropyMerge(transit_entropy_state), 4) AS carrier_transit_chaos,
    round(entropyMerge(outcome_entropy_state), 4) AS combined_node_chaos
FROM dustinia.mv_entropy_forensics
GROUP BY seller_state, customer_state
HAVING countMerge(total_volume) > 50
ORDER BY combined_node_chaos DESC
LIMIT 20;
