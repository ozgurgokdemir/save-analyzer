import { analyzeSekiroSave } from '@save-analyzer/analyzer';
import type { AnyRecord } from '@save-analyzer/shared';
import {
  Anvil,
  Award,
  BookOpenCheck,
  FileCheck2,
  Gauge,
  KeyRound,
  LoaderCircle,
  RotateCcw,
  ShieldAlert,
  Sparkles,
  Sword,
  UploadCloud,
  Wrench,
  XCircle,
  type LucideIcon,
} from 'lucide-react';
import { useId, useMemo, useRef, useState } from 'react';

import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button, buttonVariants } from '@/components/ui/button';
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { sekiroStaticData } from '@/data/sekiro';
import { cn } from '@/lib/utils';

type AnalyzerState = 'idle' | 'analyzing' | 'complete' | 'error';

interface CategoryDefinition {
  key: string;
  label: string;
  description: string;
  icon: LucideIcon;
  conservative?: boolean;
}

const categories: CategoryDefinition[] = [
  {
    key: 'gourdSeeds',
    label: 'Gourd Seeds',
    description: 'Pickup and merchant locations',
    icon: Gauge,
  },
  {
    key: 'prayerBeads',
    label: 'Prayer Beads',
    description: 'Locations reconciled to inventory totals',
    icon: Award,
  },
  {
    key: 'prosthetics',
    label: 'Prosthetic Tools',
    description: 'Base Prosthetic Tool ownership',
    icon: Wrench,
  },
  {
    key: 'prostheticUpgrades',
    label: 'Prosthetic Upgrades',
    description: 'Mapped upgrade unlocks',
    icon: Anvil,
  },
  {
    key: 'skills',
    label: 'Skills',
    description: 'Combat arts, passives, and martial arts',
    icon: Sparkles,
  },
  {
    key: 'keyItems',
    label: 'Key Items',
    description: 'Progression and route inventory',
    icon: KeyRound,
  },
  {
    key: 'endings',
    label: 'Endings',
    description: 'Route completion and availability',
    icon: BookOpenCheck,
  },
  {
    key: 'bosses',
    label: 'Bosses',
    description: 'Conservative boss-state evidence',
    icon: Sword,
    conservative: true,
  },
];

const issueStatuses = new Set([
  'missing',
  'incomplete',
  'unknown',
  'blocked',
  'not_defeated',
]);
const completeStatuses = new Set([
  'collected',
  'unlocked',
  'completed',
  'defeated',
]);

function normalized(value: unknown): string {
  return typeof value === 'string' ? value.toLowerCase() : 'unknown';
}

function titleCase(value: unknown): string {
  return String(value ?? 'unknown')
    .replace(/([a-z\d])([A-Z])/g, '$1 $2')
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function priority(entity: AnyRecord): number {
  const status = normalized(entity.status);
  if (status === 'missing' || status === 'incomplete' || status === 'blocked')
    return 0;
  if (status === 'unknown' || status === 'not_defeated') return 1;
  if (status === 'available') return 2;
  return 3;
}

function statusBadge(statusValue: unknown) {
  const status = normalized(statusValue);
  if (
    status === 'missing' ||
    status === 'blocked' ||
    status === 'not_defeated'
  ) {
    return (
      <Badge className="bg-red-50 text-red-700 dark:bg-red-950/50 dark:text-red-300">
        {titleCase(status)}
      </Badge>
    );
  }
  if (status === 'unknown' || status === 'incomplete') {
    return (
      <Badge className="bg-amber-50 text-amber-700 dark:bg-amber-950/50 dark:text-amber-300">
        {titleCase(status)}
      </Badge>
    );
  }
  if (completeStatuses.has(status)) {
    return (
      <Badge className="bg-emerald-50 text-emerald-700 dark:bg-emerald-950/50 dark:text-emerald-300">
        {titleCase(status)}
      </Badge>
    );
  }
  return (
    <Badge className="bg-slate-50 text-slate-700 dark:bg-slate-900/50 dark:text-slate-300">
      {titleCase(status)}
    </Badge>
  );
}

function primitiveText(value: unknown): string | null {
  if (typeof value === 'string' && value.trim()) return value;
  if (typeof value === 'number' || typeof value === 'boolean')
    return String(value);
  if (Array.isArray(value)) {
    const values = value.filter((item) =>
      ['string', 'number', 'boolean'].includes(typeof item),
    );
    return values.length ? values.join(', ') : null;
  }
  return null;
}

function metadataRows(metadata: unknown): Array<[string, string]> {
  if (!metadata || typeof metadata !== 'object' || Array.isArray(metadata))
    return [];
  const ignored = new Set([
    'sourceReferences',
    'notes',
    'ownershipInferencePolicy',
    'confidence',
    'sourceType',
    'shopLineupParamRowId',
    'itemLotParamRowId',
  ]);
  return Object.entries(metadata as AnyRecord)
    .filter(
      ([key]) =>
        !ignored.has(key) &&
        !/(?:param|confidence|rowId|itemId|eventFlag)/i.test(key),
    )
    .map(([key, value]) => [titleCase(key), primitiveText(value)] as const)
    .filter((row): row is [string, string] => row[1] !== null)
    .slice(0, 10);
}

function noteEntries(entity: AnyRecord): string[] {
  const isPublicNote = (note: unknown): note is string =>
    typeof note === 'string' &&
    note.trim().length > 0 &&
    !/(?:\bflag\b|itemlotparam|shoplineupparam|equipparam|skillparam|inventory_weapon|inventory-derived|mapping row|row id|sha-256)/i.test(
      note,
    );
  const notes = Array.isArray(entity.notes)
    ? entity.notes.filter(isPublicNote)
    : [];
  if (
    isPublicNote(entity.statusDetails) &&
    !notes.includes(entity.statusDetails)
  ) {
    return [entity.statusDetails, ...notes];
  }
  return notes;
}

function entitySubtitle(entity: AnyRecord): string {
  const acquisition = (entity.acquisitionMetadata ??
    entity.sourceLocation ??
    {}) as AnyRecord;
  return [
    ...new Set(
      [
        entity.area ?? acquisition.area,
        entity.location ?? acquisition.location,
        entity.skillTree ?? acquisition.skillTree,
        entity.baseToolName,
      ].filter(
        (value): value is string =>
          typeof value === 'string' && value.trim().length > 0,
      ),
    ),
  ].join(' · ');
}

function EntityDetails({ entity }: { entity: AnyRecord }) {
  const acquisition = metadataRows(entity.acquisitionMetadata);
  const notes = noteEntries(entity);

  return (
    <div className="space-y-5 border-t pt-4">
      {acquisition.length > 0 && (
        <section aria-label="Acquisition metadata">
          <dl className="grid gap-x-6 gap-y-3 sm:grid-cols-2">
            {acquisition.map(([label, value]) => (
              <div key={`${label}-${value}`} className="flex flex-col gap-0.5">
                <dt className="text-xs text-muted-foreground">{label}</dt>
                <dd className="leading-6 text-foreground">{value}</dd>
              </div>
            ))}
          </dl>
        </section>
      )}

      {notes.length > 0 && (
        <section aria-label="Notes">
          <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Notes
          </h4>
          <ul className="mt-3 list-disc space-y-1 ps-5 text-muted-foreground">
            {notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </section>
      )}

      {acquisition.length === 0 && notes.length === 0 && (
        <p className="text-muted-foreground">
          No additional acquisition details are available for this entry.
        </p>
      )}
    </div>
  );
}

function CategoryCard({
  definition,
  category,
}: {
  definition: CategoryDefinition;
  category: AnyRecord;
}) {
  const Icon = definition.icon;
  const summary = (category.summary ?? {}) as AnyRecord;
  const statuses = (summary.byStatus ?? {}) as AnyRecord;
  const entities = useMemo(
    () =>
      [...(Array.isArray(category.entities) ? category.entities : [])].sort(
        (a, b) =>
          priority(a) - priority(b) ||
          String(a.name ?? a.id).localeCompare(String(b.name ?? b.id)),
      ),
    [category.entities],
  );
  const total = Number(summary.total ?? entities.length ?? 0);
  const complete = Object.entries(statuses).reduce(
    (count, [status, value]) =>
      count + (completeStatuses.has(normalized(status)) ? Number(value) : 0),
    0,
  );
  const percentage = total > 0 ? Math.round((complete / total) * 100) : 0;

  return (
    <Card id={definition.key}>
      <CardHeader className="border-b has-data-[slot=card-description]:grid-rows-[auto] gap-y-4">
        <div className="flex items-start gap-3">
          <div className="grid size-10 shrink-0 place-items-center rounded-xl bg-primary/10 text-primary">
            <Icon className="size-5" aria-hidden="true" />
          </div>
          <div>
            <CardTitle>{definition.label}</CardTitle>
            <CardDescription>{definition.description}</CardDescription>
          </div>
        </div>
        <CardAction className="row-span-1">
          <span className="text-sm font-medium tabular-nums">
            {complete} / {total}
          </span>
        </CardAction>
        <div className="col-span-full">
          <Progress
            value={percentage}
            aria-label={`${definition.label}: ${percentage}% complete`}
          />
        </div>
        <div className="col-span-full flex flex-wrap gap-2">
          {Object.entries(statuses).map(([status, count]) => (
            <span
              key={status}
              className={cn(
                'inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium',
                issueStatuses.has(normalized(status)) && Number(count) > 0
                  ? 'bg-primary/5'
                  : 'bg-muted/30',
              )}
            >
              <strong className="tabular-nums">{String(count)}</strong>{' '}
              {titleCase(status)}
            </span>
          ))}
        </div>
      </CardHeader>
      <CardContent>
        {definition.conservative && (
          <Alert className="mb-4 border-amber-500/25 bg-amber-500/5">
            <ShieldAlert className="text-amber-700 dark:text-amber-300" />
            <AlertTitle>Conservative detection</AlertTitle>
            <AlertDescription>
              Boss evidence is not promoted to a definite result unless it has
              reliable persistent semantics. Unknown is expected.
            </AlertDescription>
          </Alert>
        )}
        {entities.length > 0 ? (
          <Accordion multiple>
            {entities.map((entity: AnyRecord) => (
              <AccordionItem
                key={String(entity.id ?? entity.name)}
                value={String(entity.id ?? entity.name)}
                className="data-open:bg-transparent"
              >
                <AccordionTrigger>
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-medium">
                        {String(entity.name ?? titleCase(entity.id))}
                      </span>
                      {statusBadge(entity.status)}
                    </div>
                    {entitySubtitle(entity) && (
                      <p className="mt-1 truncate text-xs font-normal text-muted-foreground">
                        {entitySubtitle(entity)}
                      </p>
                    )}
                  </div>
                </AccordionTrigger>
                <AccordionContent>
                  <EntityDetails entity={entity} />
                </AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        ) : (
          <p className="rounded-lg border border-dashed p-4 text-muted-foreground">
            No normalized entries were returned for this category.
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function getFriendlyError(error: unknown): string {
  const message = error instanceof Error ? error.message : String(error);
  if (/BND4|magic|container|entry|USER_DATA/i.test(message)) {
    return 'This file does not appear to be a supported Sekiro save container. Make sure you selected the original .sl2 file.';
  }
  if (/crypto|digest|SHA-256/i.test(message)) {
    return 'This browser cannot provide the secure local hashing feature required by the analyzer. Try a current browser over HTTPS.';
  }
  return `The save could not be analyzed: ${message}`;
}

export default function Analyzer() {
  const inputId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const [state, setState] = useState<AnalyzerState>('idle');
  const [dragActive, setDragActive] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<AnyRecord | null>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [activeCategory, setActiveCategory] = useState(categories[0].key);

  async function analyzeFile(file: File) {
    setError(null);
    setReport(null);
    setFileName(file.name);
    setActiveCategory(categories[0].key);

    if (!file.name.toLowerCase().endsWith('.sl2')) {
      setState('error');
      setError('Choose a Sekiro save file with the .sl2 extension.');
      return;
    }
    if (file.size === 0) {
      setState('error');
      setError(
        'That file is empty. Choose the original Sekiro .sl2 save file.',
      );
      return;
    }

    setState('analyzing');
    try {
      await new Promise<void>((resolve) =>
        requestAnimationFrame(() => resolve()),
      );
      const buffer = await file.arrayBuffer();
      const nextReport = await analyzeSekiroSave(buffer, sekiroStaticData, {
        fileName: file.name,
      });
      setReport(nextReport);
      setState('complete');
    } catch (nextError) {
      setError(getFriendlyError(nextError));
      setState('error');
    } finally {
      if (inputRef.current) inputRef.current.value = '';
    }
  }

  function reset() {
    setState('idle');
    setError(null);
    setReport(null);
    setFileName(null);
    if (inputRef.current) inputRef.current.value = '';
  }

  const shape = report?.parseSekiroSaveShape as AnyRecord | undefined;
  const activeDefinition =
    categories.find((definition) => definition.key === activeCategory) ??
    categories[0];
  const issueCount = shape
    ? categories.reduce((sum, definition) => {
        const statuses = shape[definition.key]?.summary?.byStatus ?? {};
        return (
          sum +
          Object.entries(statuses).reduce(
            (inner, [status, count]) =>
              inner +
              (issueStatuses.has(normalized(status)) ? Number(count) : 0),
            0,
          )
        );
      }, 0)
    : 0;

  if (state === 'complete' && report && shape) {
    return (
      <div className="space-y-4" aria-live="polite">
        <Card>
          <CardHeader className="border-b has-data-[slot=card-description]:grid-rows-[auto]">
            <div className="flex items-start gap-3">
              <div className="grid size-10 place-items-center rounded-xl bg-primary/10">
                <FileCheck2
                  className="size-5 text-primary"
                  aria-hidden="true"
                />
              </div>
              <div>
                <CardTitle>Analysis complete</CardTitle>
                <CardDescription>
                  {fileName} · slot {String(report.active_slot ?? 'unknown')}
                </CardDescription>
              </div>
            </div>
            <CardAction className="row-span-1">
              <Badge>{issueCount} items to review</Badge>
            </CardAction>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-[1fr_auto] sm:items-end">
            <div>
              <p className="text-xs uppercase tracking-wider text-muted-foreground">
                Local SHA-256
              </p>
              <p className="mt-1 break-all font-mono text-xs text-muted-foreground">
                {String(report.sha256)}
              </p>
            </div>
            <Button variant="outline" onClick={reset}>
              <RotateCcw data-icon="inline-start" />
              Analyze another file
            </Button>
          </CardContent>
        </Card>

        <div
          className="sticky top-16 z-40 -mx-4 bg-background p-4"
          role="tablist"
          aria-label="Analysis categories"
        >
          <div className="flex gap-2 overflow-x-auto">
            {categories.map((definition, index) => {
              const selected = definition.key === activeCategory;
              return (
                <Button
                  key={definition.key}
                  id={`result-tab-${definition.key}`}
                  role="tab"
                  aria-selected={selected}
                  aria-controls={`result-panel-${definition.key}`}
                  tabIndex={selected ? 0 : -1}
                  variant={selected ? 'default' : 'outline'}
                  size="sm"
                  className="shrink-0"
                  onClick={() => setActiveCategory(definition.key)}
                  onKeyDown={(event) => {
                    if (
                      !['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(
                        event.key,
                      )
                    )
                      return;
                    event.preventDefault();
                    const nextIndex =
                      event.key === 'Home'
                        ? 0
                        : event.key === 'End'
                          ? categories.length - 1
                          : (index +
                              (event.key === 'ArrowRight' ? 1 : -1) +
                              categories.length) %
                            categories.length;
                    const nextKey = categories[nextIndex].key;
                    setActiveCategory(nextKey);
                    requestAnimationFrame(() =>
                      document.getElementById(`result-tab-${nextKey}`)?.focus(),
                    );
                  }}
                >
                  {definition.label}
                </Button>
              );
            })}
          </div>
        </div>

        <div
          id={`result-panel-${activeDefinition.key}`}
          role="tabpanel"
          aria-labelledby={`result-tab-${activeDefinition.key}`}
          tabIndex={0}
        >
          <CategoryCard
            definition={activeDefinition}
            category={shape[activeDefinition.key] ?? {}}
          />
        </div>
      </div>
    );
  }

  return (
    <section>
      <div className="space-y-5">
        <input
          ref={inputRef}
          id={inputId}
          type="file"
          accept=".sl2,application/octet-stream"
          className="sr-only"
          onChange={(event) =>
            event.target.files?.[0] && void analyzeFile(event.target.files[0])
          }
        />
        <label
          htmlFor={inputId}
          tabIndex={state === 'analyzing' ? -1 : 0}
          aria-disabled={state === 'analyzing'}
          onKeyDown={(event) => {
            if (
              (event.key === 'Enter' || event.key === ' ') &&
              state !== 'analyzing'
            ) {
              event.preventDefault();
              inputRef.current?.click();
            }
          }}
          onDragEnter={(event) => {
            event.preventDefault();
            setDragActive(true);
          }}
          onDragOver={(event) => {
            event.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={(event) => {
            event.preventDefault();
            setDragActive(false);
          }}
          onDrop={(event) => {
            event.preventDefault();
            setDragActive(false);
            if (state !== 'analyzing' && event.dataTransfer.files[0])
              void analyzeFile(event.dataTransfer.files[0]);
          }}
          className={cn(
            'group grid min-h-72 cursor-pointer place-items-center rounded-xl border-2 border-dashed p-8 text-center outline-none transition-all focus-visible:border-primary focus-visible:ring-4 focus-visible:ring-primary/15',
            dragActive
              ? 'border-primary bg-primary/5'
              : 'border-border hover:border-primary/50 hover:bg-muted/30',
            state === 'analyzing' && 'pointer-events-none',
          )}
        >
          {state === 'analyzing' ? (
            <div>
              <LoaderCircle
                className="mx-auto size-10 animate-spin text-primary"
                aria-hidden="true"
              />
              <p className="mt-5 text-lg font-medium">Analyzing {fileName}</p>
              <p className="mt-2 text-sm text-muted-foreground">
                Reading the save and evaluating progress locally…
              </p>
            </div>
          ) : (
            <div>
              <div className="mx-auto grid size-14 place-items-center rounded-2xl bg-primary/10 text-primary transition-transform group-hover:-translate-y-1">
                <UploadCloud className="size-7" aria-hidden="true" />
              </div>
              <p className="mt-5 text-lg font-medium">
                Drop your <code>.sl2</code> file here
              </p>
              <p className="mt-2 text-sm text-muted-foreground">
                or use the file picker
              </p>
              <span
                className={cn(buttonVariants({ variant: 'default' }), 'mt-5')}
              >
                Choose save file
              </span>
            </div>
          )}
        </label>

        {state === 'error' && error && (
          <Alert variant="destructive">
            <XCircle />
            <AlertTitle>Could not analyze this file</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
      </div>
    </section>
  );
}
