# SpikeNet C++ vs Python Equivalence Report

- Generated at: 2026-04-19T18:27:31
- Total checks: 52
- Passed: 52
- Failed: 0

## Performance Summary

| Engine | Real Time Total (s) | User Time Total (s) | Torch CPU Time Total (ms) | Torch GPU Time Total (ms) |
|---|---:|---:|---:|---:|
| C++ | 0.090 | 0.030 | N/A | N/A |
| Torch | 10.370 | 10.940 | 1614.478 | 0.000 |

## Executions

| Engine | Case | Return Code | Real (s) | User (s) | Sys (s) | Torch CPU (ms) | Torch GPU (ms) | Output File |
|---|---|---:|---:|---:|---:|---:|---:|---|
| cpp | 0001-core-nosyn_in | 0 | 0.020 | 0.000 | 0.000 |  |  | /home/vullar/Studio/Playground/SpikeNet/reports/equivalence_after_stats/cpp/0001-core-nosyn_in/0001-core-nosyn_in_1776594441090_out.h5 |
| cpp | 0002-core-recurrent_in | 0 | 0.030 | 0.010 | 0.010 |  |  | /home/vullar/Studio/Playground/SpikeNet/reports/equivalence_after_stats/cpp/0002-core-recurrent_in/0002-core-recurrent_in_1776594444612_out.h5 |
| cpp | 0003-core-twopop_in | 0 | 0.040 | 0.020 | 0.000 |  |  | /home/vullar/Studio/Playground/SpikeNet/reports/equivalence_after_stats/cpp/0003-core-twopop_in/0003-core-twopop_in_1776594448086_out.h5 |
| python | 0001-core-nosyn_in | 0 | 3.470 | 2.950 | 0.500 | 33.529 | 0.000 | /home/vullar/Studio/Playground/SpikeNet/reports/equivalence_after_stats/python/0001-core-nosyn_in/0001-core-nosyn_in_1776594443808_out.h5 |
| python | 0002-core-recurrent_in | 0 | 3.410 | 3.910 | 0.760 | 495.333 | 0.000 | /home/vullar/Studio/Playground/SpikeNet/reports/equivalence_after_stats/python/0002-core-recurrent_in/0002-core-recurrent_in_1776594447401_out.h5 |
| python | 0003-core-twopop_in | 0 | 3.490 | 4.080 | 0.730 | 1085.616 | 0.000 | /home/vullar/Studio/Playground/SpikeNet/reports/equivalence_after_stats/python/0003-core-twopop_in/0003-core-twopop_in_1776594450955_out.h5 |

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
| 0001-core-nosyn_in | /pop_result_0/stats_V_mean | PASS | allclose | 1.421e-14 | 2.357e-16 |
| 0001-core-nosyn_in | /pop_result_0/stats_V_std | PASS | allclose | 1.033e-14 | 3.199e-14 |
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
| 0002-core-recurrent_in | /pop_result_0/stats_V_mean | PASS | allclose | 2.132e-14 | 3.361e-16 |
| 0002-core-recurrent_in | /pop_result_0/stats_V_std | PASS | allclose | 5.329e-15 | 3.336e-15 |
| 0002-core-recurrent_in | /pop_result_0/stats_I_input_mean | PASS | allclose | 2.776e-17 | 2.621e-16 |
| 0002-core-recurrent_in | /pop_result_0/stats_I_input_std | PASS | allclose | 1.110e-16 | 3.964e-16 |
| 0002-core-recurrent_in | /syn_result_0/stats_I_mean | PASS | allclose | 2.776e-17 | 2.621e-16 |
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
| 0003-core-twopop_in | /pop_result_0/stats_V_mean | PASS | allclose | 2.842e-14 | 4.335e-16 |
| 0003-core-twopop_in | /pop_result_0/stats_V_std | PASS | allclose | 6.550e-15 | 8.876e-15 |
| 0003-core-twopop_in | /pop_result_0/stats_I_input_mean | PASS | allclose | 0.000e+00 | 0.000e+00 |
| 0003-core-twopop_in | /pop_result_0/stats_I_input_std | PASS | allclose | 0.000e+00 | 0.000e+00 |
| 0003-core-twopop_in | /pop_result_1/spike_hist_tot | PASS | integer exact match |  |  |
| 0003-core-twopop_in | /pop_result_1/num_spikes_pop | PASS | integer exact match |  |  |
| 0003-core-twopop_in | /pop_result_1/num_ref_pop | PASS | integer exact match |  |  |
| 0003-core-twopop_in | /pop_result_1/stats_V_mean | PASS | allclose | 1.421e-14 | 2.410e-16 |
| 0003-core-twopop_in | /pop_result_1/stats_V_std | PASS | allclose | 5.329e-15 | 5.965e-14 |
| 0003-core-twopop_in | /pop_result_1/stats_I_input_mean | PASS | allclose | 1.110e-16 | 3.073e-16 |
| 0003-core-twopop_in | /pop_result_1/stats_I_input_std | PASS | allclose | 1.110e-16 | 3.685e-16 |
| 0003-core-twopop_in | /syn_result_0/stats_I_mean | PASS | allclose | 1.110e-16 | 3.073e-16 |
| 0003-core-twopop_in | /syn_result_1/stats_I_mean | PASS | allclose | 0.000e+00 | 0.000e+00 |