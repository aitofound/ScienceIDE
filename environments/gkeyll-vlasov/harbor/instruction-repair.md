<!-- @CANARY@ -->
<!-- template-owner: gkeyll-vlasov -->
Find and repair @DEFECT_SCOPE@ in the pinned Gkeyll @APP@ subsystem. The root
cause and exact location are yours to determine.

## Observed symptom

@SYMPTOM@

The graded rows are: @CHECKS_LIST@. Each `/app/cases/<check>/row.json` and
the matching `/app/checks/<check>/` define one authoritative serial regression.

After repairing `/app/gkeyll`, build once and run every listed row:

    python3 /app/rowtool.py build /app/gkeyll @PROFILE@ /app/builds/@PROFILE@ 2
    python3 /app/rowtool.py run /app/builds /app/cases/<check> /app/checks/<check> /logs/artifacts/<check> @ROW_TIMEOUT@

Do not modify cases, validators, helpers, outputs, or compiler flags, and do
not fabricate or post-process results. An empty delivery earns 0.0.
