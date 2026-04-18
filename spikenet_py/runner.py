from __future__ import annotations

import json
import os
import time
from pathlib import Path

import h5py
import numpy as np
import torch

from .config import SimulationConfig, load_config_h5
from .core import Population, Synapse


def _generate_output_stem(input_path: str) -> str:
    in_path = Path(input_path)
    stem = in_path.with_suffix("")
    timestamp_ms = int(time.time() * 1000)
    return f"{stem}_{timestamp_ms}"


class SimulationRunner:
    def __init__(self, config: SimulationConfig, device: str = "cpu") -> None:
        self.config = config
        self.device = torch.device(device)

        restart_state = config.restart_state

        self.populations = [
            Population(
                cfg=pop_cfg,
                dt=config.dt,
                step_tot=config.step_tot,
                device=self.device,
                restart_state=restart_state.populations.get(pop_cfg.index) if restart_state is not None else None,
            )
            for pop_cfg in config.populations
        ]
        self.synapses = [
            Synapse(
                cfg=syn_cfg,
                dt=config.dt,
                n_pre=config.pop_sizes[syn_cfg.pop_pre],
                n_post=config.pop_sizes[syn_cfg.pop_post],
                device=self.device,
                restart_state=restart_state.synapses.get(syn_cfg.index) if restart_state is not None else None,
            )
            for syn_cfg in config.synapses
            if 0 <= syn_cfg.pop_pre < len(config.pop_sizes) and syn_cfg.pop_post < len(config.pop_sizes)
        ]

    def simulate(self) -> None:
        populations = self.populations
        synapses = self.synapses
        step_tot = self.config.step_tot

        with torch.inference_mode():
            for step_current in range(step_tot):
                for population in populations:
                    population.update_spikes(step_current)

                for synapse in synapses:
                    synapse.update(step_current, populations)

                for population in populations:
                    population.update_voltage(step_current)

    def write_output(self, input_path: str, out_stem: str) -> str:
        out_file = f"{out_stem}_out.h5"
        with h5py.File(out_file, "w") as h5:
            config_group = h5.create_group("/config_filename")
            config_group.create_dataset(
                "config_filename",
                data=np.asarray([input_path], dtype=h5py.string_dtype("utf-8")),
            )

            killed_group = h5.create_group("/run_away_killed")
            killed_group.create_dataset("step", data=np.asarray([-1], dtype=np.int32))

            for idx, population in enumerate(self.populations):
                pop_group = h5.create_group(f"/pop_result_{idx}")
                population.write_results(pop_group)

            for idx, synapse in enumerate(self.synapses):
                syn_group = h5.create_group(f"/syn_result_{idx}")
                synapse.write_results(syn_group)

        return out_file

    def write_restart(self, input_path: str, out_stem: str) -> str:
        restart_file = f"{out_stem}_restart.h5"
        with h5py.File(restart_file, "w") as h5:
            simu_group = h5.create_group("/SimuInterface")
            simu_group.create_dataset(
                "in_filename",
                data=np.asarray([input_path], dtype=h5py.string_dtype("utf-8")),
            )
            simu_group.create_dataset(
                "out_filename",
                data=np.asarray([out_stem], dtype=h5py.string_dtype("utf-8")),
            )

            restart_group = h5.create_group("/Restart")
            restart_group.create_dataset("child_no_of_parent", data=np.asarray([1], dtype=np.int32))
            restart_group.create_dataset("no_children", data=np.asarray([0], dtype=np.int32))

            net_group = h5.create_group("/Net")
            net_group.create_dataset("N_array", data=np.asarray(self.config.pop_sizes, dtype=np.int32))
            net_group.create_dataset("step_tot", data=np.asarray([self.config.step_tot], dtype=np.int32))
            net_group.create_dataset("dt", data=np.asarray([self.config.dt], dtype=np.float64))
            net_group.create_dataset("Num_pop", data=np.asarray([len(self.populations)], dtype=np.int32))

            pops_group = h5.create_group("/pops")
            for population in self.populations:
                population.write_restart(pops_group, step_tot=self.config.step_tot)

            syns_group = h5.create_group("/syns")
            syns_group.create_dataset("n_syns", data=np.asarray([len(self.synapses)], dtype=np.int32))
            for synapse in self.synapses:
                synapse.write_restart(syns_group, step_tot=self.config.step_tot)

        return restart_file


def run_single_file(input_path: str, device: str = "cpu") -> tuple[str, str]:
    config = load_config_h5(input_path)
    runner = SimulationRunner(config=config, device=device)

    profile_json_path = os.getenv("SPIKENET_TORCH_PROFILE_JSON", "").strip()
    if profile_json_path:
        enable_cuda_timing = runner.device.type == "cuda" and torch.cuda.is_available()
        start_event: torch.cuda.Event | None = None
        end_event: torch.cuda.Event | None = None
        if enable_cuda_timing:
            start_event = torch.cuda.Event(enable_timing=True)
            end_event = torch.cuda.Event(enable_timing=True)
            start_event.record()

        cpu_start = time.process_time()
        runner.simulate()
        cpu_end = time.process_time()

        total_gpu_ms = 0.0
        if enable_cuda_timing and start_event is not None and end_event is not None:
            end_event.record()
            torch.cuda.synchronize()
            total_gpu_ms = float(start_event.elapsed_time(end_event))

        payload = {
            "torch_cpu_time_ms": (cpu_end - cpu_start) * 1000.0,
            "torch_gpu_time_ms": total_gpu_ms,
            "cuda_timing_enabled": enable_cuda_timing,
            "gpu_time_source": "cuda_event" if enable_cuda_timing else "none",
            "device": runner.device.type,
        }
        profile_path = Path(profile_json_path)
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        profile_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    else:
        runner.simulate()

    out_stem = _generate_output_stem(input_path)
    out_file = runner.write_output(input_path=input_path, out_stem=out_stem)
    runner.write_restart(input_path=input_path, out_stem=out_stem)
    return out_stem, out_file
