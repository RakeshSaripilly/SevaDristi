import React from 'react';
import { IndianRupee, Footprints, ShieldAlert, Info } from 'lucide-react';
import { useTranslation } from '../hooks/useTranslation';

interface WageSavedDashboardProps {
  casesProcessed: number;
  issuesPreempted: number;
  repeatVisitsAvoided: number;
}

export const WageSavedDashboard: React.FC<WageSavedDashboardProps> = ({
  casesProcessed,
  issuesPreempted,
  repeatVisitsAvoided,
}) => {
  const { t } = useTranslation();

  // Model assumption: ~₹450 daily rural agricultural/unorganized wage + ~₹80 round-trip RTC bus transit
  const estimatedSavingsINR = repeatVisitsAvoided * 530;

  return (
    <div className="bg-gradient-to-r from-emerald-900 to-slate-900 rounded-2xl p-5 text-white shadow-lg space-y-3">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 border-b border-emerald-800/60 pb-2">
        <div className="flex items-center space-x-2">
          <div className="p-1.5 rounded-lg bg-emerald-500/20 text-emerald-400">
            <IndianRupee className="w-4 h-4" />
          </div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-300">
            {t('wage_dashboard_title')}
          </h3>
        </div>
        <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-950/80 text-emerald-400 border border-emerald-800">
          Simulated Heuristic Metrics
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        {/* Metric 1 */}
        <div className="bg-slate-800/80 rounded-xl p-3 border border-emerald-900/60 flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
            <IndianRupee className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[11px] text-slate-300 block">{t('estimated_wages_saved')}</span>
            <span className="text-lg font-black text-white">
              ₹{estimatedSavingsINR.toLocaleString()}
            </span>
          </div>
        </div>

        {/* Metric 2 */}
        <div className="bg-slate-800/80 rounded-xl p-3 border border-emerald-900/60 flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-blue-500/10 text-blue-400">
            <Footprints className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[11px] text-slate-300 block">{t('visits_prevented')}</span>
            <span className="text-lg font-black text-white">{repeatVisitsAvoided} trips</span>
          </div>
        </div>

        {/* Metric 3 */}
        <div className="bg-slate-800/80 rounded-xl p-3 border border-emerald-900/60 flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-amber-500/10 text-amber-400">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <span className="text-[11px] text-slate-300 block">{t('discrepancies_caught')}</span>
            <span className="text-lg font-black text-white">{issuesPreempted} flagged</span>
          </div>
        </div>
      </div>

      {/* Assumptions Disclaimer */}
      <div className="flex items-start space-x-2 text-[10px] text-emerald-300/80 pt-1">
        <Info className="w-3.5 h-3.5 shrink-0 mt-0.5" />
        <p>{t('simulated_estimate_disclaimer')} (Calculated on {casesProcessed} simulated sessions).</p>
      </div>
    </div>
  );
};
