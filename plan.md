# SpikeNet C++ -> Python/PyTorch Migration Plan

## Scope
- Migrate the C++ simulator core in `cpp_sources/` to Python.
- Keep existing Matlab preprocessing/postprocessing and HDF5 contracts stable.
- Prioritize CPU correctness first, then PyTorch tensor acceleration.

## Constraints
- Current test environment does not support Matlab runtime.
- Validation should use synthetic HDF5 input data and script-level checks.
- Existing shell/PBS workflow should remain adaptable with minimal changes.

## Milestones

### Phase 0: Contract Freeze and Baseline
1. Freeze I/O and CLI contracts:
   - Input: `/config/Net`, `/config/pops`, `/config/syns`.
   - Output: `/config_filename`, `/run_away_killed`, `/pop_result_*`, `/syn_result_*`.
   - CLI: multiple input files accepted.
2. Prepare baseline scenarios:
   - Small network with recurrent synapses.
   - Optional features enabled progressively (sampling, plasticity, restart).
3. Define validation criteria:
   - Structural compatibility: HDF5 paths/dtypes/shapes.
   - Behavioral compatibility: spike count trend and basic population stats.

### Phase 1: Python Scaffold (in progress)
1. Add package skeleton and CLI.
2. Implement minimal config loader for required HDF5 fields.
3. Implement minimal simulation loop:
   - population spike update,
   - synaptic current propagation with delay,
   - membrane voltage update.
4. Write compatibility output writer for key HDF5 groups.
5. Add smoke test runnable without Matlab.

### Phase 2: Feature Parity
1. Add restart import/export path.
2. Add optional external inputs and more INIT blocks.
3. Add sampling and stats parity.
4. Add plasticity modules in staged order:
   - STD,
   - SP,
   - Inh-STDP,
   - JH learning.

### Phase 3: Performance Optimization
1. Convert hot loops to vectorized tensor operations.
2. Rework synapse projection using efficient index-based accumulation.
3. Evaluate sparse layouts where beneficial.
4. Benchmark:
   - steps/s,
   - peak memory,
   - scaling with neuron/synapse counts.

### Phase 4: Workflow Integration
1. Provide a compatibility launcher strategy for shell/PBS scripts.
2. Keep output naming and location semantics compatible.
3. Document migration status and unsupported features clearly.

## Validation Checklist
- [ ] CLI works for one and multiple `.h5` input files.
- [ ] Output `.h5` contains required top-level groups.
- [ ] `pop_result_*` and `syn_result_*` datasets are readable by current Matlab readers.
- [ ] Smoke test passes in `utils` conda environment.
- [ ] Core step loop stable for at least 1e4 steps on synthetic input.

## Current Status
- [x] Repository contract and architecture mapped.
- [x] Root migration plan created.
- [x] Python scaffold created.
- [x] Minimal config parser added.
- [x] Minimal simulation core added.
- [x] Compatibility output writer added.
- [x] Smoke test script added.
- [ ] Restart support.
- [ ] Advanced feature parity.
- [ ] Performance tuning and benchmarks.
