import { useState } from "react";

/**
 * RoutineCard — displays AM/PM routine steps from /api/routine response.
 * Collapsible sections for AM/PM/Avoid/Lifestyle.
 */
function RoutineCard({ routine }) {
  if (!routine) return null;

  const [open, setOpen] = useState({ am: true, pm: true, avoid: false, lifestyle: false });

  const toggle = (key) => setOpen((prev) => ({ ...prev, [key]: !prev[key] }));

  const Section = ({ title, items, key, icon, emptyMsg }) => {
    if (!items || items.length === 0) return null;
    return (
      <details className="group border border-surface-border rounded-xl bg-white overflow-hidden" open={open[key]} onToggle={() => toggle(key)}>
        <summary className="flex items-center gap-3 px-4 py-3 cursor-pointer list-none">
          <span className="text-lg">{icon}</span>
          <h4 className="font-semibold text-slate-800 capitalize">{title}</h4>
          <span className="ml-auto text-sm text-slate-500">{items.length} step{items.length !== 1 ? "s" : ""}</span>
          <svg className="w-5 h-5 text-slate-400 transition-transform group-open:rotate-180" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" /></svg>
        </summary>
        <div className="px-4 pb-4 pt-2 animate-in slide-in-from-top-2 duration-200">
          <ul className="space-y-2">
            {items.map((item, i) => (
              <li key={i} className="flex items-start gap-3 p-3 rounded-lg bg-slate-50 border border-surface-border">
                <span className="flex-shrink-0 w-8 h-8 rounded-full bg-brand-100 text-brand-700 text-xs font-medium flex items-center justify-center">{i + 1}</span>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-slate-800">{item.step}: <span className="font-normal text-brand-700">{item.ingredient}</span></p>
                  {item.note && <p className="text-sm text-slate-500 mt-0.5">{item.note}</p>}
                </div>
              </li>
            ))}
          </ul>
        </div>
      </details>
    );
  };

  return (
    <div className="mt-8 space-y-4" aria-live="polite">
      <div className="flex items-center justify-between">
        <h3 className="text-xl font-semibold text-slate-800">Your Routine</h3>
        <span className="text-xs text-slate-500 bg-slate-100 px-2 py-1 rounded-full">Rule-based · Not medical advice</span>
      </div>

      <Section title="AM Routine" items={routine.am} key="am" icon="☀️" emptyMsg="No AM steps" />
      <Section title="PM Routine" items={routine.pm} key="pm" icon="🌙" emptyMsg="No PM steps" />
      <Section title="Avoid" items={routine.avoid?.map((s, i) => ({ step: "", ingredient: s, note: "" }))} key="avoid" icon="🚫" emptyMsg="" />
      <Section title="Lifestyle Tips" items={routine.lifestyle?.map((s, i) => ({ step: "", ingredient: s, note: "" }))} key="lifestyle" icon="💡" emptyMsg="" />

      {routine.sunscreen && (
        <div className="mt-4 p-4 rounded-xl bg-amber-50 border border-amber-200 flex items-start gap-3">
          <span className="text-2xl">☀️</span>
          <div>
            <p className="font-semibold text-amber-800">Sunscreen Reminder</p>
            <p className="text-sm text-amber-700 mt-0.5">{routine.sunscreen}</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default RoutineCard;