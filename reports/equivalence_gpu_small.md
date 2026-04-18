# SpikeNet C++ vs Python Equivalence Report

- Generated at: 2026-04-18T12:03:54
- Total checks: 52
- Passed: 52
- Failed: 0

## Performance Summary

| Engine | Real Time Total (s) | User Time Total (s) | Torch CPU Time Total (ms) | Torch GPU Time Total (ms) |
|---|---:|---:|---:|---:|
| C++ | 0.100 | 0.060 | N/A | N/A |
| Torch | 28.420 | 19.670 | 2526.368 | 0.000 |

## Executions

| Engine | Case | Return Code | Real (s) | User (s) | Sys (s) | Torch CPU (ms) | Torch GPU (ms) | Output File |
|---|---|---:|---:|---:|---:|---:|---:|---|
| cpp | 0001-core-nosyn_in | 0 | 0.030 | 0.010 | 0.010 |  |  | /home/vullar/Studio/Playground/SpikeNet/reports/equivalence_gpu_small/cpp/0001-core-nosyn_in/0001-core-nosyn_in_1776485006048_out.h5 |
| cpp | 0002-core-recurrent_in | 0 | 0.030 | 0.030 | 0.000 |  |  | /home/vullar/Studio/Playground/SpikeNet/reports/equivalence_gpu_small/cpp/0002-core-recurrent_in/0002-core-recurrent_in_1776485016016_out.h5 |
| cpp | 0003-core-twopop_in | 0 | 0.040 | 0.020 | 0.000 |  |  | /home/vullar/Studio/Playground/SpikeNet/reports/equivalence_gpu_small/cpp/0003-core-twopop_in/0003-core-twopop_in_1776485022225_out.h5 |
| python | 0001-core-nosyn_in | 0 | 9.910 | 4.750 | 1.370 | 603.266 | 0.000 | /home/vullar/Studio/Playground/SpikeNet/reports/equivalence_gpu_small/python/0001-core-nosyn_in/0001-core-nosyn_in_1776485014986_out.h5 |
| python | 0002-core-recurrent_in | 0 | 6.150 | 5.980 | 1.120 | 798.494 | 0.000 | /home/vullar/Studio/Playground/SpikeNet/reports/equivalence_gpu_small/python/0002-core-recurrent_in/0002-core-recurrent_in_1776485021043_out.h5 |
| python | 0003-core-twopop_in | 0 | 12.360 | 8.940 | 1.500 | 1124.608 | 0.000 | /home/vullar/Studio/Playground/SpikeNet/reports/equivalence_gpu_small/python/0003-core-twopop_in/0003-core-twopop_in_1776485033207_out.h5 |

## Detailed Checks

| Case | Path | Status | Detail | Max Abs | Max Rel |
|---|---|---|---|---:|---:|
| 0001-core-nosyn_in | CLI::Number of input files: | PASS | cpp=True, py=True |  |  |
| 0001-core-nosyn_in | CLI::Processing input file No.1 out of 1... | PASS | cpp=True, py=True |  |  |
| 0001-core-nosyn_in | CLI::Data file name is: | PASS | cpp=True, py=True |  |  |
| 0001-core-nosyn_in | CLI::The planet earth is blue and there's nothing I can do. | PASS | cpp=True, py=True |  |  |
| 0001-core-nosyn_in | CLI::exit_code | PASS | cpp=0, py=0 |  |  |
| 0001-core-nosyn_in | /config_filename/config_filename | PASS | present in both outputs |  |  |
| 0001-core-nosyn_in | /run_away_killed/step | PASS | present in both outputs |  |  |
| 0001-core-nosyn_in | /pop_result_0/spike_hist_tot | PASS | integer exact match |  |  |
| 0001-core-nosyn_in | /pop_result_0/num_spikes_pop | PASS | integer exact match |  |  |
| 0001-core-nosyn_in | /pop_result_0/num_ref_pop | PASS | integer exact match |  |  |
| 0001-core-nosyn_in | /pop_result_0/stats_V_mean | PASS | allclose | 2.842e-14 | 4.433e-16 |
| 0001-core-nosyn_in | /pop_result_0/stats_V_std | PASS | allclose | 9.825e-15 | 3.575e-14 |
| 0001-core-nosyn_in | /pop_result_0/stats_I_input_mean | PASS | allclose | 0.000e+00 | 0.000e+00 |
| 0001-core-nosyn_in | /pop_result_0/stats_I_input_std | PASS | allclose | 0.000e+00 | 0.000e+00 |
| 0002-core-recurrent_in | CLI::Number of input files: | PASS | cpp=True, py=True |  |  |
| 0002-core-recurrent_in | CLI::Processing input file No.1 out of 1... | PASS | cpp=True, py=True |  |  |
| 0002-core-recurrent_in | CLI::Data file name is: | PASS | cpp=True, py=True |  |  |
| 0002-core-recurrent_in | CLI::The planet earth is blue and there's nothing I can do. | PASS | cpp=True, py=True |  |  |
| 0002-core-recurrent_in | CLI::exit_code | PASS | cpp=0, py=0 |  |  |
| 0002-core-recurrent_in | /config_filename/config_filename | PASS | present in both outputs |  |  |
| 0002-core-recurrent_in | /run_away_killed/step | PASS | present in both outputs |  |  |
| 0002-core-recurrent_in | /pop_result_0/spike_hist_tot | PASS | integer exact match |  |  |
| 0002-core-recurrent_in | /pop_result_0/num_spikes_pop | PASS | integer exact match |  |  |
| 0002-core-recurrent_in | /pop_result_0/num_ref_pop | PASS | integer exact match |  |  |
| 0002-core-recurrent_in | /pop_result_0/stats_V_mean | PASS | allclose | 1.421e-14 | 2.316e-16 |
| 0002-core-recurrent_in | /pop_result_0/stats_V_std | PASS | allclose | 5.329e-15 | 3.112e-15 |
| 0002-core-recurrent_in | /pop_result_0/stats_I_input_mean | PASS | allclose | 2.776e-17 | 4.354e-16 |
| 0002-core-recurrent_in | /pop_result_0/stats_I_input_std | PASS | allclose | 5.551e-17 | 2.796e-16 |
| 0002-core-recurrent_in | /syn_result_0/stats_I_mean | PASS | allclose | 2.776e-17 | 4.354e-16 |
| 0003-core-twopop_in | CLI::Number of input files: | PASS | cpp=True, py=True |  |  |
| 0003-core-twopop_in | CLI::Processing input file No.1 out of 1... | PASS | cpp=True, py=True |  |  |
| 0003-core-twopop_in | CLI::Data file name is: | PASS | cpp=True, py=True |  |  |
| 0003-core-twopop_in | CLI::The planet earth is blue and there's nothing I can do. | PASS | cpp=True, py=True |  |  |
| 0003-core-twopop_in | CLI::exit_code | PASS | cpp=0, py=0 |  |  |
| 0003-core-twopop_in | /config_filename/config_filename | PASS | present in both outputs |  |  |
| 0003-core-twopop_in | /run_away_killed/step | PASS | present in both outputs |  |  |
| 0003-core-twopop_in | /pop_result_0/spike_hist_tot | PASS | integer exact match |  |  |
| 0003-core-twopop_in | /pop_result_0/num_spikes_pop | PASS | integer exact match |  |  |
| 0003-core-twopop_in | /pop_result_0/num_ref_pop | PASS | integer exact match |  |  |
| 0003-core-twopop_in | /pop_result_0/stats_V_mean | PASS | allclose | 1.421e-14 | 2.308e-16 |
| 0003-core-twopop_in | /pop_result_0/stats_V_std | PASS | allclose | 8.660e-15 | 1.111e-14 |
| 0003-core-twopop_in | /pop_result_0/stats_I_input_mean | PASS | allclose | 0.000e+00 | 0.000e+00 |
| 0003-core-twopop_in | /pop_result_0/stats_I_input_std | PASS | allclose | 0.000e+00 | 0.000e+00 |
| 0003-core-twopop_in | /pop_result_1/spike_hist_tot | PASS | integer exact match |  |  |
| 0003-core-twopop_in | /pop_result_1/num_spikes_pop | PASS | integer exact match |  |  |
| 0003-core-twopop_in | /pop_result_1/num_ref_pop | PASS | integer exact match |  |  |
| 0003-core-twopop_in | /pop_result_1/stats_V_mean | PASS | allclose | 1.421e-14 | 2.413e-16 |
| 0003-core-twopop_in | /pop_result_1/stats_V_std | PASS | allclose | 4.441e-15 | 3.535e-14 |
| 0003-core-twopop_in | /pop_result_1/stats_I_input_mean | PASS | allclose | 1.110e-16 | 4.359e-16 |
| 0003-core-twopop_in | /pop_result_1/stats_I_input_std | PASS | allclose | 1.110e-16 | 3.685e-16 |
| 0003-core-twopop_in | /syn_result_0/stats_I_mean | PASS | allclose | 1.110e-16 | 4.359e-16 |
| 0003-core-twopop_in | /syn_result_1/stats_I_mean | PASS | allclose | 0.000e+00 | 0.000e+00 |