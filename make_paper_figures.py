# Regenerates the article figures (overleaf/figures/*.pdf) from the v3 results (max rule).
# Usage: python make_paper_figures.py output/cooperation_experiment_v3_dist/final_v3/resumo_v3.csv overleaf/figures
import sys, pandas as pd, numpy as np, matplotlib
from matplotlib.ticker import MaxNLocator
matplotlib.use('Agg'); import matplotlib.pyplot as plt
r = pd.read_csv(sys.argv[1]); OUT = sys.argv[2]; I = 5
plt.rcParams.update({'font.family': 'serif', 'font.size': 9, 'axes.titlesize': 9.5, 'axes.labelsize': 9,
                     'legend.fontsize': 8, 'xtick.labelsize': 8, 'ytick.labelsize': 8, 'pdf.fonttype': 42,
                     'mathtext.fontset': 'cm', 'font.serif': ['cmr10'], 'axes.formatter.use_mathtext': True,
                     'axes.unicode_minus': False})
C = {'coop': '#2a78d6', 'ind': '#eb6834', 'fixed': '#1baf7a', 'ff': '#8a8985', 'ref': '#3d3c39', 'out': '#7a5cc4'}
TXT, GRID = '#3d3c39', '#e5e4df'
def style(ax, title, ylabel, xlabel=r'$|K|$ (cooperating providers)'):
    ax.set_title(title, loc='left', color='#0b0b0b'); ax.set_xlabel(xlabel, color=TXT); ax.set_ylabel(ylabel, color=TXT)
    ax.tick_params(colors=TXT); ax.grid(axis='y', color=GRID, lw=0.7)
    for s in ('top', 'right'): ax.spines[s].set_visible(False)
def curve(ax, mec, col, color, label, dashed=False, scale=100):
    s = r[r.mecanismo == mec].groupby(['base_index', 'k'])[col].mean().unstack('base_index') * scale
    m, sd = s.mean(axis=1), s.std(axis=1)
    ax.plot(m.index, m.values, '--' if dashed else '-', color=color, lw=1.8, marker=None if dashed else 'o', ms=4, label=label)
    ax.fill_between(m.index, m - sd, m + sd, color=color, alpha=0.13, lw=0)

# Figure: gain vs |K| and vs protected links
fig, axes = plt.subplots(1, 2, figsize=(6.3, 2.6), gridspec_kw={'width_ratios': [1, 1]})
ax = axes[0]; ax.axhline(0, color=TXT, lw=0.8)
curve(ax, 'demanda individual', 'd_eta_todos', C['ind'], 'Individual protection', dashed=True)
curve(ax, 'demanda cooperativa', 'd_eta_todos', C['coop'], 'Cooperative protection')
style(ax, '(a) Gain vs. group size', r'$\Delta\eta$ (pp)'); ax.set_xticks(range(I + 1))
ax.yaxis.set_major_locator(MaxNLocator(integer=True))
ax.legend(frameon=False, loc='upper left')
c = r[(r.mecanismo == 'demanda cooperativa') & (r.k > 0)]
ax = axes[1]
KCOL = ['#56B4E9', '#E69F00', '#009E73', '#CC79A7', '#0072B2']; KMK = ['o', 's', '^', 'D', 'P']  # Okabe-Ito
jit = np.random.default_rng(0).uniform(-0.18, 0.18, len(c))
for k in range(1, 6):
    m = (c.k == k).values
    ax.scatter(c.prot_max_links.values[m] + jit[m], c.d_eta_todos.values[m] * 100, s=16, marker=KMK[k - 1],
               color=KCOL[k - 1], edgecolors='#0b0b0b', linewidths=0.3, alpha=0.85, label=f'{k}')
ax.legend(title=r'$|K|$', frameon=False, loc='upper left', fontsize=8, title_fontsize=8, handletextpad=0.2, ncol=1)
style(ax, '(b) Gain vs. protected links (cooperative)', r'$\Delta\eta$ (pp)', 'protected links')
ax.xaxis.set_major_locator(MaxNLocator(integer=True))
fig.tight_layout(); fig.savefig(f'{OUT}/gain_vs_k.pdf', bbox_inches='tight'); plt.close(fig)

# Figure: costs vs |K|
fig, axes = plt.subplots(1, 2, figsize=(6.3, 2.6))
ax = axes[0]; ax.axhline(0, color=TXT, lw=0.8)
curve(ax, 'demanda individual', 'd_B_n_K', C['ind'], 'Individual protection', dashed=True)
curve(ax, 'demanda cooperativa', 'd_B_n_K', C['coop'], 'Cooperative protection')
style(ax, r'(a) Background blocking, members of $K$', r'$\Delta B_\mathrm{n}$ (pp)'); ax.set_xticks(range(1, I + 1)); ax.set_xlim(0.7, 5.3)
ax = axes[1]; ax.axhline(0, color=TXT, lw=0.8)
curve(ax, 'demanda cooperativa', 'd_eta_isolados', C['coop'], r'$\Delta\eta$')
curve(ax, 'demanda cooperativa', 'd_B_n_isolados', C['out'], r'$\Delta B_\mathrm{n}$', dashed=True)
style(ax, r'(b) Providers outside $K$ (cooperative)', 'change vs. reference (pp)'); ax.set_xticks(range(I)); ax.set_xlim(-0.2, 4.2)
ax.legend(frameon=False, loc='lower left')
axes[0].legend(frameon=False, loc='upper left')
fig.tight_layout()
fig.savefig(f'{OUT}/costs_vs_k.pdf', bbox_inches='tight'); plt.close(fig)

# Figure: trade-off at K = I (paired deltas)
kI = r[r.k == I].set_index(['mecanismo', 'base_index'])
ref = kI.loc['sem reserva']
def deltas(m):
    return (kI.loc[m]['B_n'] - ref['B_n']) * 100, (kI.loc[m]['eta_todos'] - ref['eta_todos']) * 100
fig, ax = plt.subplots(figsize=(3.95, 2.8))
fx, fy = [0], [0]
for p in (25, 55, 85):
    x, y = deltas(f'fixa {p}%'); fx.append(x.mean()); fy.append(y.mean())
    ax.errorbar(x.mean(), y.mean(), xerr=x.std(), yerr=y.std(), fmt='s', color=C['fixed'], ms=5, capsize=2, lw=1)
    ax.annotate(rf'$\rho={p}\%$', (x.mean(), y.mean()), xytext=(6, -10), textcoords='offset points', color=TXT, fontsize=8)
ax.plot(fx, fy, color=C['fixed'], lw=1.2, alpha=0.7, marker='s', ms=4, label='Fixed reservation')
for m, col, lab, mk in [('demanda cooperativa', C['coop'], 'Demand-driven, cooperative', 'o'),
                        ('demanda individual', C['ind'], 'Demand-driven, individual', 'D')]:
    x, y = deltas(m)
    ax.errorbar(x.mean(), y.mean(), xerr=x.std(), yerr=y.std(), fmt=mk, color=col, ms=6, capsize=2, lw=1, label=lab)
ax.plot(0, 0, 'o', color=C['ref'], ms=5, mec='white', zorder=5, label='Reference (no reservation)')
ax.axhline(0, color=GRID, lw=0.8); ax.axvline(0, color=GRID, lw=0.8)
style(ax, '', r'$\Delta\eta$ (pp)', r'$\Delta B_\mathrm{n}$ (pp)')
ax.legend(frameon=False, loc='upper left', fontsize=8)
fig.savefig(f'{OUT}/tradeoff.pdf', bbox_inches='tight'); plt.close(fig)

print('ok')
