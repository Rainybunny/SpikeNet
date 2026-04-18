# SpikeNet C++ vs Python Equivalence Report

- Generated at: 2026-04-18T12:08:33
- Total checks: 52
- Passed: 52
- Failed: 0

## Performance Summary

| Engine | Real Time Total (s) | User Time Total (s) | Torch CPU Time Total (ms) | Torch GPU Time Total (ms) |
|---|---:|---:|---:|---:|
| C++ | 1.130 | 0.910 | N/A | N/A |
| Torch | 14.660 | 32.130 | 24229.059 | 0.000 |

## Executions

| Engine | Case | Return Code | Real (s) | User (s) | Sys (s) | Torch CPU (ms) | Torch GPU (ms) | Output File |
|---|---|---:|---:|---:|---:|---:|---:|---|
| cpp | 0001-core-nosyn-medium_in | 0 | 0.080 | 0.040 | 0.010 |  |  | /home/vullar/Studio/Playground/SpikeNet/reports/equivalence_medium_cpu/cpp/0001-core-nosyn-medium_in/0001-core-nosyn-medium_in_1776485297254_out.h5 |
| cpp | 0002-core-recurrent-medium_in | 0 | 0.810 | 0.710 | 0.020 |  |  | /home/vullar/Studio/Playground/SpikeNet/reports/equivalence_medium_cpu/cpp/0002-core-recurrent-medium_in/0002-core-recurrent-medium_in_1776485301106_out.h5 |
| cpp | 0003-core-twopop-medium_in | 0 | 0.240 | 0.160 | 0.060 |  |  | /home/vullar/Studio/Playground/SpikeNet/reports/equivalence_medium_cpu/cpp/0003-core-twopop-medium_in/0003-core-twopop-medium_in_1776485308262_out.h5 |
| python | 0001-core-nosyn-medium_in | 0 | 3.740 | 2.850 | 0.590 | 312.506 | 0.000 | /home/vullar/Studio/Playground/SpikeNet/reports/equivalence_medium_cpu/python/0001-core-nosyn-medium_in/0001-core-nosyn-medium_in_1776485300360_out.h5 |
| python | 0002-core-recurrent-medium_in | 0 | 6.300 | 23.090 | 1.950 | 20333.106 | 0.000 | /home/vullar/Studio/Playground/SpikeNet/reports/equivalence_medium_cpu/python/0002-core-recurrent-medium_in/0002-core-recurrent-medium_in_1776485307488_out.h5 |
| python | 0003-core-twopop-medium_in | 0 | 4.620 | 6.190 | 0.820 | 3583.447 | 0.000 | /home/vullar/Studio/Playground/SpikeNet/reports/equivalence_medium_cpu/python/0003-core-twopop-medium_in/0003-core-twopop-medium_in_1776485312328_out.h5 |

## Detailed Checks

| Case | Path | Status | Detail | Max Abs | Max Rel |
|---|---|---|---|---:|---:|
| 0001-core-nosyn-medium_in | CLI::Number of input files: | PASS | cpp=True, py=True |  |  |
| 0001-core-nosyn-medium_in | CLI::Processing input file No.1 out of 1... | PASS | cpp=True, py=True |  |  |
| 0001-core-nosyn-medium_in | CLI::Data file name is: | PASS | cpp=True, py=True |  |  |
| 0001-core-nosyn-medium_in | CLI::The planet earth is blue and there's nothing I can do. | PASS | cpp=True, py=True |  |  |
| 0001-core-nosyn-medium_in | CLI::exit_code | PASS | cpp=0, py=0 |  |  |
| 0001-core-nosyn-medium_in | /config_filename/config_filename | PASS | present in both outputs |  |  |
| 0001-core-nosyn-medium_in | /run_away_killed/step | PASS | present in both outputs |  |  |
| 0001-core-nosyn-medium_in | /pop_result_0/spike_hist_tot | PASS | integer exact match |  |  |
| 0001-core-nosyn-medium_in | /pop_result_0/num_spikes_pop | PASS | integer exact match |  |  |
| 0001-core-nosyn-medium_in | /pop_result_0/num_ref_pop | PASS | integer exact match |  |  |
| 0001-core-nosyn-medium_in | /pop_result_0/stats_V_mean | PASS | allclose | 2.558e-13 | 3.655e-15 |
| 0001-core-nosyn-medium_in | /pop_result_0/stats_V_std | PASS | allclose | 3.048e-14 | 3.652e-11 |
| 0001-core-nosyn-medium_in | /pop_result_0/stats_I_input_mean | PASS | allclose | 0.000e+00 | 0.000e+00 |
| 0001-core-nosyn-medium_in | /pop_result_0/stats_I_input_std | PASS | allclose | 0.000e+00 | 0.000e+00 |
| 0002-core-recurrent-medium_in | CLI::Number of input files: | PASS | cpp=True, py=True |  |  |
| 0002-core-recurrent-medium_in | CLI::Processing input file No.1 out of 1... | PASS | cpp=True, py=True |  |  |
| 0002-core-recurrent-medium_in | CLI::Data file name is: | PASS | cpp=True, py=True |  |  |
| 0002-core-recurrent-medium_in | CLI::The planet earth is blue and there's nothing I can do. | PASS | cpp=True, py=True |  |  |
| 0002-core-recurrent-medium_in | CLI::exit_code | PASS | cpp=0, py=0 |  |  |
| 0002-core-recurrent-medium_in | /config_filename/config_filename | PASS | present in both outputs |  |  |
| 0002-core-recurrent-medium_in | /run_away_killed/step | PASS | present in both outputs |  |  |
| 0002-core-recurrent-medium_in | /pop_result_0/spike_hist_tot | PASS | integer exact match |  |  |
| 0002-core-recurrent-medium_in | /pop_result_0/num_spikes_pop | PASS | integer exact match |  |  |
| 0002-core-recurrent-medium_in | /pop_result_0/num_ref_pop | PASS | integer exact match |  |  |
| 0002-core-recurrent-medium_in | /pop_result_0/stats_V_mean | PASS | allclose | 1.137e-13 | 1.932e-15 |
| 0002-core-recurrent-medium_in | /pop_result_0/stats_V_std | PASS | allclose | 1.279e-13 | 5.491e-14 |
| 0002-core-recurrent-medium_in | /pop_result_0/stats_I_input_mean | PASS | allclose | 1.990e-13 | 2.433e-15 |
| 0002-core-recurrent-medium_in | /pop_result_0/stats_I_input_std | PASS | allclose | 1.954e-14 | 5.762e-15 |
| 0002-core-recurrent-medium_in | /syn_result_0/stats_I_mean | PASS | allclose | 1.990e-13 | 2.433e-15 |
| 0003-core-twopop-medium_in | CLI::Number of input files: | PASS | cpp=True, py=True |  |  |
| 0003-core-twopop-medium_in | CLI::Processing input file No.1 out of 1... | PASS | cpp=True, py=True |  |  |
| 0003-core-twopop-medium_in | CLI::Data file name is: | PASS | cpp=True, py=True |  |  |
| 0003-core-twopop-medium_in | CLI::The planet earth is blue and there's nothing I can do. | PASS | cpp=True, py=True |  |  |
| 0003-core-twopop-medium_in | CLI::exit_code | PASS | cpp=0, py=0 |  |  |
| 0003-core-twopop-medium_in | /config_filename/config_filename | PASS | present in both outputs |  |  |
| 0003-core-twopop-medium_in | /run_away_killed/step | PASS | present in both outputs |  |  |
| 0003-core-twopop-medium_in | /pop_result_0/spike_hist_tot | PASS | integer exact match |  |  |
| 0003-core-twopop-medium_in | /pop_result_0/num_spikes_pop | PASS | integer exact match |  |  |
| 0003-core-twopop-medium_in | /pop_result_0/num_ref_pop | PASS | integer exact match |  |  |
| 0003-core-twopop-medium_in | /pop_result_0/stats_V_mean | PASS | allclose | 1.990e-13 | 2.835e-15 |
| 0003-core-twopop-medium_in | /pop_result_0/stats_V_std | PASS | allclose | 1.721e-14 | 6.882e-12 |
| 0003-core-twopop-medium_in | /pop_result_0/stats_I_input_mean | PASS | allclose | 1.554e-15 | 3.674e-15 |
| 0003-core-twopop-medium_in | /pop_result_0/stats_I_input_std | PASS | allclose | 2.220e-16 | 4.738e-15 |
| 0003-core-twopop-medium_in | /pop_result_1/spike_hist_tot | PASS | integer exact match |  |  |
| 0003-core-twopop-medium_in | /pop_result_1/num_spikes_pop | PASS | integer exact match |  |  |
| 0003-core-twopop-medium_in | /pop_result_1/num_ref_pop | PASS | integer exact match |  |  |
| 0003-core-twopop-medium_in | /pop_result_1/stats_V_mean | PASS | allclose | 2.274e-13 | 3.256e-15 |
| 0003-core-twopop-medium_in | /pop_result_1/stats_V_std | PASS | allclose | 1.599e-14 | 1.000e+00 |
| 0003-core-twopop-medium_in | /pop_result_1/stats_I_input_mean | PASS | allclose | 1.776e-15 | 2.848e-15 |
| 0003-core-twopop-medium_in | /pop_result_1/stats_I_input_std | PASS | allclose | 2.220e-15 | 3.986e-15 |
| 0003-core-twopop-medium_in | /syn_result_0/stats_I_mean | PASS | allclose | 1.776e-15 | 2.848e-15 |
| 0003-core-twopop-medium_in | /syn_result_1/stats_I_mean | PASS | allclose | 1.554e-15 | 3.674e-15 |