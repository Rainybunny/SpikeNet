from __future__ import annotations

import math
from dataclasses import dataclass

import h5py
import numpy as np
import torch

from .config import PopulationConfig, SynapseConfig


@dataclass
class NeuronParams:
    cm: float = 0.25
    tau_ref: float = 2.0
    v_rt: float = -60.0
    v_lk: float = -70.0
    v_th: float = -50.0
    g_lk: float = 0.0167


class Population:
    def __init__(self, cfg: PopulationConfig, dt: float, step_tot: int, device: torch.device) -> None:
        self.index = cfg.index
        self.n = cfg.size
        self.dt = dt
        self.step_tot = step_tot
        self.device = device

        params = NeuronParams()
        params.cm = cfg.params.get("Cm", params.cm)
        params.tau_ref = cfg.params.get("tau_ref", params.tau_ref)
        params.v_rt = cfg.params.get("V_rt", params.v_rt)
        params.v_lk = cfg.params.get("V_lk", params.v_lk)
        params.v_th = cfg.params.get("V_th", params.v_th)
        params.g_lk = cfg.params.get("g_lk", params.g_lk)
        self.params = params

        self.ref_steps = int(round(self.params.tau_ref / self.dt))
        self.rng = torch.Generator(device="cpu")
        if cfg.seed is not None:
            self.rng.manual_seed(cfg.seed)

        self.v = torch.full((self.n,), self.params.v_lk, dtype=torch.float64, device=self.device)
        self.ref_step_left = torch.zeros((self.n,), dtype=torch.int64, device=self.device)

        if cfg.init_v_external is not None:
            init_v = np.asarray(cfg.init_v_external, dtype=np.float64).reshape(-1)
            if init_v.size != self.n:
                raise ValueError(
                    f"Population {self.index}: SETINITV/external_init_V length {init_v.size} != N {self.n}"
                )
            self.v = torch.tensor(init_v, dtype=torch.float64, device=self.device)

        if cfg.init_p_fire is not None:
            self._set_initial_condition(cfg.init_r_v0, cfg.init_p_fire)

        self.i_leak = torch.zeros((self.n,), dtype=torch.float64, device=self.device)
        self.i_input = torch.zeros((self.n,), dtype=torch.float64, device=self.device)
        self.i_ampa = torch.zeros((self.n,), dtype=torch.float64, device=self.device)
        self.i_gaba = torch.zeros((self.n,), dtype=torch.float64, device=self.device)
        self.i_nmda = torch.zeros((self.n,), dtype=torch.float64, device=self.device)
        self.i_ext = torch.zeros((self.n,), dtype=torch.float64, device=self.device)

        self.spikes_current = torch.empty((0,), dtype=torch.int64, device=self.device)
        self.spike_hist_tot: list[int] = []
        self.num_spikes_pop: list[int] = []
        self.num_ref_pop: list[int] = []

        self.stats_v_mean: list[float] = []
        self.stats_v_std: list[float] = []
        self.stats_i_mean: list[float] = []
        self.stats_i_std: list[float] = []

    def _set_initial_condition(self, r_v0: float | None, p_fire: float) -> None:
        local_r_v0 = 1.0 if r_v0 is None else float(r_v0)
        u = torch.rand((self.n,), generator=self.rng, dtype=torch.float64)
        base = self.params.v_rt + (self.params.v_th - self.params.v_rt) * local_r_v0 * u
        fire_mask = torch.rand((self.n,), generator=self.rng, dtype=torch.float64) < p_fire
        forced = torch.full_like(base, self.params.v_th + 1.0)
        self.v = torch.where(fire_mask.to(self.device), forced.to(self.device), base.to(self.device))

    def _reset_synaptic_currents(self) -> None:
        self.i_ampa.zero_()
        self.i_gaba.zero_()
        self.i_nmda.zero_()
        self.i_ext.zero_()

    def update_spikes(self, step_current: int) -> None:
        _ = step_current
        self._reset_synaptic_currents()

        can_spike = self.ref_step_left == 0
        spike_mask = torch.logical_and(can_spike, self.v >= self.params.v_th)
        self.spikes_current = torch.nonzero(spike_mask, as_tuple=False).reshape(-1)

        if self.spikes_current.numel() > 0:
            self.v[self.spikes_current] = self.params.v_rt
            self.ref_step_left[self.spikes_current] = self.ref_steps

        spike_count = int(self.spikes_current.numel())
        self.num_spikes_pop.append(spike_count)
        if spike_count > 0:
            self.spike_hist_tot.extend(self.spikes_current.detach().cpu().tolist())

        refractory = self.ref_step_left > 0
        # Match C++ semantics: count refractory neurons before decrementing the counters.
        self.num_ref_pop.append(int(refractory.sum().item()))
        self.ref_step_left[refractory] -= 1

    def receive_current(self, current: torch.Tensor, pop_ind_pre: int, syn_type: int) -> None:
        if pop_ind_pre < 0:
            self.i_ext += current
        elif syn_type == 0:
            self.i_ampa += current
        elif syn_type == 1:
            self.i_gaba += current
        elif syn_type == 2:
            self.i_nmda += current

    def update_voltage(self, step_current: int) -> None:
        _ = step_current
        self.i_input = self.i_ampa + self.i_gaba + self.i_nmda + self.i_ext
        self.i_leak = -self.params.g_lk * (self.v - self.params.v_lk)

        vdot = (self.i_leak + self.i_input) / self.params.cm
        non_ref = self.ref_step_left == 0
        self.v[non_ref] += vdot[non_ref] * self.dt

        self.stats_v_mean.append(float(self.v.mean().item()))
        # C++ uses sample variance (N-1) via Welford.
        v_std = self.v.std(unbiased=True).item() if self.n > 1 else 0.0
        self.stats_v_std.append(float(v_std))
        self.stats_i_mean.append(float(self.i_input.mean().item()))
        i_std = self.i_input.std(unbiased=True).item() if self.n > 1 else 0.0
        self.stats_i_std.append(float(i_std))

    def pop_para_string(self) -> str:
        return (
            f"Cm,{self.params.cm},"
            f"tau_ref,{self.params.tau_ref},"
            f"V_rt,{self.params.v_rt},"
            f"V_lk,{self.params.v_lk},"
            f"V_th,{self.params.v_th},"
            f"g_lk,{self.params.g_lk},"
        )

    def write_results(self, group: h5py.Group) -> None:
        group.create_dataset("spike_hist_tot", data=np.asarray(self.spike_hist_tot, dtype=np.int32))
        group.create_dataset("num_spikes_pop", data=np.asarray(self.num_spikes_pop, dtype=np.int32))
        group.create_dataset("num_ref_pop", data=np.asarray(self.num_ref_pop, dtype=np.int32))
        group.create_dataset("pop_para", data=np.asarray([self.pop_para_string()], dtype=h5py.string_dtype("utf-8")))

        group.create_dataset("stats_V_mean", data=np.asarray(self.stats_v_mean, dtype=np.float64))
        group.create_dataset("stats_V_std", data=np.asarray(self.stats_v_std, dtype=np.float64))
        group.create_dataset("stats_I_input_mean", data=np.asarray(self.stats_i_mean, dtype=np.float64))
        group.create_dataset("stats_I_input_std", data=np.asarray(self.stats_i_std, dtype=np.float64))

        # These placeholders preserve the expected output contract for downstream readers.
        group.create_dataset("stats_I_AMPA_time_avg", data=np.zeros((self.n,), dtype=np.float64))
        group.create_dataset("stats_I_NMDA_time_avg", data=np.zeros((self.n,), dtype=np.float64))
        group.create_dataset("stats_I_GABA_time_avg", data=np.zeros((self.n,), dtype=np.float64))
        group.create_dataset("stats_I_ext_time_avg", data=np.zeros((self.n,), dtype=np.float64))
        group.create_dataset("stats_I_tot_time_mean", data=np.zeros((self.n,), dtype=np.float64))
        group.create_dataset("stats_I_tot_time_var", data=np.zeros((self.n,), dtype=np.float64))
        group.create_dataset("stats_V_time_mean", data=np.zeros((self.n,), dtype=np.float64))
        group.create_dataset("stats_V_time_cov", data=np.zeros((self.n, self.n), dtype=np.float64))
        group.create_dataset("stats_V_time_var", data=np.zeros((self.n,), dtype=np.float64))
        group.create_dataset("stats_IE_ratio", data=np.zeros((self.n,), dtype=np.float64))
        group.create_dataset("LFP_data", data=np.zeros((0, 0), dtype=np.float64))


class Synapse:
    def __init__(self, cfg: SynapseConfig, dt: float, n_pre: int, n_post: int, device: torch.device) -> None:
        self.index = cfg.index
        self.syn_type = cfg.syn_type
        self.pop_pre = cfg.pop_pre
        self.pop_post = cfg.pop_post
        self.dt = dt
        self.device = device

        self.n_pre = n_pre
        self.pre_idx = torch.tensor(cfg.i, dtype=torch.int64, device=self.device)
        self.post_idx = torch.tensor(cfg.j, dtype=torch.int64, device=self.device)
        self.weight = torch.tensor(cfg.k, dtype=torch.float64, device=self.device)
        self.delay_steps = torch.tensor(np.round(cfg.d / dt).astype(np.int64), dtype=torch.int64, device=self.device)

        self.v_ex = 0.0
        self.v_in = -80.0

        self.steps_trans = max(1, int(round(self._tau_rise() / self.dt)))
        self.k_trans = 1.0 / float(self.steps_trans)
        self.exp_step_decay = math.exp(-self.dt / self._tau_decay())

        max_delay = int(self.delay_steps.max().item()) if self.delay_steps.numel() else 0
        self.buffer_steps = max_delay + self.steps_trans + 1
        self.buffer = torch.zeros((self.buffer_steps, n_post), dtype=torch.float64, device=self.device)
        self.gs_sum = torch.zeros((n_post,), dtype=torch.float64, device=self.device)
        # Model-0 state variables in C++ implementation.
        self.s_pre = torch.zeros((self.n_pre,), dtype=torch.float64, device=self.device)
        self.trans_left = torch.zeros((self.n_pre,), dtype=torch.int64, device=self.device)

        self.edge_by_pre: list[torch.Tensor] = []
        for pre in range(self.n_pre):
            edge_ids = torch.nonzero(self.pre_idx == pre, as_tuple=False).reshape(-1)
            self.edge_by_pre.append(edge_ids)

        self.stats_i_mean: list[float] = []
        self.stats_i_std: list[float] = []

    def _tau_rise(self) -> float:
        if self.syn_type == 0:
            return 1.0
        if self.syn_type == 1:
            return 1.0
        return 5.0

    def _tau_decay(self) -> float:
        if self.syn_type == 0:
            return 5.0
        if self.syn_type == 1:
            return 3.0
        return 80.0

    def _calc_current(self, v_post: torch.Tensor) -> torch.Tensor:
        if self.syn_type == 0:
            return -self.gs_sum * (v_post - self.v_ex)
        if self.syn_type == 1:
            return -self.gs_sum * (v_post - self.v_in)
        b_v = 1.0 / (1.0 + 0.33 * torch.exp(-0.06 * v_post))
        return -self.gs_sum * b_v * (v_post - self.v_ex)

    def update(self, step_current: int, populations: list[Population]) -> None:
        if self.pop_pre < 0:
            # External-noise synapses are deferred to later phases.
            return

        pre_spikes = populations[self.pop_pre].spikes_current
        if pre_spikes.numel() > 0:
            for pre in pre_spikes.detach().cpu().tolist():
                if pre < self.n_pre:
                    self.trans_left[pre] += self.steps_trans

        # Match C++ model-0 transmitter dynamics.
        for i_pre in range(self.n_pre):
            if int(self.trans_left[i_pre].item()) <= 0:
                continue

            edge_ids = self.edge_by_pre[i_pre]
            if edge_ids.numel() > 0:
                posts = self.post_idx[edge_ids]
                delays = self.delay_steps[edge_ids]
                values = self.weight[edge_ids] * (self.k_trans * (1.0 - self.s_pre[i_pre]))
                unique_delays = torch.unique(delays)
                for delay in unique_delays.detach().cpu().tolist():
                    mask = delays == delay
                    slot = int((step_current + int(delay)) % self.buffer_steps)
                    self.buffer[slot].index_add_(0, posts[mask], values[mask])

            self.trans_left[i_pre] -= 1
            self.s_pre[i_pre] += self.k_trans * (1.0 - self.s_pre[i_pre])

        self.s_pre *= self.exp_step_decay

        slot_now = int(step_current % self.buffer_steps)
        self.gs_sum += self.buffer[slot_now]
        self.gs_sum *= self.exp_step_decay
        self.buffer[slot_now].zero_()

        v_post = populations[self.pop_post].v
        current = self._calc_current(v_post)
        populations[self.pop_post].receive_current(current, self.pop_pre, self.syn_type)

        self.stats_i_mean.append(float(current.mean().item()))
        self.stats_i_std.append(float(current.std(unbiased=False).item()))

    def write_results(self, group: h5py.Group) -> None:
        syn_para = (
            f"pop_ind_pre,{self.pop_pre},"
            f"pop_ind_post,{self.pop_post},"
            f"syn_type,{self.syn_type},"
        )
        group.create_dataset("syn_para", data=np.asarray([syn_para], dtype=h5py.string_dtype("utf-8")))
        group.create_dataset("stats_I_mean", data=np.asarray(self.stats_i_mean, dtype=np.float64))
        group.create_dataset("stats_I_std", data=np.asarray(self.stats_i_std, dtype=np.float64))
        # ReadH5.m currently looks up stats_std by mistake; keep both names for compatibility.
        group.create_dataset("stats_std", data=np.asarray(self.stats_i_std, dtype=np.float64))
        group.create_dataset("stats_s_time_mean", data=np.zeros((0,), dtype=np.float64))
        group.create_dataset("stats_s_time_cov", data=np.zeros((0, 0), dtype=np.float64))
        group.create_dataset("stats_I_time_mean", data=np.zeros((0,), dtype=np.float64))
        group.create_dataset("stats_I_time_var", data=np.zeros((0,), dtype=np.float64))
