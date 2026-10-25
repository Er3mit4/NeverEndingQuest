/**
 * Controlled-vocabulary display map.
 *
 * Game data keeps its English values (`weapon`, `neutral`, `evocation`); this
 * module translates a value only while it is being displayed. Unknown values
 * fall through unchanged so homebrew modules never break.
 */

export type VocabGroup =
  | 'ability'
  | 'skill'
  | 'condition'
  | 'damage'
  | 'alignment'
  | 'size'
  | 'itemType'
  | 'itemSubtype'
  | 'rarity'
  | 'school'
  | 'coin'
  | 'saveMode'
  | 'season'
  | 'moon'
  | 'dayCycle'
  | 'questStatus'
  | 'spellLevel'
  | 'language'
  | 'className'
  | 'sense'
  | 'rollMode'

const PT: Record<VocabGroup, Record<string, string>> = {
  ability: {
    strength: 'Força',
    dexterity: 'Destreza',
    constitution: 'Constituição',
    intelligence: 'Inteligência',
    wisdom: 'Sabedoria',
    charisma: 'Carisma',
  },
  skill: {
    athletics: 'Atletismo',
    acrobatics: 'Acrobacia',
    'sleight of hand': 'Prestidigitação',
    stealth: 'Furtividade',
    arcana: 'Arcanismo',
    history: 'História',
    investigation: 'Investigação',
    nature: 'Natureza',
    religion: 'Religião',
    'animal handling': 'Adestrar animais',
    insight: 'Intuição',
    medicine: 'Medicina',
    perception: 'Percepção',
    survival: 'Sobrevivência',
    deception: 'Enganação',
    intimidation: 'Intimidação',
    performance: 'Atuação',
    persuasion: 'Persuasão',
  },
  condition: {
    blinded: 'Cego',
    charmed: 'Enfeitiçado',
    deafened: 'Surdo',
    exhausted: 'Exausto',
    frightened: 'Amedrontado',
    grappled: 'Agarrado',
    incapacitated: 'Incapacitado',
    invisible: 'Invisível',
    paralyzed: 'Paralisado',
    petrified: 'Petrificado',
    poisoned: 'Envenenado',
    prone: 'Caído',
    restrained: 'Impedido',
    stunned: 'Atordoado',
    unconscious: 'Inconsciente',
  },
  damage: {
    acid: 'ácido',
    bludgeoning: 'concussão',
    cold: 'frio',
    fire: 'fogo',
    force: 'energia',
    lightning: 'relâmpago',
    necrotic: 'necrótico',
    piercing: 'perfurante',
    poison: 'veneno',
    psychic: 'psíquico',
    radiant: 'radiante',
    slashing: 'cortante',
    thunder: 'trovão',
  },
  alignment: {
    'lawful good': 'Leal e bom',
    'neutral good': 'Neutro e bom',
    'chaotic good': 'Caótico e bom',
    'lawful neutral': 'Leal e neutro',
    neutral: 'Neutro',
    'true neutral': 'Neutro',
    'chaotic neutral': 'Caótico e neutro',
    'lawful evil': 'Leal e mau',
    'neutral evil': 'Neutro e mau',
    'chaotic evil': 'Caótico e mau',
  },
  size: {
    tiny: 'Minúsculo',
    small: 'Pequeno',
    medium: 'Médio',
    large: 'Grande',
    huge: 'Enorme',
    gargantuan: 'Colossal',
  },
  itemType: {
    weapon: 'arma',
    armor: 'armadura',
    shield: 'escudo',
    consumable: 'consumível',
    equipment: 'equipamento',
    gear: 'equipamento',
    tool: 'ferramenta',
    misc: 'diversos',
    miscellaneous: 'diversos',
    potion: 'poção',
    scroll: 'pergaminho',
    wand: 'varinha',
    ring: 'anel',
    rod: 'bastão',
    staff: 'cajado',
    treasure: 'tesouro',
    magic: 'mágico',
    magical: 'mágico',
    ammunition: 'munição',
  },
  itemSubtype: {
    other: 'outro',
    melee: 'corpo a corpo',
    ranged: 'à distância',
    'simple melee': 'corpo a corpo simples',
    'simple ranged': 'à distância simples',
    'martial melee': 'corpo a corpo marcial',
    'martial ranged': 'à distância marcial',
    light: 'leve',
    heavy: 'pesada',
    finesse: 'acuidade',
    'two-handed': 'duas mãos',
    versatile: 'versátil',
    thrown: 'arremesso',
    ammunition: 'munição',
    potion: 'poção',
    scroll: 'pergaminho',
    wand: 'varinha',
    ring: 'anel',
    rod: 'bastão',
    staff: 'cajado',
  },
  rarity: {
    common: 'Comum',
    uncommon: 'Incomum',
    rare: 'Raro',
    'very rare': 'Muito raro',
    legendary: 'Lendário',
    artifact: 'Artefato',
    varies: 'Varia',
  },
  school: {
    abjuration: 'abjuração',
    conjuration: 'conjuração',
    divination: 'adivinhação',
    enchantment: 'encantamento',
    evocation: 'evocação',
    illusion: 'ilusão',
    necromancy: 'necromancia',
    transmutation: 'transmutação',
  },
  coin: {
    gp: 'PO',
    sp: 'PP',
    cp: 'PC',
    pp: 'PL',
    ep: 'PE',
  },
  saveMode: {
    full: 'completo',
    essential: 'essencial',
  },
  season: {
    spring: 'Primavera',
    summer: 'Verão',
    autumn: 'Outono',
    fall: 'Outono',
    winter: 'Inverno',
  },
  moon: {
    'new moon': 'Lua nova',
    'waxing crescent': 'Lua crescente',
    'first quarter': 'Quarto crescente',
    'waxing gibbous': 'Gibosa crescente',
    'full moon': 'Lua cheia',
    'waning gibbous': 'Gibosa minguante',
    'last quarter': 'Quarto minguante',
    'waning crescent': 'Lua minguante',
  },
  dayCycle: {
    day: 'Dia',
    night: 'Noite',
    dawn: 'Amanhecer',
    dusk: 'Crepúsculo',
    morning: 'Manhã',
    afternoon: 'Tarde',
    evening: 'Noite',
  },
  questStatus: {
    active: 'Ativa',
    completed: 'Concluída',
    complete: 'Concluída',
    failed: 'Falhada',
    abandoned: 'Abandonada',
    paused: 'Pausada',
    'in progress': 'Em andamento',
    available: 'Disponível',
  },
  spellLevel: {
    cantrips: 'Truques',
    cantrip: 'Truque',
    '1st level': '1º círculo',
    '2nd level': '2º círculo',
    '3rd level': '3º círculo',
    '4th level': '4º círculo',
    '5th level': '5º círculo',
    '6th level': '6º círculo',
    '7th level': '7º círculo',
    '8th level': '8º círculo',
    '9th level': '9º círculo',
  },
  language: {
    common: 'Comum',
    elvish: 'Élfico',
    dwarvish: 'Anão',
    draconic: 'Dracônico',
    infernal: 'Infernal',
    celestial: 'Celestial',
    abyssal: 'Abissal',
    gnomish: 'Gnômico',
    halfling: 'Halfling',
    orc: 'Orc',
    sylvan: 'Silvestre',
    undercommon: 'Subcomum',
    giant: 'Gigante',
    goblin: 'Goblin',
    primordial: 'Primordial',
    'deep speech': 'Fala profunda',
  },
  className: {
    barbarian: 'Bárbaro',
    bard: 'Bardo',
    cleric: 'Clérigo',
    druid: 'Druida',
    fighter: 'Guerreiro',
    monk: 'Monge',
    paladin: 'Paladino',
    ranger: 'Patrulheiro',
    rogue: 'Ladino',
    sorcerer: 'Feiticeiro',
    warlock: 'Bruxo',
    wizard: 'Mago',
    artificer: 'Artífice',
  },
  sense: {
    darkvision: 'Visão no escuro',
    blindsight: 'Percepção cega',
    tremorsense: 'Sentido sísmico',
    truesight: 'Visão verdadeira',
  },
  rollMode: {
    normal: 'normal',
    advantage: 'vantagem',
    disadvantage: 'desvantagem',
  },
}

/** Lowercased lookup key: tolerate `Sleight_of_Hand`, extra spaces and casing. */
export function vocabKey(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[_-]+/g, ' ')
    .replace(/\s+/g, ' ')
}

export function vocabulary(locale: 'en' | 'pt-BR', group: VocabGroup, value: string): string {
  if (locale === 'en') return value
  return PT[group][vocabKey(value)] ?? value
}
