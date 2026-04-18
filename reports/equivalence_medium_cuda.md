# SpikeNet C++ vs Python Equivalence Report

- Generated at: 2026-04-18T12:09:25
- Total checks: 52
- Passed: 52
- Failed: 0

## Performance Summary

| Engine | Real Time Total (s) | User Time Total (s) | Torch CPU Time Total (ms) | Torch GPU Time Total (ms) |
|---|---:|---:|---:|---:|
| C++ | 1.150 | 0.970 | N/A | N/A |
| Torch | 31.770 | 20.380 | 16154.668 | 16145.223 |

## Executions

| Engine | Case | Return Code | Real (s) | User (s) | Sys (s) | Torch CPU (ms) | Torch GPU (ms) | Output File |
|---|---|---:|---:|---:|---:|---:|---:|---|
| cpp | 0001-core-nosyn-medium_in | 0 | 0.070 | 0.050 | 0.010 |  |  | /home/vullar/Studio/Playground/SpikeNet/reports/equivalence_medium_cuda/cpp/0001-core-nosyn-medium_in/0001-core-nosyn-medium_in_1776485332142_out.h5 |
| cpp | 0002-core-recurrent-medium_in | 0 | 0.830 | 0.730 | 0.020 |  |  | /home/vullar/Studio/Playground/SpikeNet/reports/equivalence_medium_cuda/cpp/0002-core-recurrent-medium_in/0002-core-recurrent-medium_in_1776485341658_out.h5 |
| cpp | 0003-core-twopop-medium_in | 0 | 0.250 | 0.190 | 0.030 |  |  | /home/vullar/Studio/Playground/SpikeNet/reports/equivalence_medium_cuda/cpp/0003-core-twopop-medium_in/0003-core-twopop-medium_in_1776485352896_out.h5 |
| python | 0001-core-nosyn-medium_in | 0 | 9.410 | 4.250 | 1.530 | 2291.379 | 2285.510 | /home/vullar/Studio/Playground/SpikeNet/reports/equivalence_medium_cuda/python/0001-core-nosyn-medium_in/0001-core-nosyn-medium_in_1776485340780_out.h5 |
| python | 0002-core-recurrent-medium_in | 0 | 10.360 | 8.390 | 2.650 | 7412.206 | 7409.824 | /home/vullar/Studio/Playground/SpikeNet/reports/equivalence_medium_cuda/python/0002-core-recurrent-medium_in/0002-core-recurrent-medium_in_1776485351885_out.h5 |
| python | 0003-core-twopop-medium_in | 0 | 12.000 | 7.740 | 2.390 | 6451.083 | 6449.890 | /home/vullar/Studio/Playground/SpikeNet/reports/equivalence_medium_cuda/python/0003-core-twopop-medium_in/0003-core-twopop-medium_in_1776485364065_out.h5 |

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
| 0001-core-nosyn-medium_in | /pop_result_0/stats_V_mean | PASS | allclose | 2.416e-13 | 3.452e-15 |
| 0001-core-nosyn-medium_in | /pop_result_0/stats_V_std | PASS | allclose | 3.035e-14 | 4.014e-11 |
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
| 0002-core-recurrent-medium_in | /pop_result_0/stats_V_mean | PASS | allclose | 1.066e-13 | 1.898e-15 |
| 0002-core-recurrent-medium_in | /pop_result_0/stats_V_std | PASS | allclose | 1.599e-14 | 3.529e-14 |
| 0002-core-recurrent-medium_in | /pop_result_0/stats_I_input_mean | PASS | allclose | 2.132e-13 | 2.595e-15 |
| 0002-core-recurrent-medium_in | /pop_result_0/stats_I_input_std | PASS | allclose | 1.599e-14 | 1.688e-15 |
| 0002-core-recurrent-medium_in | /syn_result_0/stats_I_mean | PASS | allclose | 2.132e-13 | 2.595e-15 |
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
| 0003-core-twopop-medium_in | /pop_result_0/stats_V_std | PASS | allclose | 1.332e-14 | 8.631e-12 |
| 0003-core-twopop-medium_in | /pop_result_0/stats_I_input_mean | PASS | allclose | 1.998e-15 | 3.491e-15 |
| 0003-core-twopop-medium_in | /pop_result_0/stats_I_input_std | PASS | allclose | 1.665e-16 | 1.269e-15 |
| 0003-core-twopop-medium_in | /pop_result_1/spike_hist_tot | PASS | integer exact match |  |  |
| 0003-core-twopop-medium_in | /pop_result_1/num_spikes_pop | PASS | integer exact match |  |  |
| 0003-core-twopop-medium_in | /pop_result_1/num_ref_pop | PASS | integer exact match |  |  |
| 0003-core-twopop-medium_in | /pop_result_1/stats_V_mean | PASS | allclose | 2.274e-13 | 3.256e-15 |
| 0003-core-twopop-medium_in | /pop_result_1/stats_V_std | PASS | allclose | 6.321e-15 | 4.913e-13 |
| 0003-core-twopop-medium_in | /pop_result_1/stats_I_input_mean | PASS | allclose | 1.776e-15 | 2.848e-15 |
| 0003-core-twopop-medium_in | /pop_result_1/stats_I_input_std | PASS | allclose | 9.992e-16 | 1.421e-15 |
| 0003-core-twopop-medium_in | /syn_result_0/stats_I_mean | PASS | allclose | 1.776e-15 | 2.848e-15 |
| 0003-core-twopop-medium_in | /syn_result_1/stats_I_mean | PASS | allclose | 1.998e-15 | 3.491e-15 |