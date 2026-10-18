/**
 * Bloom root component — placeholder until Stage 10.
 * Owns all app state and view transitions in the final build.
 */
function App() {
  return (
    <div className="min-h-screen bg-surface-subtle font-sans">
      <header className="sticky top-0 z-10 h-16 bg-white border-b border-surface-border flex items-center justify-between px-4 sm:px-8">
        <span className="text-xl font-semibold text-brand-700">Bloom</span>
        <span className="text-xs text-slate-400">Not medical advice</span>
      </header>
      <main className="max-w-4xl mx-auto px-4 sm:px-8 py-16 text-center text-slate-500">
        Scaffold OK — pipeline UI arrives in Stage 10.
      </main>
    </div>
  );
}

export default App;
