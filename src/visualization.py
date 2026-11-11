"""Every chart is computed from the analysis or prospective planning assumptions."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter, NullFormatter
import numpy as np
from .experiment_design import Design, sample_size

BLUE,TEAL,RED = '#24547A','#008577','#BC4855'

def charts(results: dict, quality: dict, business: dict, d: Design, folder: Path) -> None:
    folder.mkdir(parents=True,exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'axes.spines.top':False,
        'axes.spines.right':False,'axes.titleweight':'bold','figure.facecolor':'white','axes.labelcolor':'#243746'})
    def save(fig, name):
        fig.text(.01,.01,f'SYNTHETIC randomized experiment | fixed seed {d.seed}',fontsize=8,color='#666666')
        fig.tight_layout(rect=(0,.04,1,1))
        fig.savefig(folder/name,dpi=200,bbox_inches='tight',metadata={'Software':'healthcare-sms-ab-testing'})
        plt.close(fig)
    r=results['primary']
    fig,ax=plt.subplots(figsize=(7,4.5))
    for i,(label,a,color) in enumerate([('Control',r['control'],BLUE),('SMS assignment',r['treatment'],TEAL)]):
        ax.bar(i,a['rate']*100,color=color,width=.55)
        ax.errorbar(i,a['rate']*100,yerr=np.array([[a['rate']-a['rate_ci'][0]],[a['rate_ci'][1]-a['rate']]])*100,fmt='none',color='black',capsize=5)
        ax.text(i,a['rate_ci'][1]*100+.8,f"{a['rate']:.1%}\nn = {a['n']:,}",ha='center')
    ax.set(xticks=[0,1],xticklabels=['Control','SMS assignment'],ylabel='No-show rate (%)',ylim=(0,28),title='Does assignment to SMS reduce no-shows?')
    ax.text(.02,.95,'Bars: ITT rates | whiskers: 95% Wilson intervals',transform=ax.transAxes,fontsize=9)
    save(fig,'01_no_show_rates.png')
    fig,ax=plt.subplots(figsize=(8,3.5))
    ax.errorbar(r['effect_pp'],0,xerr=np.array([[r['effect']-r['ci'][0]],[r['ci'][1]-r['effect']]])*100,fmt='o',color=TEAL,capsize=7,markersize=9)
    ax.axvline(0,color=RED,label='No effect')
    ax.axvline(-100*d.minimum_business_reduction,color=BLUE,linestyle='--',label='Business point-estimate threshold')
    ax.set(yticks=[],xlabel='Treatment − control (percentage points; negative = improvement)',title='How large and uncertain is the estimated effect?',ylim=(-1,1))
    ax.legend(loc='upper left',fontsize=9)
    save(fig,'02_treatment_effect.png')
    fig,ax=plt.subplots(figsize=(7,4.5))
    effects=np.linspace(.01,.06,51)
    for power in [.8,.9]:
        ax.plot(effects*100,[2*sample_size(d.baseline,float(e),d.alpha,power) for e in effects],label=f'{power:.0%} power')
    ax.scatter([d.mde*100],[quality['rows']],color=RED,zorder=3,label='Selected design')
    ax.set(xlabel='Minimum detectable reduction (percentage points)',ylabel='Required total sample (log scale)',yscale='log',title='Smaller effects require larger experiments')
    ax.set_yticks([2000,5000,10000,20000,40000])
    ax.yaxis.set_major_formatter(ScalarFormatter())
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.legend(); ax.grid(alpha=.2)
    save(fig,'03_sample_size.png')
    fig,(ax,bx)=plt.subplots(1,2,figsize=(11,4.8),gridspec_kw={'width_ratios':[1,2]})
    ax.bar(['Control','SMS'],[quality['control_n'],quality['treatment_n']],color=[BLUE,TEAL])
    ax.axhline(quality['rows']/2,color=RED,linestyle='--')
    ax.set(ylabel='Randomized patients',title=f"Allocation: SRM p = {quality['srm_p_value']:.3f}")
    balance=quality['covariate_balance']
    bx.barh([b['covariate'].replace('specialty_','') for b in balance],[b['smd'] for b in balance],color=TEAL)
    bx.axvline(-.1,color=RED,linestyle='--');bx.axvline(.1,color=RED,linestyle='--')
    bx.set(xlim=(-.2,.2),xlabel='Standardized mean difference',title='Pre-treatment balance (diagnostic only)')
    save(fig,'04_randomization.png')
    fig,axes=plt.subplots(1,2,figsize=(10,4))
    for ax,metric,title in zip(axes,['cancelled','complaint'],['Cancellation','Complaint']):
        g=results['guardrails'][metric]
        ax.errorbar(100*g['effect'],0,xerr=np.array([[g['effect']-g['ci'][0]],[g['ci'][1]-g['effect']]])*100,fmt='o',color=TEAL,capsize=5)
        ax.axvline(100*g['margin'],color=RED,linestyle='--',label='Maximum allowed increase')
        ax.axvline(0,color='#999999',linewidth=.8)
        ax.set(title=title+' safety gate',yticks=[],xlabel='Treatment − control (percentage points)',ylim=(-1,1))
        ax.legend(loc='upper left',fontsize=8)
    save(fig,'05_guardrails.png')
    fig,ax=plt.subplots(figsize=(8,4.7))
    fractions=np.linspace(0,1,101)
    low,point,high=business['avoided_no_shows_low_point_high']
    cost=business['sms_and_fixed_cost_sar']
    ax.fill_between(fractions*100,low*d.capacity_value*fractions-cost,high*d.capacity_value*fractions-cost,color=TEAL,alpha=.16,label='Primary 95% CI propagated; inputs fixed')
    ax.plot(fractions*100,point*d.capacity_value*fractions-cost,color=TEAL,label='Point estimate')
    ax.axhline(0,color=RED);ax.axvline(d.realization*100,color=BLUE,linestyle='--',label='Base scenario')
    ax.set(xlabel='Avoided no-shows converted to usable capacity (%)',ylabel='Illustrative monthly net value (SAR)',title='Value depends on whether freed capacity is usable')
    ax.legend(fontsize=9);ax.grid(alpha=.15)
    save(fig,'06_business_sensitivity.png')
