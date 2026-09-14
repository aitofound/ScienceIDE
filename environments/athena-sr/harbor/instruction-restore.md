<!-- @CANARY@ -->
Restore the missing body of `@SUB@` in `@DEFECT_FILE@` in Athena++, pinned at
commit `@ATHENA_COMMIT@`. Reimplement the incumbent SR behavior and restore any
compiled implementation twins.

The observed behavior is:

@SYMPTOM@

Rows: @CHECKS_LIST@. Each `/app/cases/<check>/row.json` lists a selected
official deck, hash, final `.tab` frame names, and one of these variants:

    hydro-hllc-shock: -s    --prob=gr_shock_tube --coord=cartesian --flux=hllc
    hydro-hlle-shock: -s    --prob=gr_shock_tube --coord=cartesian --flux=hlle
    hydro-llf-shock:  -s    --prob=gr_shock_tube --coord=cartesian --flux=llf
    hydro-hllc-wave:  -s    --prob=gr_linear_wave --coord=cartesian --flux=hllc
    mhd-hlld-shock:   -s -b --prob=gr_shock_tube --coord=cartesian --flux=hlld
    mhd-hlle-shock:   -s -b --prob=gr_shock_tube --coord=cartesian --flux=hlle
    mhd-llf-shock:    -s -b --prob=gr_shock_tube --coord=cartesian --flux=llf
    mhd-hlld-wave:    -s -b --prob=gr_linear_wave --coord=cartesian --flux=hlld

Configure fresh copies with the row's switches plus
`--cflag='-O2 -g0 -ffp-contract=off'`; build with
`make -j4 EXE_DIR=<bin>/ OBJ_DIR=<obj>/`. Run every deck as
`<athena> -i <deck>.athinput -d .` and place only each named native final frame
under `/logs/artifacts/<check>/`.

The ladder is 0.2 conformance + 0.5 final-frame fraction + 0.3 exact scored
bytes. No wall timestamp is present or masked. The unfixed floor is about
@FLOOR@ and reward is floor-normalized; a straw crash/hang is floor zero. The
network and pristine archive are absent. Do not alter decks, validators,
numerical/compiler settings, or post-process outputs.
