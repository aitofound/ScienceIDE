<!-- @CANARY@ -->
Restore the missing body of `@SUB@` in `@DEFECT_FILE@` in Athena++, pinned at
commit `@ATHENA_COMMIT@`. Reimplement it so native chemistry evolution matches
the incumbent, including any retained compiled implementation twins.

Observed behavior:

@SYMPTOM@

Rows: @CHECKS_LIST@. Read each `/app/cases/<row>/row.json`. Build every needed
profile with `python3 /app/rowtool.py build /app/athena <profile> <build-dir>
4 /usr`, then run rows with `/app/rowtool.py run`. Deliver only native history
and the highest-numbered full-precision final tab MeshBlock group under
`/logs/artifacts/<row>/`.

The ladder is 0.2 conformance + 0.5 pointwise evolution-frame fraction + 0.3
canonical exact bytes; physical time/cycle fields stay exact. The measured
unfixed floor is about @FLOOR@ and reward is floor-normalized. Network and the
pristine archive are absent. Do not change decks, validators, numerical or
compiler contracts, and do not post-process outputs.
