from __future__ import annotations

import math
from dataclasses import dataclass

import h5py
import numpy as np
import torch

from .config import PopulationConfig, PopulationRestartState, SynapseConfig, SynapseRestartState


@dataclass
class NeuronParams:
    cm: float = 0.25
    tau_ref: float = 2.0
    v_rt: float = -60.0
    v_lk: float = -70.0
    v_th: float = -50.0
    g_lk: float = 0.0167


class Population:
    def __init__(
        self,
        cfg: PopulationConfig,
        dt: float,
        step_tot: int,
        device: torch.device,
        restart_state: PopulationRestartState | None = None,
    ) -> None:
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

        if restart_state is not None:
            self._apply_restart_state(restart_state)

        self.i_leak = torch.zeros((self.n,), dtype=torch.float64, device=self.device)
        self.i_input = torch.zeros((self.n,), dtype=torch.float64, device=self.device)
        self.i_ampa = torch.zeros((self.n,), dtype=torch.float64, device=self.device)
        self.i_gaba = torch.zeros((self.n,), dtype=torch.float64, device=self.device)
        self.i_nmda = torch.zeros((self.n,), dtype=torch.float64, device=self.device)
        self.i_ext = torch.zeros((self.n,), dtype=torch.float64, device=self.device)
        self._zero_scalar = torch.zeros((), dtype=torch.float64, device=self.device)

        self.spikes_current = torch.empty((0,), dtype=torch.int64, device=self.device)
        self.spike_hist_parts: list[torch.Tensor] = []
        self.num_spikes_pop: list[int] = []
        self.num_ref_pop_parts: list[torch.Tensor] = []

        self.stats_v_mean: list[torch.Tensor] = []
        self.stats_v_std: list[torch.Tensor] = []
        self.stats_i_mean: list[torch.Tensor] = []
        self.stats_i_std: list[torch.Tensor] = []

        self.stats_step_count = 0
        self.i_ampa_time_sum = torch.zeros((self.n,), dtype=torch.float64, device=self.device)
        self.i_nmda_time_sum = torch.zeros((self.n,), dtype=torch.float64, device=self.device)
        self.i_gaba_time_sum = torch.zeros((self.n,), dtype=torch.float64, device=self.device)
        self.i_ext_time_sum = torch.zeros((self.n,), dtype=torch.float64, device=self.device)
        self.i_tot_time_sum = torch.zeros((self.n,), dtype=torch.float64, device=self.device)
        self.i_tot_time_sq_sum = torch.zeros((self.n,), dtype=torch.float64, device=self.device)
        self.v_time_sum = torch.zeros((self.n,), dtype=torch.float64, device=self.device)
        self.v_time_sq_sum = torch.zeros((self.n,), dtype=torch.float64, device=self.device)

        self.cov_record_enabled = False
        self.cov_time_start = 0
        self.cov_time_end = -1
        self.v_cov_count = 0
        self.v_cov_mean = torch.zeros((self.n,), dtype=torch.float64, device=self.device)
        self.v_cov_m2 = torch.zeros((self.n, self.n), dtype=torch.float64, device=self.device)
        if cfg.cov_time_start is not None and cfg.cov_time_end is not None and cfg.cov_time_end >= cfg.cov_time_start:
            self.cov_record_enabled = True
            self.cov_time_start = int(cfg.cov_time_start)
            self.cov_time_end = int(cfg.cov_time_end)

        self.lfp_record_enabled = False
        self.lfp_weights: torch.Tensor | None = None
        self.lfp_data_parts: list[torch.Tensor] = []
        if cfg.lfp_neurons is not None:
            lfp = np.asarray(cfg.lfp_neurons, dtype=np.float64)
            if lfp.ndim == 1:
                lfp = lfp.reshape(1, -1)
            if lfp.shape[1] != self.n:
                raise ValueError(
                    f"Population {self.index}: SAMP005/LFP_neurons width {lfp.shape[1]} != N {self.n}"
                )
            self.lfp_record_enabled = True
            self.lfp_weights = torch.tensor(lfp, dtype=torch.float64, device=self.device)

    def _apply_restart_state(self, restart_state: PopulationRestartState) -> None:
        v = np.asarray(restart_state.v, dtype=np.float64).reshape(-1)
        if v.size != self.n:
            raise ValueError(
                f"Population {self.index}: restart V length {v.size} != N {self.n}"
            )
        ref = np.asarray(restart_state.ref_step_left, dtype=np.int64).reshape(-1)
        if ref.size != self.n:
            raise ValueError(
                f"Population {self.index}: restart ref_step_left length {ref.size} != N {self.n}"
            )
        self.v = torch.tensor(v, dtype=torch.float64, device=self.device)
        self.ref_step_left = torch.tensor(ref, dtype=torch.int64, device=self.device)

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
            self.spike_hist_parts.append(self.spikes_current.clone())

        refractory = self.ref_step_left > 0
        # Match C++ semantics: count refractory neurons before decrementing the counters.
        self.num_ref_pop_parts.append(refractory.sum(dtype=torch.int64))
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

        self.stats_v_mean.append(self.v.mean())
        # C++ uses sample variance (N-1) via Welford.
        self.stats_v_std.append(self.v.std(unbiased=True) if self.n > 1 else self._zero_scalar)
        self.stats_i_mean.append(self.i_input.mean())
        self.stats_i_std.append(self.i_input.std(unbiased=True) if self.n > 1 else self._zero_scalar)

        self.stats_step_count += 1
        self.i_ampa_time_sum += self.i_ampa
        self.i_nmda_time_sum += self.i_nmda
        self.i_gaba_time_sum += self.i_gaba
        self.i_ext_time_sum += self.i_ext
        self.i_tot_time_sum += self.i_input
        self.i_tot_time_sq_sum += self.i_input * self.i_input
        self.v_time_sum += self.v
        self.v_time_sq_sum += self.v * self.v

        if self.lfp_record_enabled and self.lfp_weights is not None:
            lfp_sample = torch.matmul(self.lfp_weights, torch.abs(self.i_ampa) + torch.abs(self.i_gaba))
            self.lfp_data_parts.append(lfp_sample)

        if self.cov_record_enabled and self.cov_time_start <= step_current <= self.cov_time_end:
            self.v_cov_count += 1
            count_f = float(self.v_cov_count)
            delta = self.v - self.v_cov_mean
            self.v_cov_mean += delta / count_f
            delta2 = self.v - self.v_cov_mean
            self.v_cov_m2 += torch.outer(delta, delta2)

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
        if self.spike_hist_parts:
            spike_hist_tot = torch.cat(self.spike_hist_parts).detach().cpu().numpy().astype(np.int32)
        else:
            spike_hist_tot = np.zeros((0,), dtype=np.int32)

        if self.num_ref_pop_parts:
            num_ref_pop = torch.stack(self.num_ref_pop_parts).detach().cpu().numpy().astype(np.int32)
        else:
            num_ref_pop = np.zeros((0,), dtype=np.int32)

        if self.stats_v_mean:
            stats_v_mean = torch.stack(self.stats_v_mean).detach().cpu().numpy().astype(np.float64)
            stats_v_std = torch.stack(self.stats_v_std).detach().cpu().numpy().astype(np.float64)
            stats_i_mean = torch.stack(self.stats_i_mean).detach().cpu().numpy().astype(np.float64)
            stats_i_std = torch.stack(self.stats_i_std).detach().cpu().numpy().astype(np.float64)
        else:
            stats_v_mean = np.zeros((0,), dtype=np.float64)
            stats_v_std = np.zeros((0,), dtype=np.float64)
            stats_i_mean = np.zeros((0,), dtype=np.float64)
            stats_i_std = np.zeros((0,), dtype=np.float64)

        if self.stats_step_count > 0:
            steps_f = float(self.stats_step_count)
            stats_i_ampa_time_avg = (self.i_ampa_time_sum / steps_f).detach().cpu().numpy().astype(np.float64)
            stats_i_nmda_time_avg = (self.i_nmda_time_sum / steps_f).detach().cpu().numpy().astype(np.float64)
            stats_i_gaba_time_avg = (self.i_gaba_time_sum / steps_f).detach().cpu().numpy().astype(np.float64)
            stats_i_ext_time_avg = (self.i_ext_time_sum / steps_f).detach().cpu().numpy().astype(np.float64)
            stats_i_tot_time_mean_t = self.i_tot_time_sum / steps_f
            stats_v_time_mean_t = self.v_time_sum / steps_f
            stats_i_tot_time_mean = stats_i_tot_time_mean_t.detach().cpu().numpy().astype(np.float64)
            stats_v_time_mean = stats_v_time_mean_t.detach().cpu().numpy().astype(np.float64)

            if self.stats_step_count > 1:
                denom = float(self.stats_step_count - 1)
                n_f = float(self.stats_step_count)
                i_tot_var_t = (self.i_tot_time_sq_sum - (self.i_tot_time_sum * self.i_tot_time_sum) / n_f) / denom
                v_var_t = (self.v_time_sq_sum - (self.v_time_sum * self.v_time_sum) / n_f) / denom
                i_tot_var_t = torch.clamp(i_tot_var_t, min=0.0)
                v_var_t = torch.clamp(v_var_t, min=0.0)
                stats_i_tot_time_var = i_tot_var_t.detach().cpu().numpy().astype(np.float64)
                stats_v_time_var = v_var_t.detach().cpu().numpy().astype(np.float64)
            else:
                stats_i_tot_time_var = np.zeros((self.n,), dtype=np.float64)
                stats_v_time_var = np.zeros((self.n,), dtype=np.float64)

            ie_denom = stats_i_ampa_time_avg + stats_i_nmda_time_avg + stats_i_ext_time_avg
            stats_ie_ratio = np.divide(
                stats_i_gaba_time_avg,
                ie_denom,
                out=np.zeros_like(stats_i_gaba_time_avg),
                where=np.abs(ie_denom) > 1e-12,
            )
        else:
            stats_i_ampa_time_avg = np.zeros((self.n,), dtype=np.float64)
            stats_i_nmda_time_avg = np.zeros((self.n,), dtype=np.float64)
            stats_i_gaba_time_avg = np.zeros((self.n,), dtype=np.float64)
            stats_i_ext_time_avg = np.zeros((self.n,), dtype=np.float64)
            stats_i_tot_time_mean = np.zeros((self.n,), dtype=np.float64)
            stats_i_tot_time_var = np.zeros((self.n,), dtype=np.float64)
            stats_v_time_mean = np.zeros((self.n,), dtype=np.float64)
            stats_v_time_var = np.zeros((self.n,), dtype=np.float64)
            stats_ie_ratio = np.zeros((self.n,), dtype=np.float64)

        if self.cov_record_enabled and self.v_cov_count > 1:
            stats_v_time_cov = (self.v_cov_m2 / float(self.v_cov_count - 1)).detach().cpu().numpy().astype(np.float64)
        else:
            stats_v_time_cov = np.zeros((self.n, self.n), dtype=np.float64)

        if self.lfp_record_enabled and self.lfp_data_parts:
            lfp_data = torch.stack(self.lfp_data_parts, dim=1).detach().cpu().numpy().astype(np.float64)
        else:
            lfp_data = np.zeros((0, 0), dtype=np.float64)

        group.create_dataset("spike_hist_tot", data=spike_hist_tot)
        group.create_dataset("num_spikes_pop", data=np.asarray(self.num_spikes_pop, dtype=np.int32))
        group.create_dataset("num_ref_pop", data=num_ref_pop)
        group.create_dataset("pop_para", data=np.asarray([self.pop_para_string()], dtype=h5py.string_dtype("utf-8")))

        group.create_dataset("stats_V_mean", data=stats_v_mean)
        group.create_dataset("stats_V_std", data=stats_v_std)
        group.create_dataset("stats_I_input_mean", data=stats_i_mean)
        group.create_dataset("stats_I_input_std", data=stats_i_std)

        group.create_dataset("stats_I_AMPA_time_avg", data=stats_i_ampa_time_avg)
        group.create_dataset("stats_I_NMDA_time_avg", data=stats_i_nmda_time_avg)
        group.create_dataset("stats_I_GABA_time_avg", data=stats_i_gaba_time_avg)
        group.create_dataset("stats_I_ext_time_avg", data=stats_i_ext_time_avg)
        group.create_dataset("stats_I_tot_time_mean", data=stats_i_tot_time_mean)
        group.create_dataset("stats_I_tot_time_var", data=stats_i_tot_time_var)
        group.create_dataset("stats_V_time_mean", data=stats_v_time_mean)
        group.create_dataset("stats_V_time_cov", data=stats_v_time_cov)
        group.create_dataset("stats_V_time_var", data=stats_v_time_var)
        group.create_dataset("stats_IE_ratio", data=stats_ie_ratio)
        group.create_dataset("LFP_data", data=lfp_data)

    def write_restart(self, group: h5py.Group, step_tot: int) -> None:
        pop_group = group.create_group(f"pop{self.index}")
        pop_group.create_dataset("neuron_model", data=np.asarray([0], dtype=np.int32))
        pop_group.create_dataset("pop_ind", data=np.asarray([self.index], dtype=np.int32))
        pop_group.create_dataset("N", data=np.asarray([self.n], dtype=np.int32))
        pop_group.create_dataset("dt", data=np.asarray([self.dt], dtype=np.float64))
        pop_group.create_dataset("step_tot", data=np.asarray([step_tot], dtype=np.int32))
        pop_group.create_dataset("tau_ref", data=np.asarray([self.params.tau_ref], dtype=np.float64))
        pop_group.create_dataset("Cm", data=np.asarray([self.params.cm], dtype=np.float64))
        pop_group.create_dataset("V_rt", data=np.asarray([self.params.v_rt], dtype=np.float64))
        pop_group.create_dataset("V_lk", data=np.asarray([self.params.v_lk], dtype=np.float64))
        pop_group.create_dataset("V_th", data=np.asarray([self.params.v_th], dtype=np.float64))
        pop_group.create_dataset("g_lk", data=np.asarray([self.params.g_lk], dtype=np.float64))

        pop_group.create_dataset("V", data=self.v.detach().cpu().numpy().astype(np.float64))
        pop_group.create_dataset("I_leak", data=np.zeros((self.n,), dtype=np.float64))
        pop_group.create_dataset("I_input", data=np.zeros((self.n,), dtype=np.float64))
        pop_group.create_dataset("I_AMPA", data=np.zeros((self.n,), dtype=np.float64))
        pop_group.create_dataset("I_GABA", data=np.zeros((self.n,), dtype=np.float64))
        pop_group.create_dataset("I_NMDA", data=np.zeros((self.n,), dtype=np.float64))
        pop_group.create_dataset("I_GJ", data=np.zeros((self.n,), dtype=np.float64))
        pop_group.create_dataset("I_ext", data=np.zeros((self.n,), dtype=np.float64))
        pop_group.create_dataset("I_ext_mean", data=np.zeros((self.n,), dtype=np.float64))
        pop_group.create_dataset("g_ext_mean", data=np.zeros((self.n,), dtype=np.float64))
        pop_group.create_dataset("ref_steps", data=np.asarray([self.ref_steps], dtype=np.int32))
        pop_group.create_dataset(
            "ref_step_left",
            data=self.ref_step_left.detach().cpu().numpy().astype(np.int32),
        )
        pop_group.create_dataset("I_K", data=np.zeros((self.n,), dtype=np.float64))
        pop_group.create_dataset("dg_K_heter", data=np.zeros((self.n,), dtype=np.float64))
        pop_group.create_dataset("V_ext", data=np.asarray([0.0], dtype=np.float64))
        pop_group.create_dataset("spike_freq_adpt", data=np.asarray([0], dtype=np.int32))
        pop_group.create_dataset("V_K", data=np.asarray([-80.0], dtype=np.float64))
        pop_group.create_dataset("dg_K", data=np.asarray([0.0], dtype=np.float64))
        pop_group.create_dataset("tau_K", data=np.asarray([1.0], dtype=np.float64))
        pop_group.create_dataset("exp_K_step", data=np.asarray([1.0], dtype=np.float64))
        pop_group.create_dataset("step_perturb", data=np.asarray([-1], dtype=np.int32))
        pop_group.create_dataset("spike_removed", data=np.asarray([0], dtype=np.int32))
        pop_group.create_dataset("my_seed", data=np.asarray([0], dtype=np.int32))


class Synapse:
    def __init__(
        self,
        cfg: SynapseConfig,
        dt: float,
        n_pre: int,
        n_post: int,
        device: torch.device,
        restart_state: SynapseRestartState | None = None,
    ) -> None:
        self.index = cfg.index
        self.syn_type = cfg.syn_type
        self.pop_pre = cfg.pop_pre
        self.pop_post = cfg.pop_post
        self.dt = dt
        self.device = device

        self.n_pre = n_pre
        self.n_post = n_post
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
        self.buffer_flat = self.buffer.view(-1)
        self.gs_sum = torch.zeros((n_post,), dtype=torch.float64, device=self.device)
        # Model-0 state variables in C++ implementation.
        self.s_pre = torch.zeros((self.n_pre,), dtype=torch.float64, device=self.device)
        self.trans_left = torch.zeros((self.n_pre,), dtype=torch.int64, device=self.device)
        self._zero_scalar = torch.zeros((), dtype=torch.float64, device=self.device)

        if restart_state is not None:
            self._apply_restart_state(restart_state)

        if self.pre_idx.numel() > 0:
            order = torch.argsort(self.pre_idx)
            self.pre_idx_sorted = self.pre_idx[order]
            self.post_idx_sorted = self.post_idx[order]
            self.weight_sorted = self.weight[order]
            self.delay_steps_sorted = self.delay_steps[order]
            pre_counts = torch.bincount(self.pre_idx_sorted, minlength=self.n_pre)
            self.pre_ptr = torch.zeros((self.n_pre + 1,), dtype=torch.int64, device=self.device)
            self.pre_ptr[1:] = torch.cumsum(pre_counts, dim=0)
        else:
            self.pre_idx_sorted = self.pre_idx
            self.post_idx_sorted = self.post_idx
            self.weight_sorted = self.weight
            self.delay_steps_sorted = self.delay_steps
            self.pre_ptr = torch.zeros((self.n_pre + 1,), dtype=torch.int64, device=self.device)

        self.stats_i_mean: list[torch.Tensor] = []
        self.stats_i_std: list[torch.Tensor] = []
        self.stats_step_count = 0
        self.s_time_sum = torch.zeros((self.n_pre,), dtype=torch.float64, device=self.device)
        self.s_time_sq_sum = torch.zeros((self.n_pre,), dtype=torch.float64, device=self.device)
        self.i_time_sum = torch.zeros((self.n_post,), dtype=torch.float64, device=self.device)
        self.i_time_sq_sum = torch.zeros((self.n_post,), dtype=torch.float64, device=self.device)

        self.cov_record_enabled = False
        self.cov_time_start = 0
        self.cov_time_end = -1
        self.s_cov_count = 0
        self.s_cov_mean = torch.zeros((self.n_pre,), dtype=torch.float64, device=self.device)
        self.s_cov_m2 = torch.zeros((self.n_pre, self.n_pre), dtype=torch.float64, device=self.device)
        if cfg.cov_time_start is not None and cfg.cov_time_end is not None and cfg.cov_time_end >= cfg.cov_time_start:
            self.cov_record_enabled = True
            self.cov_time_start = int(cfg.cov_time_start)
            self.cov_time_end = int(cfg.cov_time_end)

    def _apply_restart_state(self, restart_state: SynapseRestartState) -> None:
        if restart_state.gs_sum is not None:
            gs_sum = np.asarray(restart_state.gs_sum, dtype=np.float64).reshape(-1)
            if gs_sum.size != self.gs_sum.numel():
                raise ValueError(
                    f"Synapse {self.index}: restart gs_sum length {gs_sum.size} != N_post {self.gs_sum.numel()}"
                )
            self.gs_sum = torch.tensor(gs_sum, dtype=torch.float64, device=self.device)

        if restart_state.d_gs_sum_buffer is not None:
            buffer_arr = np.asarray(restart_state.d_gs_sum_buffer, dtype=np.float64)
            if buffer_arr.ndim == 1:
                buffer_arr = buffer_arr.reshape(1, -1)
            if buffer_arr.shape[1] != self.gs_sum.numel():
                raise ValueError(
                    f"Synapse {self.index}: restart buffer width {buffer_arr.shape[1]} != N_post {self.gs_sum.numel()}"
                )
            self.buffer_steps = int(buffer_arr.shape[0])
            self.buffer = torch.tensor(buffer_arr, dtype=torch.float64, device=self.device)
            self.buffer_flat = self.buffer.view(-1)

        if restart_state.s_pre is not None:
            s_pre = np.asarray(restart_state.s_pre, dtype=np.float64).reshape(-1)
            if s_pre.size != self.n_pre:
                raise ValueError(
                    f"Synapse {self.index}: restart s_pre length {s_pre.size} != N_pre {self.n_pre}"
                )
            self.s_pre = torch.tensor(s_pre, dtype=torch.float64, device=self.device)

        if restart_state.trans_left is not None:
            trans_left = np.asarray(restart_state.trans_left, dtype=np.int64).reshape(-1)
            if trans_left.size != self.n_pre:
                raise ValueError(
                    f"Synapse {self.index}: restart trans_left length {trans_left.size} != N_pre {self.n_pre}"
                )
            self.trans_left = torch.tensor(trans_left, dtype=torch.int64, device=self.device)

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
            valid_spikes = pre_spikes[(pre_spikes >= 0) & (pre_spikes < self.n_pre)]
            if valid_spikes.numel() > 0:
                self.trans_left[valid_spikes] += self.steps_trans

        # Match C++ model-0 transmitter dynamics.
        active_pre = torch.nonzero(self.trans_left > 0, as_tuple=False).reshape(-1)
        if active_pre.numel() > 0:
            starts = self.pre_ptr[active_pre]
            ends = self.pre_ptr[active_pre + 1]
            lengths = ends - starts
            has_edges = lengths > 0

            if has_edges.any():
                active_pre_edges = active_pre[has_edges]
                starts = starts[has_edges]
                lengths = lengths[has_edges]

                cum_lengths = torch.cumsum(lengths, dim=0)
                total_edges = int(cum_lengths[-1].item())

                seg_start = torch.repeat_interleave(starts, lengths)
                seg_base = torch.repeat_interleave(cum_lengths - lengths, lengths)
                edge_pos = seg_start + (torch.arange(total_edges, device=self.device, dtype=torch.int64) - seg_base)
                pre_for_edge = torch.repeat_interleave(active_pre_edges, lengths)

                values = self.weight_sorted[edge_pos] * (self.k_trans * (1.0 - self.s_pre[pre_for_edge]))
                posts = self.post_idx_sorted[edge_pos]
                slots = (self.delay_steps_sorted[edge_pos] + step_current) % self.buffer_steps
                flat_index = slots * self.n_post + posts
                self.buffer_flat.index_add_(0, flat_index, values)

            self.trans_left[active_pre] -= 1
            self.s_pre[active_pre] += self.k_trans * (1.0 - self.s_pre[active_pre])

        self.s_pre *= self.exp_step_decay

        slot_now = int(step_current % self.buffer_steps)
        self.gs_sum += self.buffer[slot_now]
        self.gs_sum *= self.exp_step_decay
        self.buffer[slot_now].zero_()

        v_post = populations[self.pop_post].v
        current = self._calc_current(v_post)
        populations[self.pop_post].receive_current(current, self.pop_pre, self.syn_type)

        self.stats_i_mean.append(current.mean())
        self.stats_i_std.append(current.std(unbiased=False) if current.numel() > 1 else self._zero_scalar)
        self.stats_step_count += 1
        self.s_time_sum += self.s_pre
        self.s_time_sq_sum += self.s_pre * self.s_pre
        self.i_time_sum += current
        self.i_time_sq_sum += current * current

        if self.cov_record_enabled and self.cov_time_start <= step_current <= self.cov_time_end:
            self.s_cov_count += 1
            count_f = float(self.s_cov_count)
            delta = self.s_pre - self.s_cov_mean
            self.s_cov_mean += delta / count_f
            delta2 = self.s_pre - self.s_cov_mean
            self.s_cov_m2 += torch.outer(delta, delta2)

    def write_restart(self, group: h5py.Group, step_tot: int) -> None:
        syn_group = group.create_group(f"syn{self.index}")
        syn_group.create_dataset("dt", data=np.asarray([self.dt], dtype=np.float64))
        syn_group.create_dataset("step_tot", data=np.asarray([step_tot], dtype=np.int32))
        syn_group.create_dataset("pop_ind_pre", data=np.asarray([self.pop_pre], dtype=np.int32))
        syn_group.create_dataset("pop_ind_post", data=np.asarray([self.pop_post], dtype=np.int32))
        syn_group.create_dataset("N_pre", data=np.asarray([self.n_pre], dtype=np.int32))
        syn_group.create_dataset("N_post", data=np.asarray([self.gs_sum.numel()], dtype=np.int32))
        syn_group.create_dataset("syn_type", data=np.asarray([self.syn_type], dtype=np.int32))
        syn_group.create_dataset("I", data=self.pre_idx.detach().cpu().numpy().astype(np.int32))
        syn_group.create_dataset("J", data=self.post_idx.detach().cpu().numpy().astype(np.int32))
        syn_group.create_dataset("K", data=self.weight.detach().cpu().numpy().astype(np.float64))
        syn_group.create_dataset(
            "D",
            data=(self.delay_steps.detach().cpu().numpy().astype(np.float64) * float(self.dt)),
        )
        syn_group.create_dataset("gs_sum", data=self.gs_sum.detach().cpu().numpy().astype(np.float64))

        gsm_group = syn_group.create_group("Gsm_0")
        gsm_group.create_dataset("buffer_steps", data=np.asarray([self.buffer_steps], dtype=np.int32))
        gsm_group.create_dataset("s", data=self.s_pre.detach().cpu().numpy().astype(np.float64))
        gsm_group.create_dataset(
            "trans_left",
            data=self.trans_left.detach().cpu().numpy().astype(np.int32),
        )
        gsm_group.create_dataset(
            "d_gs_sum_buffer",
            data=self.buffer.detach().cpu().numpy().astype(np.float64),
        )

    def write_results(self, group: h5py.Group) -> None:
        syn_para = (
            f"pop_ind_pre,{self.pop_pre},"
            f"pop_ind_post,{self.pop_post},"
            f"syn_type,{self.syn_type},"
        )
        group.create_dataset("syn_para", data=np.asarray([syn_para], dtype=h5py.string_dtype("utf-8")))
        if self.stats_i_mean:
            stats_i_mean = torch.stack(self.stats_i_mean).detach().cpu().numpy().astype(np.float64)
            stats_i_std = torch.stack(self.stats_i_std).detach().cpu().numpy().astype(np.float64)
        else:
            stats_i_mean = np.zeros((0,), dtype=np.float64)
            stats_i_std = np.zeros((0,), dtype=np.float64)

        if self.stats_step_count > 0:
            steps_f = float(self.stats_step_count)
            s_time_mean_t = self.s_time_sum / steps_f
            i_time_mean_t = self.i_time_sum / steps_f
            stats_s_time_mean = s_time_mean_t.detach().cpu().numpy().astype(np.float64)
            stats_i_time_mean = i_time_mean_t.detach().cpu().numpy().astype(np.float64)

            if self.stats_step_count > 1:
                denom = float(self.stats_step_count - 1)
                n_f = float(self.stats_step_count)
                i_time_var_t = (self.i_time_sq_sum - (self.i_time_sum * self.i_time_sum) / n_f) / denom
                i_time_var_t = torch.clamp(i_time_var_t, min=0.0)
                stats_i_time_var = i_time_var_t.detach().cpu().numpy().astype(np.float64)
            else:
                stats_i_time_var = np.zeros((self.n_post,), dtype=np.float64)
        else:
            stats_s_time_mean = np.zeros((self.n_pre,), dtype=np.float64)
            stats_i_time_mean = np.zeros((self.n_post,), dtype=np.float64)
            stats_i_time_var = np.zeros((self.n_post,), dtype=np.float64)

        if self.cov_record_enabled and self.s_cov_count > 1:
            stats_s_time_cov = (self.s_cov_m2 / float(self.s_cov_count - 1)).detach().cpu().numpy().astype(np.float64)
        elif self.cov_record_enabled:
            stats_s_time_cov = np.zeros((self.n_pre, self.n_pre), dtype=np.float64)
        else:
            stats_s_time_cov = np.zeros((0, 0), dtype=np.float64)
        group.create_dataset("stats_I_mean", data=stats_i_mean)
        group.create_dataset("stats_I_std", data=stats_i_std)
        # ReadH5.m currently looks up stats_std by mistake; keep both names for compatibility.
        group.create_dataset("stats_std", data=stats_i_std)
        group.create_dataset("stats_s_time_mean", data=stats_s_time_mean)
        group.create_dataset("stats_s_time_cov", data=stats_s_time_cov)
        group.create_dataset("stats_I_time_mean", data=stats_i_time_mean)
        group.create_dataset("stats_I_time_var", data=stats_i_time_var)
