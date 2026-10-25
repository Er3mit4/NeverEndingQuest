/**
 * NPC screens, tooltips and map screens.
 *
 * Keys are the exact English strings rendered by the components, so the
 * English build keeps working unchanged.
 */
export const sheetNpcs = {
  // NpcCharacterSheet
  '{name} character sheet': 'Ficha de {name}',
  'Ability scores': 'Valores de atributo',
  'Abilities': 'Atributos',
  '{ability} modifier': 'Modificador de {ability}',
  '{ability} score': 'Valor de {ability}',
  'Combat statistics': 'Estatísticas de combate',
  'Combat': 'Combate',
  'Armor class': 'Classe de armadura',
  'Initiative': 'Iniciativa',
  'Hit points': 'Pontos de vida',
  'Saving throws & skills': 'Testes de resistência e perícias',
  'Proficient': 'Proficiente',
  'Not proficient': 'Não proficiente',
  'Equipment & magic': 'Equipamento e magia',
  'Features & background': 'Habilidades e antecedentes',
  'Personality & bonds': 'Personalidade e vínculos',
  'Personality Traits': 'Traços de personalidade',
  'Ideals': 'Ideais',
  'Bonds': 'Vínculos',
  'Flaws': 'Fraquezas',

  // NpcDetailModal
  'Saving Throws': 'Testes de resistência',
  'Skills': 'Perícias',
  'Inventory': 'Inventário',
  'Key Abilities': 'Habilidades principais',
  'Racial Traits': 'Traços raciais',
  'Background': 'Antecedente',
  'Spellcasting': 'Conjuração',
  "{name}'s {title}": '{title} de {name}',
  'No skills available.': 'Nenhuma perícia disponível.',
  'No key abilities available.': 'Nenhuma habilidade principal disponível.',
  'No racial traits available.': 'Nenhum traço racial disponível.',
  'No background available.': 'Nenhum antecedente disponível.',
  'No items in inventory.': 'Nenhum item no inventário.',
  'Equipped': 'Equipado',
  '{current}/{max} charges': '{current}/{max} cargas',
  'This character does not have spellcasting abilities.': 'Este personagem não possui habilidades de conjuração.',
  'Save DC: {dc}': 'CD de conjuração: {dc}',
  'Spell Attack: {value}': 'Ataque mágico: {value}',
  'Spell reference unavailable.': 'Referência de magias indisponível.',
  'Retry': 'Tentar novamente',
  '{current}/{max} slots': '{current}/{max} espaços',
  'Prepared': 'Preparada',
  'Unknown NPC': 'NPC desconhecido',

  // NpcInventoryPanel
  'NPC inventory': 'Inventário do NPC',
  'Search NPC inventory': 'Buscar no inventário do NPC',
  'Find an item…': 'Encontrar um item…',
  'Filter NPC inventory': 'Filtrar inventário do NPC',
  'All items': 'Todos os itens',
  'Sort NPC inventory': 'Ordenar inventário do NPC',
  'Name A–Z': 'Nome A–Z',
  'Type': 'Tipo',
  'Quantity': 'Quantidade',
  '{shown} / {total} entries': '{shown} / {total} entradas',
  'No items match the filter.': 'Nenhum item corresponde ao filtro.',

  // NpcsTab
  'Full character details are not available for this NPC.': 'Os detalhes completos deste NPC não estão disponíveis.',
  'No NPC data available': 'Nenhum dado de NPC disponível',
  'Saving Throw': 'Teste de resistência',
  'Spells': 'Magias',
  'HP': 'PV',
  'AC': 'CA',
  'XP': 'XP',
  'GP': 'PO',
  'SP': 'PP',
  'CP': 'PC',
  'INIT': 'INIC',
  'Level {level}': 'Nível {level}',
  'Status:': 'Status:',
  'Condition:': 'Condição:',

  // NpcTabbedSheet
  'NPC character': 'Ficha do NPC',

  // CharacterTooltips
  '{ability} Skills': 'Perícias de {ability}',

  // MapTab / MapModal
  'Map is showing {mapArea}; you are in {currentArea}': 'O mapa mostra {mapArea}; você está em {currentArea}',
  'Parchment': 'Pergaminho',
  'Night ink': 'Tinta noturna',
  '☾ night': '☾ noite',
  '☀ day': '☀ dia',
  '⊙ fit': '⊙ ajustar',
  '▭ whole': '▭ inteiro',
  '⤢ expand': '⤢ expandir',
  '✕ close': '✕ fechar',
  'The map is blank…': 'O mapa está em branco…',
  'You are here': 'Você está aqui',
} satisfies Record<string, string>
