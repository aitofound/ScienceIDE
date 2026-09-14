#!/usr/bin/env julia
# Solve one self-contained frozen check. Scientific tolerances are owned by the
# trusted Python oracle/rubric, not by this candidate-side data producer.
using EDKit, LinearAlgebra, SparseArrays, TOML

length(ARGS)==2 || error("Usage: julia --project=ENV run_case.jl INPUT.toml OUT/result.toml")
const INPUT=TOML.parsefile(ARGS[1])
INPUT["schema_version"]==1 || error("Unsupported input schema")
const TIME_SCALE=parse(Float64,get(ENV,"SAB_TIME_SCALE","1.0"))
isfinite(TIME_SCALE) && 0<TIME_SCALE<=1 || error("SAB_TIME_SCALE must be finite and in (0,1]")

function matrix_rows(re,im)
    nr=length(re); nc=length(first(re)); A=Matrix{ComplexF64}(undef,nr,nc)
    for i=1:nr, j=1:nc; A[i,j]=complex(re[i][j],im[i][j]); end
    A
end
function build_hamiltonian(h)
    kind=h["kind"]
    if kind in ("xxz","xxz_sector")
        h["periodic"] || error("These official fixtures require periodic bonds")
        L=h["L"]
        B=kind=="xxz" ? TensorBasis(L=L,base=2) : TranslationalBasis(L=L,N=h["N"],k=h["k"],base=2,threaded=false)
        # Local construction deliberately exercises pinned EDKit spin/Operator.
        bond=get(h,"spin_form","cartesian")=="cartesian" ? spin((2*h["flip"],"xx"),(2*h["flip"],"yy"),(h["delta"],"zz")) : spin((h["flip"],"+-"),(h["flip"],"-+"),(h["delta"],"zz"))
        H=trans_inv_operator(bond,1:2,B)
        shift=get(h,"shift",0.0)
        iszero(shift) || (H=H+operator(spin(shift,"1"),[1],B))
        return H
    elseif kind=="dense"
        A=matrix_rows(h["real"],h["imag"])
        return A+get(h,"shift",0.0)*I
    elseif kind=="diagonal"
        return Diagonal(Float64.(h["values"]).+get(h,"shift",0.0))
    end
    error("Unknown Hamiltonian kind: $kind")
end
function diag_dict(d)
    names=(:basis_builds,:basis_extensions,:restarts,:matvecs,:max_dim_used,:total_times_served,:liouvillian_applies)
    Dict{String,Any}(string(n)=>getproperty(d,n) for n in names if hasproperty(d,n))
end
exception_name(f)=try f(); "no_exception" catch e; string(nameof(typeof(e))) end
function run_one(c)
    H=build_hamiltonian(c["hamiltonian"])
    representation=get(c,"representation","")
    representation=="hermitian" && (H=Hermitian(H))
    representation=="sparse" && (H=sparse(H))
    p=complex.(Float64.(c["state_real"]),Float64.(c["state_imag"]))
    ts=TIME_SCALE .* Float64.(c["times"]); mode=c["mode"]
    kw=(Symbol(k)=>v for (k,v) in c["options"])
    options=(;kw...)
    states=Vector{Vector{ComplexF64}}(); statuses=Dict{String,Any}(); diagnostics=Dict{String,Any}()
    cache=nothing
    started=time_ns()
    if mode=="single"
        for t in ts
            s,d=timeevolve(H,p,t;options...,return_diagnostics=true)
            push!(states,ComplexF64.(s)); diagnostics=diag_dict(d)
        end
    elseif mode=="multi"
        S,d=timeevolve(H,p,ts;options...,return_diagnostics=true)
        states=[ComplexF64.(S[:,j]) for j in axes(S,2)]; diagnostics=diag_dict(d)
    elseif mode=="cache"
        cache=KrylovEvolutionCache(H,p;options...)
        statuses["reduced_phase_length"]=length(cache.reduced_phase)==cache.m ? "pass" : "fail"
        statuses["reduced_coeffs_length"]=length(cache.reduced_coeffs)==cache.m ? "pass" : "fail"
        for t in ts; push!(states,ComplexF64.(timeevolve!(cache,t))); end
        diagnostics=diag_dict(cache.diagnostics)
    elseif mode=="inplace"
        for t in ts
            out=fill(ComplexF64(NaN,NaN),length(p))
            timeevolve!(out,H,p,t;options...); push!(states,out)
        end
    elseif startswith(mode,"lindblad_")
        lb=lindblad(H,Matrix{ComplexF64}[]); rho=densitymatrix(p)
        if mode=="lindblad_single"
            for t in ts
                s,d=lindblad_timeevolve(lb,rho,t;options...,return_diagnostics=true)
                push!(states,vec(ComplexF64.(s.ρ))); diagnostics=diag_dict(d)
            end
        elseif mode=="lindblad_multi"
            S,d=lindblad_timeevolve(lb,rho,ts;options...,return_diagnostics=true)
            states=[vec(ComplexF64.(s.ρ)) for s in S]; diagnostics=diag_dict(d)
        elseif mode=="lindblad_cache"
            cache=LindbladArnoldiCache(lb,rho;options...)
            for t in ts; push!(states,vec(ComplexF64.(lindblad_timeevolve!(cache,t).ρ))); end
            diagnostics=diag_dict(cache.diagnostics)
        else
            error("Unknown density mode $mode")
        end
    elseif mode!="api"
        error("Unknown mode $mode")
    end
    for name in keys(c["expected_statuses"])
        name in ("reduced_phase_length","reduced_coeffs_length") && continue
        if name=="matvec_budget"
            # Record upstream work-count coverage without requiring it from a port.
            statuses[name]=haskey(diagnostics,"matvecs") && haskey(diagnostics,"max_dim_used") ?
                (diagnostics["matvecs"]<=diagnostics["max_dim_used"] ? "pass" : "fail") : "not-reported"
        elseif name=="cache_backward"
            statuses[name]=exception_name(()->timeevolve!(cache,0.1*TIME_SCALE))
        elseif name=="zero_input"
            statuses[name]=exception_name(()->KrylovEvolutionCache(H,zeros(ComplexF64,length(p))))
        elseif name=="negative_single"
            statuses[name]=exception_name(()->timeevolve(H,p,-0.3*TIME_SCALE;tol=1e-12))
        elseif name=="negative_multi"
            statuses[name]=exception_name(()->timeevolve(H,p,TIME_SCALE.*[-0.1,0.3];tol=1e-12))
        elseif name=="unsorted_cache"
            cc=KrylovEvolutionCache(H,p;options...)
            shuffled=TIME_SCALE.*collect(range(0,2;length=9))[[5,1,9,3,7,2,8,4,6]]
            out=Matrix{ComplexF64}(undef,length(p),length(shuffled))
            statuses[name]=exception_name(()->timeevolve!(out,cc,shuffled))
        elseif name=="cache_hermitian"
            statuses[name]=exception_name(()->KrylovEvolutionCache(H,p;hermitian=true))
        elseif name=="call_hermitian"
            statuses[name]=exception_name(()->timeevolve(H,p,0.1;hermitian=false))
        else
            error("Unknown expected status $name")
        end
    end
    elapsed=(time_ns()-started)/1e9
    # Only requested statuses are part of this check's declared contract.
    statuses=Dict(k=>statuses[k] for k in keys(c["expected_statuses"]))
    result=Dict{String,Any}("id"=>c["id"],"statuses"=>statuses,"diagnostics"=>diagnostics)
    if mode!="api"
        result["times"]=ts
        result["states_real"]=[real.(s) for s in states]
        result["states_imag"]=[imag.(s) for s in states]
        if "magnetization_site1" in get(c,"measure",String[])
            Z=operator(spin("z"),[1],H.B)
            result["observables"]=Dict("magnetization_site1"=>[real(dot(s,Z*s)) for s in states])
        end
    end
    result,elapsed
end

measured=[run_one(c) for c in INPUT["cases"]]
output=Dict("schema_version"=>1,"check"=>INPUT["check"],"cases"=>[first(r) for r in measured])
mkpath(dirname(abspath(ARGS[2])))
open(ARGS[2],"w") do io; TOML.print(io,output;sorted=true); end
println("EDKIT_SOLVER_SECONDS=",sum(last(r) for r in measured))
println("EDKIT_TIMING_NOTE=solver calls include first-use JIT; Hamiltonian assembly and output serialization excluded")
println("Wrote complete states to ",ARGS[2])
