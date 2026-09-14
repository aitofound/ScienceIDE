# 写手简报 — gkeyll-vlasov

模块:Vlasov-Maxwell and Vlasov-Poisson DG Solvers

**可变异的源文件(1 个,模块只编译这些)**
  vlasov/

**死代码 / 不可达(2 条,永远不要在这里出题)**
  - Fluid moment evolution is owned by the fluid/MHD module.
  - Gyrokinetic and PKPM reduced kinetic models are separate modules.

**坑(2 条)**
  ! The generated kernel set is very large and a complete laptop CPU build exceeded the bounded investigation window.
  ! GPU and distributed-memory behavior were not measured locally.

## can-pb-annulus-sodshock-1x2v-p1

- 官方测试源:`code/gkeyll/vlasov/creg/rt_can_pb_bgk_surf_annulus_sodshock_im_1x2v_p1.c`
- 活配置(决定哪些分支被编译/执行):Upstream P1 1x2v Sod shock on an annular surface (128 radial cells, 12x12 velocity cells) through t=0.1 with implicit BGK collisions at nu=15000 and reflecting radial boundaries.
- 判分观测量(缺陷必须动到它):the complete neutral integrated-moment and distribution-L2 histories plus the final energy-moment frame
- 容差 atol=1e-11;噪声地板=8.21565e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 53.2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=7.77156e-15

## can-pb-cylindrical-sodshock-2x3v-p1

- 官方测试源:`code/gkeyll/vlasov/creg/rt_can_pb_bgk_surf_cylindrical_sodshock_im_2x3v_p1.c`
- 活配置(决定哪些分支被编译/执行):Upstream P1 2x3v Sod shock on a cylindrical surface (32x1 configuration cells, 4x4x4 velocity cells) through t=0.1 with implicit BGK collisions at nu=15000 and reflecting radial boundaries.
- 判分观测量(缺陷必须动到它):the complete neutral integrated-moment and distribution-L2 histories plus the final energy-moment frame
- 容差 atol=1e-11;噪声地板=2.79776e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 41s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=4.4853e-14

## can-pb-explicit-bgk-flat

- 官方测试源:`code/gkeyll/vlasov/creg/rt_can_pb_ex_bgk_surf_flat.c`
- 活配置(决定哪些分支被编译/执行):Upstream P2 2x2v BGK relaxation on a flat metric (2x2 configuration cells, 8x8 velocity cells) through t=0.1 with the explicit BGK scheme at nu=15000.
- 判分观测量(缺陷必须动到它):the complete neutral integrated-moment and distribution-L2 histories
- 容差 atol=1e-11;噪声地板=3.35287e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 30s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=1.07914e-13

## can-pb-implicit-bgk-flat

- 官方测试源:`code/gkeyll/vlasov/creg/rt_can_pb_im_bgk_surf_flat.c`
- 活配置(决定哪些分支被编译/执行):The implicit twin of can-pb-explicit-bgk-flat: the same P2 2x2v flat-metric relaxation through t=0.1 with the implicit BGK scheme, which takes far fewer steps at nu=15000.
- 判分观测量(缺陷必须动到它):the complete neutral integrated-moment and distribution-L2 histories
- 容差 atol=1e-11;噪声地板=8.88178e-16 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 2.2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=1.77636e-15

## can-pb-implicit-bgk-sodshock-1x1v-p2

- 官方测试源:`code/gkeyll/vlasov/creg/rt_can_pb_neut_bgk_sodshock_im_1x1v_p2.c`
- 活配置(决定哪些分支被编译/执行):Upstream P2 1x1v neutral Sod shock on 128x32 cells through t=0.1 in the canonical Poisson-bracket model with the implicit BGK collision scheme at nu=15000.
- 判分观测量(缺陷必须动到它):the complete neutral integrated-moment and distribution-L2 histories plus the final energy-moment frame
- 容差 atol=1e-11;噪声地板=4.10783e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 11.5s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=8.43769e-15

## can-pb-newtonian-orbits-2x2v-p2

- 官方测试源:`code/gkeyll/vlasov/creg/rt_can_pb_newtonian_orbits_2x2v_p2.c`
- 活配置(决定哪些分支被编译/执行):Upstream P2 2x2v collisionless Newtonian orbits around a point mass in polar coordinates (16x32 configuration cells, 8x32 velocity cells) through t=0.001 with absorbing radial boundaries.
- 判分观测量(缺陷必须动到它):the neutral integrated-moment and distribution-L2 histories plus the final density and Hamiltonian-derived momentum frames
- 容差 atol=1e-11;噪声地板=2.42861e-16 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 14.2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=9.71445e-17

## can-pb-sphere-khi-2x2v-p2

- 官方测试源:`code/gkeyll/vlasov/creg/rt_can_pb_bgk_surf_sphere_khi_im_2x2v_p2.c`
- 活配置(决定哪些分支被编译/执行):Upstream P2 2x2v Kelvin-Helmholtz shear on a spherical surface (32x32 angular cells, 8x8 velocity cells) through t=0.01 with implicit BGK collisions at nu=15000.
- 判分观测量(缺陷必须动到它):the complete neutral integrated-moment and distribution-L2 histories
- 容差 atol=1e-11;噪声地板=2.30926e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 59.6s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=2.13163e-14

## dg-advection-2x-p2

- 官方测试源:`code/gkeyll/vlasov/creg/rt_dg_advect_2x_p2.c`
- 活配置(决定哪些分支被编译/执行):Upstream P2 two-dimensional DG scalar advection of a cylinder (16x16 cells) through one rotation period as a fluid species of the vlasov app.
- 判分观测量(缺陷必须动到它):the final scalar frame
- 容差 atol=1e-11;噪声地板=1.77636e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1.1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=2.9976e-15

## dg-applied-acceleration-1x1v

- 官方测试源:`code/gkeyll/vlasov/creg/rt_dg_accel_1x1v.c`
- 活配置(决定哪些分支被编译/执行):Upstream P2 1x1v electron distribution under a prescribed sinusoidal applied acceleration with a static field (32x24 cells) through t=3.
- 判分观测量(缺陷必须动到它):the final electron distribution frame, its density, momentum and energy moment frames and the final field frame
- 容差 atol=1e-11;噪声地板=2.66454e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 1.2s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=4.55191e-15

## dg-diffusion-general-3x

- 官方测试源:`code/gkeyll/vlasov/creg/rt_dg_diffusion_gen_3x.c`
- 活配置(决定哪些分支被编译/执行):Upstream P2 three-dimensional DG diffusion with a general (full-tensor) diffusion coefficient (16x16x16 cells) through t=0.01 as a fluid species of the vlasov app.
- 判分观测量(缺陷必须动到它):the final scalar frame
- 容差 atol=1e-11;噪声地板=1.33227e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 32.1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=2.22045e-15

## dg-euler-sodshock-p2

- 官方测试源:`code/gkeyll/vlasov/creg/rt_dg_euler_sodshock_p2.c`
- 活配置(决定哪些分支被编译/执行):Upstream P2 DG Euler Sod shock (512 cells) through t=0.1 as a fluid species of the vlasov app.
- 判分观测量(缺陷必须动到它):the final conserved-variable and primitive-variable frames of the fluid species
- 容差 atol=1e-07;噪声地板=8.16492e-10 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 4.3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=3.43519e-10

## dg-five-moment-beach-p2

- 官方测试源:`code/gkeyll/vlasov/creg/rt_dg_5m_mom_beach_p2.c`
- 活配置(决定哪些分支被编译/执行):Upstream P2 plasma-beach problem (200 cells, 5 ns, SI units): a DG five-moment electron fluid driven by an applied current against a density ramp, coupled to the Maxwell field.
- 判分观测量(缺陷必须动到它):the final electron five-moment frame, the final field frame and the complete field-energy history
- 容差 atol=1e-08;噪声地板=2.43722e-12 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 9.4s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=5.44134e-11

## dg-hyperdiffusion4-3x

- 官方测试源:`code/gkeyll/vlasov/creg/rt_dg_diffusion4_const_3x.c`
- 活配置(决定哪些分支被编译/执行):Upstream P2 three-dimensional fourth-order (hyper-)diffusion with a constant coefficient (4x4x4 cells) through t=0.1 as a fluid species of the vlasov app.
- 判分观测量(缺陷必须动到它):the final scalar frame
- 容差 atol=1e-11;噪声地板=2.22045e-16 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 4s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=1.11022e-15

## dg-maxwell-waveguide-2d

- 官方测试源:`code/gkeyll/vlasov/creg/rt_dg_maxwell_wg_2d.c`
- 活配置(决定哪些分支被编译/执行):Upstream P2 two-dimensional DG Maxwell waveguide mode (70x50 cells) through ten periods with no kinetic species.
- 判分观测量(缺陷必须动到它):the final field frame and the complete field-energy history
- 容差 atol=1e-11;噪声地板=2.54019e-13 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 13.4s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=1.89626e-13

## gr-schwarzschild-geodesics

- 官方测试源:`code/gkeyll/vlasov/creg/rt_gr_can_pb_schwarzschild_bh_geodesics.c`
- 活配置(决定哪些分支被编译/执行):Upstream P2 2x2v geodesic motion in the Schwarzschild spacetime (32x32 configuration cells, 32x32 velocity cells, radii 5 to 25) through t=0.1 with absorbing radial boundaries.
- 判分观测量(缺陷必须动到它):the neutral integrated-moment and distribution-L2 histories plus the final density and Hamiltonian-derived momentum frames
- 容差 atol=1e-11;噪声地板=8.8124e-16 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 58s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=7.99193e-17

## vlasov-bgk-relaxation

- 官方测试源:`code/gkeyll/vlasov/creg/rt_vlasov_bgk_relax_1x1v_p2.c`
- 活配置(决定哪些分支被编译/执行):Upstream P2 top-hat-plus-bump BGK relaxation problem to t=500 without a field solve.
- 判分观测量(缺陷必须动到它):the complete square and bump species integrated-moment and distribution-L2 histories
- 容差 atol=1e-11;噪声地板=4.88498e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 9.3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=9.54792e-14

## vlasov-bgk-sodshock-1x2v-p2

- 官方测试源:`code/gkeyll/vlasov/creg/rt_vlasov_neut_bgk_sodshock_1x2v_p2.c`
- 活配置(决定哪些分支被编译/执行):Upstream P2 1x2v neutral Sod shock in the classic Vlasov app (32x16x16 cells) through t=0.1 with explicit BGK collisions at nu=100 and the LTE projection.
- 判分观测量(缺陷必须动到它):the complete neutral integrated-moment and distribution-L2 histories
- 容差 atol=1e-11;噪声地板=1.33227e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 35.1s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=1.33227e-15

## vlasov-electrostatic-shock

- 官方测试源:`code/gkeyll/vlasov/creg/rt_vlasov_es_shock.c`
- 活配置(决定哪些分支被编译/执行):Upstream electron-ion one-dimensional Vlasov-Poisson electrostatic-shock problem to t=20.
- 判分观测量(缺陷必须动到它):the complete electron and ion integrated-moment and distribution-L2 histories plus electrostatic field energy
- 容差 atol=1e-11;噪声地板=7.63976e-11 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 11s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=1.01863e-10

## vlasov-em-advection

- 官方测试源:`code/gkeyll/vlasov/creg/rt_vlasov_em_advect_1x3v_p1.c`
- 活配置(决定哪些分支被编译/执行):Upstream P1 1x3v electromagnetic-advection problem on 2x16x16x16 cells through t=10.
- 判分观测量(缺陷必须动到它):the complete electron integrated-moment and distribution-L2 histories, plus the field-energy history, identically zero in this problem (static self-consistent field, external Ez only), kept as a length and zero guard
- 容差 atol=1e-11;噪声地板=1.42109e-13 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 41.9s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=1.13687e-13

## vlasov-landau-damping

- 官方测试源:`code/gkeyll/vlasov/creg/rt_vlasov_landau_damping_1x1v_p2.c`
- 活配置(决定哪些分支被编译/执行):Upstream P2 one-configuration/one-velocity Landau-damping problem to t=20 with LBO collisions.
- 判分观测量(缺陷必须动到它):the complete electron integrated-moment, distribution-L2, and electrostatic field-energy histories
- 容差 atol=1e-11;噪声地板=8.88178e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 4s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=2.13163e-14

## vlasov-lbo-cross-species-1x1v-p2

- 官方测试源:`code/gkeyll/vlasov/creg/rt_vlasov_lbo_cross_1x1v_p2.c`
- 活配置(决定哪些分支被编译/执行):Upstream P2 1x1v relaxation of two neutral species with a 20:1 mass ratio (16x32 cells) through t=0.0025 with self and cross-species LBO collisions.
- 判分观测量(缺陷必须动到它):the complete integrated-moment and distribution-L2 histories of both species
- 容差 atol=1e-11;噪声地板=2.4869e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 3.7s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=2.84217e-14

## vlasov-lbo-wall

- 官方测试源:`code/gkeyll/vlasov/creg/rt_vlasov_neut_lbo_wall.c`
- 活配置(决定哪些分支被编译/执行):Upstream P2 1x1v drifting neutral gas hitting reflecting walls (128x16 cells) through t=0.3 with LBO collisions at nu=10.
- 判分观测量(缺陷必须动到它):the complete neutral integrated-moment and distribution-L2 histories
- 容差 atol=1e-11;噪声地板=6.21725e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 6.8s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=5.77316e-15

## vlasov-sheath

- 官方测试源:`code/gkeyll/vlasov/creg/rt_vlasov_sheath_1x1v_p2.c`
- 活配置(决定哪些分支被编译/执行):Upstream P2 1x1v electron-ion sheath on 128x32 cells through ten inverse electron-plasma frequencies.
- 判分观测量(缺陷必须动到它):the complete electron and ion integrated-moment and distribution-L2 histories plus electrostatic field energy
- 容差 atol=1e-11;噪声地板=1.64927e+12 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 47.7s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=4.59046e+13

## vlasov-sr-bgk-sodshock-1x1v-p2

- 官方测试源:`code/gkeyll/vlasov/creg/rt_vlasov_sr_neut_bgk_sodshock_1x1v_p2.c`
- 活配置(决定哪些分支被编译/执行):Upstream P2 1x1v special-relativistic neutral Sod shock (128x32 cells) through t=0.1 with BGK collisions at nu=100 and the relativistic LTE projection.
- 判分观测量(缺陷必须动到它):the complete neutral integrated-moment and distribution-L2 histories
- 容差 atol=1e-11;噪声地板=1.44329e-15 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 11.6s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=9.99201e-16

## vlasov-sr-two-stream-1x1v

- 官方测试源:`code/gkeyll/vlasov/creg/rt_vlasov_sr_twostream_1x1v.c`
- 活配置(决定哪些分支被编译/执行):Upstream P2 1x1v special-relativistic two-stream instability (64x64 cells, drift 0.9c) through t=100 with self-consistent Vlasov-Maxwell coupling.
- 判分观测量(缺陷必须动到它):the complete electron integrated-moment, distribution-L2 and field-energy histories
- 容差 atol=1e-10;噪声地板=2.74003e-13 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 12.5s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=2.19025e-12

## vlasov-sr-weibel

- 官方测试源:`code/gkeyll/vlasov/creg/rt_vlasov_sr_weibel_1x3v.c`
- 活配置(决定哪些分支被编译/执行):Upstream P2 special-relativistic 1x3v Weibel problem on 24x12x12x12 cells through t=10.
- 判分观测量(缺陷必须动到它):the complete relativistic electron integrated-moment, distribution-L2, and self-consistent electromagnetic field-energy histories
- 容差 atol=1e-10;噪声地板=5.32907e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 67.6s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=5.71987e-13

## vlasov-two-stream

- 官方测试源:`code/gkeyll/vlasov/creg/rt_vlasov_twostream_p2.c`
- 活配置(决定哪些分支被编译/执行):Upstream P2 one-configuration/one-velocity collisionless two-stream instability to t=100.
- 判分观测量(缺陷必须动到它):the complete electron integrated-moment, distribution-L2, and electrostatic field-energy histories
- 容差 atol=2e-05;噪声地板=4.72337e-08 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 20s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=7.86199e-08

## vlasov-weibel

- 官方测试源:`code/gkeyll/vlasov/creg/rt_vlasov_weibel_1x2v_p2.c`
- 活配置(决定哪些分支被编译/执行):Upstream P2 1x2v self-consistent Weibel problem on 24x12x12 cells through t=80.
- 判分观测量(缺陷必须动到它):the complete electron integrated-moment, distribution-L2, and self-consistent electromagnetic field-energy histories
- 容差 atol=1e-10;噪声地板=3.12639e-13 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 6.4s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=3.62377e-13

## vlasov-weibel-2x2v-p1

- 官方测试源:`code/gkeyll/vlasov/creg/rt_vlasov_weibel_2x2v_p1.c`
- 活配置(决定哪些分支被编译/执行):Upstream P1 2x2v Weibel instability (8x8 configuration cells, 16x16 velocity cells) through t=80 with self-consistent Vlasov-Maxwell coupling.
- 判分观测量(缺陷必须动到它):the complete electron integrated-moment, distribution-L2 and field-energy histories
- 容差 atol=1e-09;噪声地板=1.15335e-10 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 67.4s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=7.37771e-10

## vlasov-weibel-lbo-2x2v-p2

- 官方测试源:`code/gkeyll/vlasov/creg/rt_vlasov_weibel_lbo_2x2v_p2.c`
- 活配置(决定哪些分支被编译/执行):Upstream P2 2x2v Weibel instability with LBO collisions (8x8 configuration cells, 16x16 velocity cells) through t=5.
- 判分观测量(缺陷必须动到它):the complete electron integrated-moment, distribution-L2 and field-energy histories
- 容差 atol=1e-11;噪声地板=1.13687e-13 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 37.5s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=5.11591e-13

## vp-emission-spectrum-1x1v-p2

- 官方测试源:`code/gkeyll/vlasov/creg/rt_vlasov_poisson_emission_spectrum_1x1v_p2.c`
- 活配置(决定哪些分支被编译/执行):Upstream P2 1x1v electron emission problem through the Vlasov-Poisson app (128x32 cells, ten inverse plasma frequencies): a reflecting lower wall, an emitting upper electron boundary with a secondary-emission spectrum, an absorbing ion wall and a boundary-flux source, in SI units.
- 判分观测量(缺陷必须动到它):the electron and ion integrated-moment histories, the field energy and the final emitted-electron boundary frame
- 容差 atol=1e-09;噪声地板=3.84829e+12 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 4.3s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=5.49756e+12

## vp-landau-damping-1x1v-p2

- 官方测试源:`code/gkeyll/vlasov/creg/rt_vp_landau_damping_1x1v_p2.c`
- 活配置(决定哪些分支被编译/执行):Upstream P2 1x1v Landau damping through the Vlasov-Poisson app (32x32 cells, 100 inverse plasma frequencies) with explicit Poisson boundary conditions.
- 判分观测量(缺陷必须动到它):the complete electron integrated-moment, distribution-L2 and field-energy histories
- 容差 atol=1e-11;噪声地板=1.77636e-14 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 9.4s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=5.9952e-14

## vp-sheath-1x1v-p2

- 官方测试源:`code/gkeyll/vlasov/creg/rt_vp_sheath_1x1v_p2.c`
- 活配置(决定哪些分支被编译/执行):Upstream P2 1x1v electron-ion sheath through the Vlasov-Poisson app (64x16 cells, 100 inverse plasma frequencies) with absorbing lower and reflecting upper species boundaries and Dirichlet/Neumann Poisson boundary conditions, in SI units.
- 判分观测量(缺陷必须动到它):the complete electron and ion integrated-moment and distribution-L2 histories plus the electrostatic field energy
- 容差 atol=1e-10;噪声地板=7.4217e+13 —— 症状小于容差 = marginal,漏斗必杀
- 参考耗时 6.8s（rubric） —— straw 超时按**缺陷版自己**的耗时定,这只是起点
- 上游测得 floor=2.15504e+14
