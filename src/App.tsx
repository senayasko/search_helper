import { useEffect, useMemo, useRef, useState } from 'react';
import { AnimatePresence, motion, MotionConfig } from 'motion/react';
import {
  ArrowDownWideNarrow, ArrowLeft, ArrowRight, Bookmark, Check, ChevronDown, Command,
  Compass, GraduationCap, Heart, MapPin, Maximize2, Minus, Moon, Search, SlidersHorizontal,
  Sparkles, Sun, X, Zap,
} from 'lucide-react';
import csvFallback from '../universite_verileri.csv?raw';
import { emptyFilters, filterPrograms, getSuggestions, normalize, numberFormat, parsePrograms, scoreFormat, type Filters, type Program, type SortKey } from './data';

type Theme = 'dark' | 'light';
type View = 'home' | 'results' | 'favorites';
type MotionChoice = 'system' | 'full' | 'reduced';

function stored<T>(key: string, fallback: T): T {
  try { const value = localStorage.getItem(key); return value ? JSON.parse(value) as T : fallback; }
  catch { return fallback; }
}

function useStored<T>(key: string, fallback: T): [T, (value: T | ((previous: T) => T)) => void] {
  const [value, setValue] = useState<T>(() => stored(key, fallback));
  useEffect(() => { localStorage.setItem(key, JSON.stringify(value)); }, [key, value]);
  return [value, setValue];
}

const sortLabels: Record<SortKey, string> = {
  'score-desc': 'Taban puan: yüksekten', 'score-asc': 'Taban puan: düşükten',
  'rank-asc': 'Başarı sırası: iyiden', 'rank-desc': 'Başarı sırası: sondan',
  university: 'Üniversite: A–Z', department: 'Bölüm: A–Z',
};

function IconButton({ label, children, onClick, className = '' }: { label: string; children: React.ReactNode; onClick: () => void; className?: string }) {
  return <button className={`icon-button ${className}`} type="button" aria-label={label} title={label} onClick={onClick}>{children}</button>;
}

function WindowBar({ theme }: { theme: Theme }) {
  return <div className="window-bar">
    <div className="window-brand"><span className="brand-glyph"><span /></span><span>ÜNİ<span className="brand-dot">.</span>ARA</span><span className="window-brand-label">/ keşif alanı</span></div>
    <div className="window-drag" />
    {window.desktop && <div className="window-controls">
      <IconButton label="Küçült" onClick={() => window.desktop?.minimize()}><Minus size={15} /></IconButton>
      <IconButton label="Büyüt veya geri al" onClick={() => window.desktop?.toggleMaximize()}><Maximize2 size={13} /></IconButton>
      <IconButton label="Kapat" className="close-button" onClick={() => window.desktop?.close()}><X size={16} /></IconButton>
    </div>}
    <span className="window-theme-marker" data-theme={theme} />
  </div>;
}

function Highlight({ text, query }: { text: string; query: string }) {
  const q = normalize(query);
  if (!q) return <>{text}</>;
  const index = normalize(text).indexOf(q);
  if (index < 0) return <>{text}</>;
  return <>{text.slice(0, index)}<mark>{text.slice(index, index + query.length)}</mark>{text.slice(index + query.length)}</>;
}

function SearchField({ value, onChange, onSubmit, programs, inputRef, compact = false }: {
  value: string; onChange: (value: string) => void; onSubmit: (value?: string) => void;
  programs: Program[]; inputRef: React.RefObject<HTMLInputElement | null>; compact?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(-1);
  const listRef = useRef<HTMLDivElement>(null);
  const listId = compact ? 'result-search-suggestions' : 'home-search-suggestions';
  const suggestions = useMemo(() => getSuggestions(programs, value), [programs, value]);
  useEffect(() => {
    if (active >= 0) listRef.current?.querySelector(`[data-suggestion-index="${active}"]`)?.scrollIntoView({ block: 'nearest' });
  }, [active]);
  const choose = (label: string) => { onChange(label); setOpen(false); setActive(-1); onSubmit(label); };
  const onKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'ArrowDown' && suggestions.length) { event.preventDefault(); setOpen(true); setActive((v) => Math.min(v + 1, suggestions.length - 1)); }
    if (event.key === 'ArrowUp' && suggestions.length) { event.preventDefault(); setActive((v) => Math.max(v - 1, 0)); }
    if (event.key === 'Escape') { setOpen(false); setActive(-1); }
    if (event.key === 'Enter') { event.preventDefault(); active >= 0 && open ? choose(suggestions[active].label) : (setOpen(false), onSubmit()); }
  };
  return <div className={`search-shell ${compact ? 'search-shell-compact' : ''}`}>
    <div className="search-box">
      <Search size={compact ? 19 : 23} strokeWidth={2.1} className="search-icon" />
      <input ref={inputRef} value={value} onChange={(event) => { onChange(event.target.value); setOpen(true); setActive(-1); }} onKeyDown={onKeyDown}
        onFocus={() => setOpen(true)} onBlur={() => window.setTimeout(() => setOpen(false), 150)}
        aria-label="Üniversite, bölüm veya şehir ara" aria-expanded={open && suggestions.length > 0}
        aria-autocomplete="list" aria-controls={listId} aria-activedescendant={active >= 0 ? `${listId}-${active}` : undefined}
        placeholder="Üniversite, bölüm veya şehir ara..." autoComplete="off" />
      {value && <IconButton label="Aramayı temizle" onClick={() => { onChange(''); inputRef.current?.focus(); }}><X size={17} /></IconButton>}
      {!compact && <button className="search-submit" type="button" onClick={() => onSubmit()}>Keşfet <ArrowRight size={18} /></button>}
      {compact && <span className="search-shortcut">⌘ K</span>}
    </div>
    <AnimatePresence>
      {open && suggestions.length > 0 && <motion.div ref={listRef} id={listId} className="suggestions" role="listbox" initial={{ opacity: 0, y: -8, scale: .985 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, y: -6, scale: .985 }} transition={{ duration: .18 }}>
        <div className="suggestions-title">ÖNERİLER <span>↑ ↓ seç · ↵ aç</span></div>
        {suggestions.map((item, index) => <button id={`${listId}-${index}`} data-suggestion-index={index} className={`suggestion ${active === index ? 'selected' : ''}`} type="button" role="option" aria-selected={active === index} key={`${item.kind}-${item.label}`} onMouseDown={(event) => event.preventDefault()} onClick={() => choose(item.label)}>
          <span className="suggestion-icon">{item.kind === 'Şehir' ? <MapPin size={17} /> : item.kind === 'Üniversite' ? <GraduationCap size={17} /> : <Compass size={17} />}</span>
          <span className="suggestion-name"><Highlight text={item.label} query={value} /></span><span className="suggestion-kind">{item.kind}</span><ArrowRight size={15} className="suggestion-arrow" />
        </button>)}
      </motion.div>}
    </AnimatePresence>
  </div>;
}

function KpiCard({ icon, value, label, caption, onClick, index }: { icon: React.ReactNode; value: string; label: string; caption: string; onClick: () => void; index: number }) {
  return <motion.button type="button" className={`kpi-card kpi-${index}`} onClick={onClick}
    initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: .18 + index * .08, duration: .5 }}
    whileHover={{ y: -7, scale: 1.015 }} whileTap={{ scale: .985 }}>
    <span className="kpi-top"><span className="kpi-icon">{icon}</span><ArrowRight size={19} className="kpi-arrow" /></span>
    <span className="kpi-value">{value}</span>
    <span className="kpi-label">{label}</span>
    <span className="kpi-caption">{caption}</span>
  </motion.button>;
}

function ProgramCard({ program, index, onOpen, favorite, onFavorite }: { program: Program; index: number; onOpen: () => void; favorite: boolean; onFavorite: () => void }) {
  return <motion.article className="program-card" initial={{ opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .28, delay: Math.min(index, 7) * .025 }}>
    <button className="program-main" type="button" onClick={onOpen} aria-label={`${program.university} ${program.department} detaylarını aç`}>
      <div className="program-card-top"><span className="program-type">{program.scoreType}</span><span className="program-city"><MapPin size={14} /> {program.city}</span></div>
      <div className="program-university">{program.university}</div>
      <h3>{program.department}</h3>
      <div className="program-stats"><div><span>TABAN PUAN</span><strong>{scoreFormat(program.minScore)}</strong></div><div><span>BAŞARI SIRASI</span><strong>{numberFormat(program.rank)}</strong></div><div><span>KONTENJAN</span><strong>{numberFormat(program.quota)}</strong></div></div>
    </button>
    <div className="program-card-bottom"><span>Program detaylarını incele <ArrowRight size={15} /></span><IconButton label={favorite ? 'Favorilerden çıkar' : 'Favorilere ekle'} className={`favorite-button ${favorite ? 'is-favorite' : ''}`} onClick={onFavorite}><Heart size={18} fill={favorite ? 'currentColor' : 'none'} /></IconButton></div>
  </motion.article>;
}

function FilterPanel({ filters, setFilters, cities, clear, mobileOpen, close }: { filters: Filters; setFilters: (value: Filters) => void; cities: string[]; clear: () => void; mobileOpen: boolean; close: () => void }) {
  const set = (key: keyof Filters, value: string) => setFilters({ ...filters, [key]: value });
  return <aside className={`filter-panel ${mobileOpen ? 'mobile-open' : ''}`}>
    <div className="filter-heading"><div><SlidersHorizontal size={19} /><strong>Filtreler</strong></div><button type="button" onClick={clear}>Temizle</button><IconButton label="Filtreleri kapat" className="mobile-filter-close" onClick={close}><X size={19} /></IconButton></div>
    <div className="filter-group"><label htmlFor="city-filter">Şehir</label><div className="select-wrap"><select id="city-filter" value={filters.city} onChange={(e) => set('city', e.target.value)}><option value="">Tüm şehirler</option>{cities.map((city) => <option key={city}>{city}</option>)}</select><ChevronDown size={16} /></div></div>
    <div className="filter-group"><span className="filter-label">Puan türü</span><div className="type-options">{['', 'SAY', 'EA', 'SÖZ'].map((type) => <button type="button" key={type} className={filters.scoreType === type ? 'active' : ''} onClick={() => set('scoreType', type)}>{type || 'Tümü'}</button>)}</div></div>
    <div className="filter-group"><span className="filter-label">Taban puan aralığı</span><div className="range-row"><input type="number" min="0" max="600" step="1" aria-label="En düşük taban puan" placeholder="Min" value={filters.minScore} onChange={(e) => set('minScore', e.target.value)} /><span>—</span><input type="number" min="0" max="600" step="1" aria-label="En yüksek taban puan" placeholder="Maks" value={filters.maxScore} onChange={(e) => set('maxScore', e.target.value)} /></div></div>
    <div className="filter-group"><span className="filter-label">Başarı sırası aralığı</span><div className="range-row"><input type="number" min="0" step="1000" aria-label="En iyi başarı sırası" placeholder="Min" value={filters.minRank} onChange={(e) => set('minRank', e.target.value)} /><span>—</span><input type="number" min="0" step="1000" aria-label="En yüksek başarı sırası" placeholder="Maks" value={filters.maxRank} onChange={(e) => set('maxRank', e.target.value)} /></div></div>
    <div className="filter-note"><Zap size={17} /><span>Filtreler anında uygulanır. Daha hızlı keşfet, daha iyi karar ver.</span></div>
  </aside>;
}

function Detail({ program, close, favorite, toggleFavorite }: { program: Program; close: () => void; favorite: boolean; toggleFavorite: () => void }) {
  return <motion.div className="modal-backdrop" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onMouseDown={close}>
    <motion.section className="detail-panel" role="dialog" aria-modal="true" aria-label="Program detayları" initial={{ x: 48, opacity: 0 }} animate={{ x: 0, opacity: 1 }} exit={{ x: 32, opacity: 0 }} transition={{ type: 'spring', stiffness: 300, damping: 30 }} onMouseDown={(event) => event.stopPropagation()}>
      <div className="detail-top"><span className="eyebrow">PROGRAM KARTI / {program.scoreType}</span><IconButton label="Detayı kapat" onClick={close}><X size={20} /></IconButton></div>
      <div className="detail-emblem"><GraduationCap size={30} /></div>
      <span className="detail-city"><MapPin size={16} />{program.city}</span>
      <h2>{program.department}</h2><p className="detail-university">{program.university}</p>
      <div className="detail-data"><div className="detail-primary"><span>TABAN PUAN</span><strong>{scoreFormat(program.minScore)}</strong></div><div className="detail-primary"><span>BAŞARI SIRASI</span><strong>{numberFormat(program.rank)}</strong></div></div>
      <div className="detail-table"><div><span>Tavan puan</span><strong>{scoreFormat(program.maxScore)}</strong></div><div><span>Kontenjan</span><strong>{numberFormat(program.quota)}</strong></div><div><span>Yerleşen</span><strong>{numberFormat(program.placed)}</strong></div><div><span>Puan türü</span><strong>{program.scoreType}</strong></div><div><span>Şehir</span><strong>{program.city}</strong></div></div>
      <button className={`detail-favorite ${favorite ? 'active' : ''}`} type="button" onClick={toggleFavorite}><Heart size={18} fill={favorite ? 'currentColor' : 'none'} />{favorite ? 'Favorilerden çıkar' : 'Favorilere ekle'}</button>
      <p className="detail-source">Bilgiler uygulamayla gelen yerel CSV dosyasından gösterilir.</p>
    </motion.section>
  </motion.div>;
}

export function App() {
  const [programs, setPrograms] = useState<Program[]>([]);
  const [error, setError] = useState('');
  const [skipped, setSkipped] = useState(0);
  const [theme, setTheme] = useStored<Theme>('uniara-theme', 'dark');
  const [motionChoice, setMotionChoice] = useStored<MotionChoice>('uniara-motion', 'system');
  const [favorites, setFavorites] = useStored<string[]>('uniara-favorites', []);
  const [recent, setRecent] = useStored<string[]>('uniara-recent', []);
  const [view, setView] = useState<View>('home');
  const [query, setQuery] = useState('');
  const [filters, setFilters] = useState<Filters>(emptyFilters);
  const [sort, setSort] = useState<SortKey>('score-desc');
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Program | null>(null);
  const [mobileFilters, setMobileFilters] = useState(false);
  const homeInput = useRef<HTMLInputElement>(null);
  const resultInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        const csv = window.desktop ? await window.desktop.readCsv() : csvFallback;
        const parsed = parsePrograms(csv);
        if (!parsed.programs.length) throw new Error('CSV dosyasında okunabilir program bulunamadı.');
        if (active) { setPrograms(parsed.programs); setSkipped(parsed.skipped); }
      } catch (cause) { if (active) setError(cause instanceof Error ? cause.message : 'Veri okunamadı.'); }
    };
    load();
    return () => { active = false; };
  }, []);

  const cities = useMemo(() => [...new Set(programs.map((p) => p.city))].sort((a, b) => a.localeCompare(b, 'tr-TR')), [programs]);
  const universityCount = useMemo(() => new Set(programs.map((p) => p.university)).size, [programs]);
  const scoreTypes = useMemo(() => [...new Set(programs.map((p) => p.scoreType))], [programs]);
  const filtered = useMemo(() => filterPrograms(view === 'favorites' ? programs.filter((p) => favorites.includes(p.id)) : programs, query, filters, sort), [programs, favorites, view, query, filters, sort]);
  const visible = filtered.slice(0, page * 24);
  const activeFilterCount = Object.values(filters).filter(Boolean).length;
  const motionMode = motionChoice === 'system' ? 'user' : motionChoice === 'reduced' ? 'always' : 'never';

  useEffect(() => { setPage(1); }, [query, filters, sort, view]);
  useEffect(() => {
    const handler = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') { event.preventDefault(); (view === 'home' ? homeInput : resultInput).current?.focus(); }
      else if (event.key === '/' && !['INPUT', 'TEXTAREA', 'SELECT'].includes((event.target as HTMLElement).tagName)) { event.preventDefault(); (view === 'home' ? homeInput : resultInput).current?.focus(); }
      else if (event.key === 'Escape') { setSelected(null); setMobileFilters(false); }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [view]);
  useEffect(() => {
    document.body.style.overflow = selected || mobileFilters ? 'hidden' : '';
    return () => { document.body.style.overflow = ''; };
  }, [selected, mobileFilters]);

  const goToView = (nextView: View) => {
    setView(nextView);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const submit = (value = query) => {
    const clean = value.trim();
    setQuery(clean);
    if (clean) setRecent((items) => [clean, ...items.filter((item) => item !== clean)].slice(0, 5));
    setView('results');
    setTimeout(() => window.scrollTo({ top: 0, behavior: 'smooth' }), 0);
  };
  const toggleFavorite = (id: string) => setFavorites((items) => items.includes(id) ? items.filter((item) => item !== id) : [...items, id]);
  const openCategory = (type: 'programs' | 'universities' | 'cities') => {
    setFilters(emptyFilters);
    setQuery(''); goToView('results');
    if (type === 'cities') window.setTimeout(() => document.getElementById('city-filter')?.focus(), 50);
  };

  return <MotionConfig reducedMotion={motionMode}>
    <div className="app" data-theme={theme} data-motion={motionChoice}>
      <WindowBar theme={theme} />
      <header className="app-header">
        <button type="button" className="header-logo" onClick={() => { goToView('home'); setQuery(''); setFilters(emptyFilters); }}><span className="header-logo-mark">Ü</span><span>ÜNİ<span>.</span>ARA</span></button>
        <nav aria-label="Ana gezinme"><button type="button" className={view === 'home' ? 'active' : ''} onClick={() => goToView('home')}>Keşfet</button><button type="button" className={view === 'results' ? 'active' : ''} onClick={() => goToView('results')}>Programlar</button><button type="button" className={view === 'favorites' ? 'active' : ''} onClick={() => goToView('favorites')}>Favoriler {favorites.length > 0 && <span>{favorites.length}</span>}</button></nav>
        <div className="header-actions"><span className="offline-badge"><span /> ÇEVRİMDIŞI HAZIR</span><IconButton label={theme === 'dark' ? 'Açık temaya geç' : 'Koyu temaya geç'} onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>{theme === 'dark' ? <Sun size={19} /> : <Moon size={19} />}</IconButton><button className="motion-toggle" type="button" title="Animasyon tercihi" onClick={() => setMotionChoice(motionChoice === 'system' ? 'reduced' : motionChoice === 'reduced' ? 'full' : 'system')}><Zap size={16} /> {motionChoice === 'system' ? 'Sistem' : motionChoice === 'reduced' ? 'Az hareket' : 'Tam hareket'}</button></div>
      </header>

      <main>
        {view === 'home' && <section className="hero">
          <div className="hero-glow hero-glow-one" /><div className="hero-glow hero-glow-two" /><div className="hero-grid" />
          <div className="hero-inner">
            <motion.div className="hero-copy" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: .55 }}>
              <div className="eyebrow hero-eyebrow"><span className="eyebrow-line" /> ÜNİVERSİTE KEŞFİNİN YENİ HALİ <Sparkles size={15} /></div>
              <h1>Geleceğini<br /><em>bulmaya</em> başla<span className="hero-period">.</span></h1>
              <p>Binlerce program, tek bir arama. Üniversiteleri keşfet, seçeneklerini karşılaştır, sana uyan yolu bul.</p>
              <SearchField value={query} onChange={setQuery} onSubmit={submit} programs={programs} inputRef={homeInput} />
              <div className="hero-search-foot"><span><Command size={14} /> Kısayol: Ctrl / ⌘ + K</span><span>Üniversite · Bölüm · Şehir</span></div>
              {recent.length > 0 && <div className="recent-row"><span>SON ARAMALAR</span>{recent.slice(0, 3).map((item) => <button key={item} type="button" onClick={() => submit(item)}>{item}<ArrowRight size={13} /></button>)}</div>}
            </motion.div>
            <motion.div className="hero-visual" initial={{ opacity: 0, scale: .9, rotate: -5 }} animate={{ opacity: 1, scale: 1, rotate: 0 }} transition={{ duration: .75, delay: .12 }} aria-hidden="true">
              <div className="orbit orbit-outer" /><div className="orbit orbit-middle" /><div className="orbit orbit-inner" />
              <div className="orbit-center"><GraduationCap size={55} strokeWidth={1.3} /><span>KEŞFET<br />KARŞILAŞTIR<br />KARAR VER</span></div>
              <div className="orbit-tag orbit-tag-one"><span>01</span> ARA</div><div className="orbit-tag orbit-tag-two"><span>02</span> FİLTRELE</div><div className="orbit-tag orbit-tag-three"><span>03</span> KEŞFET</div>
              <span className="orbit-star star-one">✦</span><span className="orbit-star star-two">✦</span>
            </motion.div>
          </div>
          <div className="hero-bottom"><span>VERİDEN KARARA, TEK EKRANDA.</span><span>SCROLL TO EXPLORE <ArrowDownWideNarrow size={16} /></span></div>
        </section>}

        {view === 'home' && <section className="dashboard-section"><div className="section-heading"><div><span className="section-kicker">RAKAMLARLA ÜNİ-ARA</span><h2>Keşfedilecek çok şey var<span>.</span></h2></div><p>İlk adımı at. Her kart seni bir sonraki keşfe götürür.</p></div><div className="kpi-grid">
          <KpiCard icon={<Compass size={27} />} value={numberFormat(programs.length)} label="Program" caption="Tüm programları keşfet" onClick={() => openCategory('programs')} index={0} />
          <KpiCard icon={<GraduationCap size={27} />} value={numberFormat(universityCount)} label="Üniversite" caption="Farklı seçenekleri incele" onClick={() => openCategory('universities')} index={1} />
          <KpiCard icon={<MapPin size={27} />} value={numberFormat(cities.length)} label="Şehir" caption="Yeni bir şehir seç" onClick={() => openCategory('cities')} index={2} />
          <KpiCard icon={<Zap size={27} />} value={numberFormat(scoreTypes.length)} label="Puan türü" caption="Sana uygun alanı bul" onClick={() => { setQuery(''); setFilters({ ...emptyFilters, scoreType: scoreTypes[0] || '' }); goToView('results'); }} index={3} />
        </div><div className="dashboard-cta"><span><Sparkles size={17} /> KEŞİF MODU</span><p>Bir arama her şeyi değiştirebilir.</p><button type="button" onClick={() => { goToView('results'); setQuery(''); }}>Tüm programları gör <ArrowRight size={18} /></button></div></section>}

        {view !== 'home' && <section className="explore-page"><div className="explore-heading"><div className="explore-heading-copy"><button className="back-link" type="button" onClick={() => setView('home')}><ArrowLeft size={17} /> Ana sayfa</button><span className="section-kicker">{view === 'favorites' ? 'KİŞİSEL LİSTEN' : 'KEŞİF ALANI'}</span><h1>{view === 'favorites' ? 'Favorilerin' : 'Programları keşfet'}<span>.</span></h1><p>{view === 'favorites' ? 'Kaydettiğin programlar, karar vermen için burada.' : 'Aradığın programa daha hızlı ulaşmak için filtrele ve karşılaştır.'}</p></div><div className="explore-heading-art"><span>Ü</span><div className="art-ring" /></div></div>
          <div className="explore-toolbar"><SearchField value={query} onChange={setQuery} onSubmit={submit} programs={programs} inputRef={resultInput} compact /><button type="button" className="mobile-filter-button" onClick={() => setMobileFilters(true)}><SlidersHorizontal size={18} /> Filtreler {activeFilterCount > 0 && `(${activeFilterCount})`}</button><span className="toolbar-divider" /><div className="sort-control"><ArrowDownWideNarrow size={17} /><select aria-label="Sıralama" value={sort} onChange={(e) => setSort(e.target.value as SortKey)}>{Object.entries(sortLabels).map(([key, label]) => <option value={key} key={key}>{label}</option>)}</select><ChevronDown size={15} /></div></div>
          <div className="explore-layout"><FilterPanel filters={filters} setFilters={setFilters} cities={cities} clear={() => setFilters(emptyFilters)} mobileOpen={mobileFilters} close={() => setMobileFilters(false)} /><div className="results-area"><div className="results-meta"><div><span className="results-dot" /><strong>{numberFormat(filtered.length)}</strong> program bulundu {skipped > 0 && <span className="skipped-note">· {skipped} satır okunamadı</span>}</div><span>YEREL VERİ · {numberFormat(programs.length)} KAYIT</span></div>
              {activeFilterCount > 0 && <div className="filter-chips">{Object.entries(filters).filter(([, value]) => value).map(([key, value]) => <button type="button" key={key} onClick={() => setFilters({ ...filters, [key]: '' })}>{({ city: 'Şehir', scoreType: 'Puan', minScore: 'Min puan', maxScore: 'Maks puan', minRank: 'Min sıra', maxRank: 'Maks sıra' } as Record<string, string>)[key]}: {value} <X size={13} /></button>)}<button type="button" className="clear-all" onClick={() => setFilters(emptyFilters)}>Tümünü temizle</button></div>}
              {error ? <div className="empty-state"><X size={35} /><h2>Veri okunamadı</h2><p>{error}</p></div> : !programs.length ? <div className="empty-state"><span className="loading-orbit" /><h2>Programlar yükleniyor</h2></div> : filtered.length === 0 ? <div className="empty-state"><Search size={34} /><h2>{view === 'favorites' && !favorites.length ? 'Henüz favorin yok' : 'Sonuç bulunamadı'}</h2><p>{view === 'favorites' && !favorites.length ? 'Beğendiğin programların kalp simgesine dokunarak onları burada toplayabilirsin.' : 'Arama kelimelerini veya filtreleri değiştirmeyi dene.'}</p><button type="button" onClick={() => { setQuery(''); setFilters(emptyFilters); }}>Aramayı temizle <ArrowRight size={16} /></button></div> : <><div className="program-grid">{visible.map((program, index) => <ProgramCard key={program.id} program={program} index={index} favorite={favorites.includes(program.id)} onFavorite={() => toggleFavorite(program.id)} onOpen={() => setSelected(program)} />)}</div>{visible.length < filtered.length && <div className="load-more"><span>{numberFormat(visible.length)} / {numberFormat(filtered.length)} program gösteriliyor</span><button type="button" onClick={() => setPage(page + 1)}>Daha fazla göster <ArrowRight size={17} /></button></div>}</>}
            </div></div>
        </section>}
      </main>
      <footer className="app-footer"><span>ÜNİ<span>.</span>ARA <small>© 2026</small></span><span>Keşfet. Karşılaştır. Karar ver.</span><span><span className="footer-indicator" /> Çevrimdışı çalışır</span></footer>
      <AnimatePresence>{selected && <Detail program={selected} close={() => setSelected(null)} favorite={favorites.includes(selected.id)} toggleFavorite={() => toggleFavorite(selected.id)} />}</AnimatePresence>
      {mobileFilters && <button type="button" className="mobile-filter-backdrop" aria-label="Filtreleri kapat" onClick={() => setMobileFilters(false)} />}
    </div>
  </MotionConfig>;
}
