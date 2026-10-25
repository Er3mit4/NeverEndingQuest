# UI localization (pt-BR)

The React player can render its interface in Brazilian Portuguese. This is a
fork-only addition: the backend, the prompt text and the game content are
unchanged, so the game itself keeps narrating and naming things in English.

## What is translated

- Every static string of the React player (`/play/`): header, log, dice, turn
  status, dialogs, settings, character sheet, inventory, spells, NPCs, map,
  party rail, accessibility labels (`aria-label`, `title`, `placeholder`,
  `alt`).
- Controlled vocabulary that comes from game data but is only *displayed*:
  attributes, skills, conditions, damage types, alignments, sizes, item types
  and subtypes, rarity, spell schools, classes, languages, coins, save modes,
  seasons, moon phases, day cycle, quest status and spell levels.
- Client-generated messages: waiting/turn status, TTS and image errors,
  startup-recovery lines, the four transient connection notices, and the
  fallbacks in the dialogs store.
- Numbers, save dates and the coin labels through `Intl` (`GP/SP/CP` →
  `PO/PP/PC`, `2026-10-25 14:30:00` → `25/10/2026 14:30`).

## What stays in English (by design)

- DM narration, item/spell/NPC/location/module names and descriptions.
- Anything the server sends verbatim: `status_update.message`, `dataErrors`,
  `dataNotices`, `actionResult.message`, compression/update logs, module stage
  names, provider status lines.
- Provider, model, voice and brand names; endpoints; environment variables;
  key formats; CSS classes; socket event names; values compared in state
  (`weapon`, `full`, `name-asc`, `T026`…).

Consequence: the UI is Portuguese but status/error lines that originate in the
backend remain English. That is intentional — translating them would mean
touching the backend, which is out of scope for this fork change.

## How it works

```
web/frontend/src/i18n/
  index.ts            t(), useT(), tn(), v(), useV(), formatNumber(), formatSaveDate()
  pt-BR.ts            aggregates the fragments below
  vocabulary.ts       controlled-vocabulary display map
  fragments/          one file per screen area (common, layout, log, dialogs,
                      settings, sheet, sheetNpcs, party)
web/frontend/src/stores/locale.ts   locale store + persistence + detection
```

The **English string is the key**:

```tsx
const t = useT()
<button>{t('Save Game')}</button>
```

```ts
// fragments/dialogs.ts
export const dialogs = {
  'Save Game': 'Salvar jogo',
} satisfies Record<string, string>
```

Why the English string as the key:

- the diff in a component is only `>Save Game<` → `>{t('Save Game')}<`, which
  keeps future upstream merges mechanical;
- `MessageKey` is `keyof typeof ptBR`, so a component cannot call `t()` for a
  key that has no translation — TypeScript fails the build;
- under `en`, `t()` returns the key, so the English UI is byte-identical to
  upstream and the existing test suite keeps passing unchanged.

### Components and non-React code

- Components call `const t = useT()` once; the hook subscribes to the locale
  store, so switching language re-renders them.
- Event handlers, stores and pure helpers import `{ t }` directly.
- Components that only map data values use `const v = useV()`.

### Locale resolution

1. `localStorage['neq.locale']` when set (Settings → Language);
2. otherwise `navigator.language` starting with `pt` → `pt-BR`;
3. otherwise `en`.

The store also updates `<html lang>` (via `App.tsx`) for screen readers.
No backend request is involved; the choice is per browser.

### Placeholders and plurals

```tsx
t('Total: {total}', { total })
tn('{count} listed spell', '{count} listed spells', count)
```

Missing placeholders are left as `{name}` rather than rendering `undefined`.

### Controlled vocabulary

```tsx
v('ability', 'strength')     // Força
v('itemType', 'weapon')      // arma
v('condition', 'poisoned')   // Envenenado
v('coin', 'GP')              // PO
```

Values are normalized (case, `_`/`-`, extra spaces) and unknown values fall
through unchanged, so homebrew data never breaks. Add a group to
`vocabulary.ts` when a new data-driven label needs translation.

## Adding a string

1. Render `t('The exact English text')` (same words, capitalisation and
   punctuation as the current UI — this is what keeps the English build
   identical).
2. Add `'The exact English text': 'O texto em português'` to the fragment for
   that area.
3. `npx tsc -b` from `web/frontend` — a missing key is a compile error.
4. `npx vitest run src/i18n` — the coverage test also scans `t('…')` literals.

## Tests

- `src/i18n/i18n.test.ts` — no empty translations, every literal key used in
  `src` exists, English passthrough, interpolation, plurals, save-date format,
  vocabulary fallback and a Portuguese wait-status line.
- The existing 400+ component tests run in `en` (jsdom reports `en-US`), so
  they assert the same English strings as before.

## Merge guidance

Upstream changes that touch translated components usually conflict in one of
two trivial ways: a changed English string (update the key and the fragment) or
new JSX (wrap it in `t()` and add the key). Keep the fragments in sync with
`npx vitest run src/i18n`.
