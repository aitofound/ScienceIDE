#!/usr/bin/env julia
# Deterministic fixture authoring for EDKit v0.5.0, commit 538fce882ab73e3af447f4bc6a1704d290c88aba.
# This generator creates inputs only: it never calls a time-evolution solver.
if ARGS == ["--help"]
    println("usage: julia --project=<EDKit-environment> generate_fixtures.jl <empty-scratch-directory>")
    println("The output directory must be outside this task and empty or absent; an existing parent directory is required.")
    println("Generates frozen inputs only. Does not call timeevolve or overwrite shipped task inputs.")
    exit(0)
end

const OUT = let
    length(ARGS) == 1 || error("Provide exactly one explicit empty scratch output directory; there is no default output path. Run with --help for usage.")
    isempty(strip(ARGS[1])) && error("The scratch output directory must not be empty text.")
    destination = abspath(ARGS[1])
    islink(destination) && error("The scratch output directory must be a real directory, not a symbolic link.")
    isdir(dirname(destination)) || error("Create the scratch output directory's parent first: $(dirname(destination))")
    if ispath(destination)
        isdir(destination) || error("The scratch output path already exists and is not a directory: $destination")
        isempty(readdir(destination)) || error("Refusing to overwrite a nonempty scratch output directory: $destination")
    end
    physical = ispath(destination) ? realpath(destination) : joinpath(realpath(dirname(destination)), basename(destination))
    task_parts = splitpath(realpath(joinpath(@__DIR__, "..", "..")))
    output_parts = splitpath(physical)
    if length(output_parts) >= length(task_parts) && output_parts[1:length(task_parts)] == task_parts
        error("Choose a scratch output directory outside this task; shipped inputs must remain unchanged.")
    end
    physical
end

using EDKit, LinearAlgebra, Random, TOML

const ITEMS = Any[]
rows(A) = [collect(A[i, :]) for i in axes(A, 1)]
opts(;kwargs...) = Dict{String,Any}(string(k)=>v for (k,v) in kwargs)
xxz(L; delta=0.7, flip=0.5, sector=false, shift=0.0) = Dict{String,Any}("kind"=>(sector ? "xxz_sector" : "xxz"), "L"=>L, "N"=>L÷2, "k"=>0, "delta"=>delta, "flip"=>flip, "shift"=>shift, "periodic"=>true, "spin_form"=>(flip==0.5 ? "cartesian" : "ladder"))
dense(A) = Dict{String,Any}("kind"=>"dense", "real"=>rows(real.(A)), "imag"=>rows(imag.(A)))
randstate(n) = normalize!(randn(ComplexF64,n))
function neel(L)
    p=zeros(ComplexF64,2^L)
    j=1+sum((isodd(i) ? 1 : 0)*2^(L-i) for i=1:L)
    p[j]=1
    p
end
function makecase(id,H,p,ts; mode="multi", options=opts(), l2=nothing, norm_abs=nothing, addition="", statuses=Dict{String,Any}(), requirements=Dict{String,Any}(), kwargs...)
    c=Dict{String,Any}("id"=>id,"mode"=>mode,"hamiltonian"=>deepcopy(H),"state_real"=>real.(p),"state_imag"=>imag.(p),"times"=>Float64.(ts),"options"=>options,"expected_statuses"=>statuses,"diagnostic_requirements"=>requirements)
    bounds=Dict{String,Any}()
    isnothing(l2) || (bounds["state_l2"]=l2)
    isnothing(norm_abs) || (bounds["norm_abs"]=norm_abs)
    c[isempty(addition) ? "upstream_bounds" : "provisional_bounds"]=bounds
    isempty(addition) || (c["addition"]=addition)
    for (k,v) in kwargs; c[string(k)]=v; end
    c
end
function emit(slug,path,selector,cases; note="", cross_checks=Any[])
    root=Dict{String,Any}("schema_version"=>1,"check"=>slug,"upstream_pin"=>"538fce882ab73e3af447f4bc6a1704d290c88aba","source_path"=>path,"source_selector"=>selector,"input_provenance"=>note,"cases"=>cases,"cross_checks"=>cross_checks)
    variant=deepcopy(root)
    modifications=Any[]
    for c in variant["cases"]
        c["mode"]=="api" && continue
        # Change one active finite nonzero component after normalization; never renormalize.
        field=any(!iszero, c["state_real"]) ? "state_real" : "state_imag"
        i=findfirst(x->isfinite(x)&&!iszero(x), c[field])
        i===nothing && error("No active finite state component in $(c["id"])")
        old=c[field][i]; new=nextfloat(nextfloat(old)); c[field][i]=new
        push!(modifications,Dict("case"=>c["id"],"field"=>field,"index_1based"=>i,"before"=>old,"after"=>new,"ulps"=>2))
    end
    for (mode,data) in (("nominal",root),("variant",variant))
        # An explicitly identical API variant must also be byte-identical,
        # including non-scientific metadata, to the nominal fixture.
        data["variant"]=isempty(modifications) ? "nominal" : mode
        data["variant_description"]=isempty(modifications) ? "identical: this official selector tests rejected keyword API outcomes and has no active numerical output" : "Each numerical case changes one active initial-state component by +2 binary64 ULP after normalization; no renormalization. API sentinels remain unchanged."
        data["perturbations"]=mode=="variant" ? modifications : Any[]
        dir=joinpath(OUT,slug,"ic",mode); mkpath(dir)
        open(joinpath(dir,"input.toml"),"w") do io; TOML.print(io,data;sorted=true); end
    end
    push!(ITEMS,Dict("check"=>slug,"source_path"=>path,"source_selector"=>selector,"input_provenance"=>note,"case_ids"=>[c["id"] for c in cases],"case_count"=>length(cases),"variant_identical"=>isempty(modifications)))
end
const TEST="test/timeevolve_tests.jl"
const PREFIX="Adaptive Krylov Time Evolution / "
const RNGNOTE="Original Julia 1.10 shared Random.seed!(11) draw order preserved across all direct selectors; the wide-spectrum selector resets to 42 as upstream. Inputs frozen in TOML; no runtime random generation. Added controls use copies of existing states and consume no draws."
function direct(slug,label,cases;kwargs...)
    emit(slug,TEST,PREFIX*label,cases;note=RNGNOTE,kwargs...)
end

Random.seed!(11)
p=randstate(64); H=xxz(6)
o=opts(tol=1e-12,m_init=25,m_max=50)
direct("operator-dense-reference","Dense reference — Operator path",[
    makecase("single-times",H,p,[0.1,0.5,1.7,-0.0];mode="single",options=o,l2=1e-10,norm_abs=1e-10),
    makecase("time-grid",H,p,collect(range(0,3;length=31));options=o,l2=1e-10,norm_abs=1e-10,requirements=Dict("total_times_served"=>Dict("eq"=>31))),
    makecase("scalar-shift-phase",xxz(6;shift=0.37),p,[0.1,0.5,1.7];options=o,l2=1e-10,norm_abs=1e-10,addition="Independent scalar-energy-shift phase regression: H+0.37I, raw state retained; no phase alignment.")])

A=randn(ComplexF64,40,40); A=(A+A')/2; p=randstate(40); H=dense(A); o=opts(tol=1e-12,m_init=20,m_max=35)
direct("matrix-representations","AbstractMatrix Hamiltonian path",[makecase(repr,H,p,[0.8];mode="single",options=o,l2=1e-10,representation=repr) for repr in ("dense","hermitian","sparse")])

B=TranslationalBasis(L=8,k=0,N=4,base=2,threaded=false); p=randstate(size(B,1))
direct("symmetry-sector","Symmetry sector compatibility",[makecase("sector-times",xxz(8;delta=0.5,flip=1.0,sector=true),p,[0.3,0.9,1.4];options=opts(tol=1e-11,m_init=20,m_max=40),l2=1e-9,norm_abs=1e-9)])

p=randstate(64)
direct("basis-reuse","Reuse actually happens",[makecase("reused-grid",xxz(6),p,collect(range(0,0.4;length=25));options=opts(tol=1e-10,m_init=25,m_max=50),addition="Retain and independently validate all states that upstream discards while checking diagnostic counters.",requirements=Dict("basis_builds"=>Dict("eq"=>1),"restarts"=>Dict("eq"=>0),"total_times_served"=>Dict("eq"=>25)),statuses=Dict("matvec_budget"=>"pass"))])

p=randstate(256); o=opts(tol=1e-10,m_init=6,m_max=6,extend_basis=false)
req=Dict("restarts"=>Dict("min"=>1),"basis_builds"=>Dict("min"=>2))
direct("long-interval-restart","Restart happens on a long interval",[
    makecase("long-grid",xxz(8),p,collect(range(0,20;length=11));options=o,l2=1e-6,requirements=req),
    makecase("nonunit-restart",xxz(8),((3+4im)/2).*p,[0.0,0.7,3.0];options=o,l2=2.5e-6,norm_abs=1e-8,requirements=req,addition="Nonunit initial state (complex factor (3+4i)/2, norm 2.5) across forced restarts exposes hidden normalization and anchor-scale loss.")])

p=randstate(64)
direct("basis-extension","Extension path",[makecase("extended-grid",xxz(6),p,collect(range(0,3;length=15));options=opts(tol=1e-12,m_init=5,m_max=40,extend_step=5,extend_basis=true),l2=1e-9,requirements=Dict("basis_extensions"=>Dict("min"=>1)))])

p=randstate(64); o=opts(tol=1e-12,m_init=20,m_max=35)
direct("explicit-cache-inplace","Explicit cache workflow and in-place variants",[
    makecase("cache-sequential",xxz(6),p,[0.5,1.5];mode="cache",options=o,l2=1e-10,statuses=Dict("reduced_phase_length"=>"pass","reduced_coeffs_length"=>"pass","cache_backward"=>"ErrorException","zero_input"=>"ErrorException")),
    makecase("inplace-single",xxz(6),p,[0.7];mode="inplace",options=o,l2=1e-10)])

p=randstate(64); o=opts(tol=1e-12,m_init=20,m_max=40)
ts=collect(range(0,2;length=9)); perm=[5,1,9,3,7,2,8,4,6]
direct("forward-time-rules","Forward-only time rules",[
    makecase("sorted",xxz(6),p,ts;options=o,l2=1e-9),
    makecase("shuffled",xxz(6),p,ts[perm];options=o,l2=1e-9),
    makecase("rejections",xxz(6),p,Float64[];mode="api",options=o,statuses=Dict("negative_single"=>"ErrorException","negative_multi"=>"ErrorException","unsorted_cache"=>"ErrorException")),
    makecase("duplicate-times",xxz(6),p,[0.7,0.0,0.7,0.2];options=o,l2=1e-9,addition="Repeated and nonuniform output times supplement upstream's shuffled uniform grid."),
    makecase("cache-duplicates",xxz(6),p,[0.0,0.2,0.2,0.7];mode="cache",options=o,l2=1e-9,addition="Repeated forward times in the explicit stateful cache API.")];cross_checks=[Dict("kind"=>"same_state_by_time","case_a"=>"sorted","case_b"=>"shuffled","upstream_l2_bound"=>1e-10)])

p=randstate(16)
direct("removed-hermitian-keyword","hermitian kwarg has been removed",[makecase("removed-keyword",xxz(4),p,Float64[];mode="api",statuses=Dict("cache_hermitian"=>"MethodError","call_hermitian"=>"MethodError"))])

p=randstate(64); o=opts(tol=1e-12,m_init=20,m_max=40)
o_norm=merge(o,Dict("normalize_output"=>true)); nonunit=((3+4im)/2).*p
direct("normalization-contract","normalize_output default does not mask error",[
    makecase("default-normalized-input",xxz(6),p,[1.0];mode="single",options=o,l2=1e-10,norm_abs=1e-10),
    makecase("opt-in-normalized-input",xxz(6),p,[1.0];mode="single",options=o_norm,l2=1e-10,norm_abs=1e-12,addition="Full complex state comparison supplements upstream norm-only check for normalize_output=true."),
    makecase("nonunit-default",xxz(6),nonunit,[0.0,0.3,1.0];options=o,l2=2.5e-10,norm_abs=1e-10,addition="Nonunit complex input exposes accidental normalization with the default option."),
    makecase("nonunit-opt-in",xxz(6),nonunit,[0.0,0.3,1.0];options=o_norm,l2=1e-10,norm_abs=1e-12,addition="Explicit normalize_output=true is checked against normalized independent output."),
    makecase("analytic-diagonal",Dict("kind"=>"diagonal","values"=>[-0.75,1.25]),ComplexF64[0.6,0.3+0.4im],[0.0,0.17,1.3,4.0];options=opts(tol=1e-12,m_init=2,m_max=2),l2=1e-10,norm_abs=1e-10,addition="Two-level analytic componentwise phase control with unequal amplitudes and nonunit norm; no numerical eigensolver is needed for the oracle.")])

Random.seed!(42); U=Matrix(qr(randn(ComplexF64,60,60)).Q); lambda=sort(16 .* rand(60) .- 8)
A=U*Diagonal(lambda)*U'; A=(A+A')/2; p=randstate(60)
direct("wide-spectrum-defect","Defect monitor stress: wide spectral spread",[
    makecase("wide-grid",dense(A),p,collect(range(0,12;length=25));options=opts(tol=1e-10,m_init=25,m_max=50),l2=1e-8,norm_abs=1e-8),
    makecase("wide-single",dense(A),p,[12.0];mode="single",options=opts(tol=1e-10,m_init=20,m_max=40),l2=1e-8,norm_abs=1e-8)])

# Upstream docs do not specify seeds. Each random example gets its own explicit
# seed; system sizes, physical coefficients, times and solver settings are unchanged.
const WORKFLOW="docs/src/examples/time-evolution-workflows.md"
const MANUAL="docs/src/manual/time-evolution.md"
const DOCNOTE="Official runnable example with unchanged system size, model, time grid and solver settings. Initial states are frozen; examples with upstream-unseeded randomness use the explicitly declared deterministic seed. Complete output states add correctness observability to upstream display-only examples."
function doc(slug,path,selector,cases;seed=0)
    emit(slug,path,selector,cases;note=DOCNOTE*" Fixture seed="*string(seed)*" (0 means no randomness).")
end
Random.seed!(1101); p=randstate(1024); o=opts(tol=1e-10,m_init=25,m_max=50)
doc("doc-workflow-full-basis",WORKFLOW,"Example 1: Full-Basis XXZ Dynamics",[makecase("workflow-full-grid",xxz(10),p,collect(range(0,2;length=41));options=o,measure=["magnetization_site1"])];seed=1101)
B=basis(L=12,N=6,k=0); H=xxz(12;delta=0.5,flip=1.0,sector=true)
Random.seed!(1102); p=randstate(size(B,1))
doc("doc-workflow-sector",WORKFLOW,"Example 2: Dynamics In A Symmetry Sector / random state",[makecase("workflow-sector-grid",H,p,[0.2,0.5,1.0,2.0];options=opts(tol=1e-11,m_init=25,m_max=50))];seed=1102)
p=ComplexF64.(productstate([i<=6 ? 1 : 0 for i=1:12],B))
doc("doc-workflow-sector-product",WORKFLOW,"Example 2: Dynamics In A Symmetry Sector / productstate snippet",[makecase("sector-product",H,p,[0.5];mode="single",options=opts(tol=1e-11,m_init=20,m_max=40))])
doc("doc-workflow-cache",WORKFLOW,"Example 3: Driving The Cache Explicitly",[makecase("workflow-cache",xxz(10),neel(10),[0.3,0.8,3.0];mode="cache",options=o)])
doc("doc-manual-full-quench",MANUAL,"Example 1: Full Basis Quench",[
    makecase("manual-single",xxz(10),neel(10),[1.5];mode="single",options=opts(tol=1e-10)),
    makecase("manual-grid",xxz(10),neel(10),collect(range(0,3;length=61));options=o)])
Random.seed!(1103); p=randstate(size(B,1))
doc("doc-manual-sector",MANUAL,"Example 2: Symmetry Sector Dynamics",[makecase("manual-sector",H,p,[0.2,0.5,1.0,2.0];options=opts(tol=1e-11,m_init=25,m_max=50))];seed=1103)
doc("doc-manual-cache",MANUAL,"Example 3: Reusing A Cache Across Calls",[makecase("manual-cache",xxz(10),neel(10),[0.3,0.6,2.0];mode="cache",options=o)])
doc("doc-getting-started","docs/src/getting-started.md","A First Time-Evolution Example",[
    makecase("getting-started-single",xxz(8),neel(8),[1.0];mode="single"),
    makecase("getting-started-grid",xxz(8),neel(8),collect(range(0,2;length=21)))])
doc("doc-matrix-free-operator","docs/src/manual/operators.md","Operator As A Matrix-Free Hamiltonian",[makecase("matrix-free-grid",xxz(10),neel(10),collect(range(0,2;length=21));options=opts(tol=1e-10))])
doc("doc-reference-api","docs/src/reference/time-evolution.md","Example",[
    makecase("reference-single",xxz(10),neel(10),[1.5];mode="single",options=opts(tol=1e-10)),
    makecase("reference-grid",xxz(10),neel(10),collect(range(0,2;length=41));options=o)])
doc("docstring-timeevolve","src/algorithms/TimeEvolution.jl","timeevolve docstring / Example",[
    makecase("docstring-single",xxz(10;delta=1.0),neel(10),[2.0];mode="single",options=opts(tol=1e-10)),
    makecase("docstring-grid",xxz(10;delta=1.0),neel(10),collect(range(0,5;length=51));options=opts(tol=1e-10))])

rng=MersenneTwister(23); A=randn(rng,ComplexF64,3,3); A=(A+A')/2
p=normalize!(randn(rng,ComplexF64,3)); H=dense(A)
emit("lindblad-unitary-integration","test/lindblad_timeevolve_tests.jl","Adaptive Lindblad Arnoldi Evolution / Pure Hamiltonian limit matches unitary density evolution",[
    makecase("density-single",H,p,[1.4];mode="lindblad_single",options=opts(tol=1e-12,m_init=4,m_max=9),l2=1e-10,observable="density",dimension=3,normalize_density=false),
    makecase("unitary-state",H,p,[1.4];mode="single",options=opts(tol=1e-12,m_init=6,m_max=12),l2=1e-10),
    makecase("density-grid",H,p,[0.0,0.2,0.7,1.5];mode="lindblad_multi",options=opts(tol=1e-12,m_init=4,m_max=9),l2=1e-10,observable="density",dimension=3,normalize_density=false,requirements=Dict("total_times_served"=>Dict("eq"=>4))),
    makecase("density-restart",H,p,[5.0];mode="lindblad_cache",options=opts(tol=1e-6,m_init=3,m_max=3,extend_basis=false),l2=5e-6,observable="density",dimension=3,normalize_density=false,requirements=Dict("restarts"=>Dict("min"=>1)))];note="Original selector's local MersenneTwister(23) draw sequence preserved. Full pure-Hamiltonian selector retained; pinned Lindblad subsystem is an unchanged cross-integration dependency, not an optimization target.",cross_checks=[Dict("kind"=>"pure_density","density_case"=>"density-single","state_case"=>"unitary-state","upstream_l2_bound"=>1e-10)])

mkpath(OUT)
open(joinpath(OUT,"manifest.toml"),"w") do io
    TOML.print(io,Dict("schema_version"=>1,"upstream_pin"=>"538fce882ab73e3af447f4bc6a1704d290c88aba","generator_julia"=>string(VERSION),"checks"=>ITEMS);sorted=true)
end
println("Generated ",length(ITEMS)," official check fixtures at ",OUT," (inputs only; no solver or verifier run).")
