import Papa from 'papaparse';

export type Program = {
  id: string;
  university: string;
  department: string;
  city: string;
  scoreType: string;
  minScore: number;
  maxScore: number;
  quota: number;
  placed: number;
  rank: number;
};

export type SortKey = 'score-desc' | 'score-asc' | 'rank-asc' | 'rank-desc' | 'university' | 'department';
export type Filters = { city: string; scoreType: string; minScore: string; maxScore: string; minRank: string; maxRank: string };

type CsvRow = Record<string, string>;
export const emptyFilters: Filters = { city: '', scoreType: '', minScore: '', maxScore: '', minRank: '', maxRank: '' };

export function normalize(value: string): string {
  return value.trim().toLocaleLowerCase('tr-TR').normalize('NFD').replace(/[\u0300-\u036f]/g, '');
}

export function parsePrograms(csv: string): { programs: Program[]; skipped: number } {
  const parsed = Papa.parse<CsvRow>(csv.replace(/^\uFEFF/, ''), { header: true, skipEmptyLines: true });
  const programs: Program[] = [];
  let skipped = 0;
  const ids = new Map<string, number>();
  for (const row of parsed.data) {
    const university = row.Universite?.trim();
    const department = row.Bolum?.trim();
    const city = row.Sehir?.trim();
    const minScore = Number(row['Taban Puan']);
    const maxScore = Number(row['Tavan Puan']);
    const quota = Number(row.Kontenjan);
    const placed = Number(row.Yerlesen);
    const rank = Number(row['Basari Sirasi']);
    if (!university || !department || !city || !Number.isFinite(minScore) || !Number.isFinite(maxScore) || !Number.isFinite(quota) || !Number.isFinite(placed) || !Number.isFinite(rank)) {
      skipped++;
      continue;
    }
    const baseId = `${university}|${department}|${city}|${row['Puan Turu'] || ''}`;
    const occurrence = ids.get(baseId) || 0;
    ids.set(baseId, occurrence + 1);
    programs.push({
      id: `${baseId}|${occurrence}`,
      university,
      department,
      city,
      scoreType: row['Puan Turu']?.trim() || '—',
      minScore,
      maxScore,
      quota,
      placed,
      rank,
    });
  }
  return { programs, skipped };
}

export function filterPrograms(programs: Program[], query: string, filters: Filters, sort: SortKey): Program[] {
  const words = normalize(query).split(/\s+/).filter(Boolean);
  const minScore = Number(filters.minScore || 0);
  const maxScore = Number(filters.maxScore || Infinity);
  const minRank = Number(filters.minRank || 0);
  const maxRank = Number(filters.maxRank || Infinity);
  const output = programs.filter((program) => {
    const haystack = normalize(`${program.university} ${program.department} ${program.city}`);
    return words.every((word) => haystack.includes(word))
      && (!filters.city || program.city === filters.city)
      && (!filters.scoreType || program.scoreType === filters.scoreType)
      && program.minScore >= minScore && program.minScore <= maxScore
      && program.rank >= minRank && program.rank <= maxRank;
  });
  const tr = new Intl.Collator('tr-TR');
  output.sort((a, b) => {
    switch (sort) {
      case 'score-asc': return a.minScore - b.minScore;
      case 'rank-asc': return a.rank - b.rank;
      case 'rank-desc': return b.rank - a.rank;
      case 'university': return tr.compare(a.university, b.university);
      case 'department': return tr.compare(a.department, b.department);
      default: return b.minScore - a.minScore;
    }
  });
  return output;
}

export type Suggestion = { label: string; kind: 'Üniversite' | 'Bölüm' | 'Şehir' };

export function getSuggestions(programs: Program[], query: string): Suggestion[] {
  const q = normalize(query);
  if (!q) return [];
  const values = new Map<string, Suggestion>();
  for (const p of programs) {
    for (const [label, kind] of [[p.university, 'Üniversite'], [p.department, 'Bölüm'], [p.city, 'Şehir']] as const) {
      if (normalize(label).includes(q) && !values.has(`${kind}:${label}`)) values.set(`${kind}:${label}`, { label, kind });
    }
  }
  return [...values.values()].sort((a, b) => {
    const aStarts = normalize(a.label).startsWith(q) ? 0 : 1;
    const bStarts = normalize(b.label).startsWith(q) ? 0 : 1;
    return aStarts - bStarts || a.label.localeCompare(b.label, 'tr-TR');
  }).slice(0, 7);
}

export const scoreFormat = (value: number) => value.toLocaleString('tr-TR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
export const numberFormat = (value: number) => value.toLocaleString('tr-TR');
