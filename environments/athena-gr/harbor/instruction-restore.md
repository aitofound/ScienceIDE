<!-- @CANARY@ -->
Restore the missing body of `@SUB@` in `@DEFECT_FILE@` in Athena++, pinned at
commit `@ATHENA_COMMIT@`. Reimplement the incumbent GR behavior and restore any
compiled implementation twins.

The observed behavior is:

@SYMPTOM@

Rows: @CHECKS_LIST@. Each `/app/cases/<check>/row.json` lists official frozen
shock decks, hashes, final `.tab` frame names, and one of the build variants
below:

    hydro-hllc-transform:     -g -t --prob=gr_shock_tube --coord=minkowski --flux=hllc
    hydro-hlle-transform:     -g -t --prob=gr_shock_tube --coord=minkowski --flux=hlle
    hydro-hlle-notransform:   -g    --prob=gr_shock_tube --coord=minkowski --flux=hlle
    hydro-llf-transform:      -g -t --prob=gr_shock_tube --coord=minkowski --flux=llf
    hydro-llf-notransform:    -g    --prob=gr_shock_tube --coord=minkowski --flux=llf
    mhd-hlld-transform:       -b -g -t --prob=gr_shock_tube --coord=minkowski --flux=hlld
    mhd-hlle-transform:       -b -g -t --prob=gr_shock_tube --coord=minkowski --flux=hlle
    mhd-llf-transform:        -b -g -t --prob=gr_shock_tube --coord=minkowski --flux=llf

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
