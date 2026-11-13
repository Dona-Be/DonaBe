export const causeLabels = {
  children_and_teenagers: "Crianças e adolescentes",
  elderly: "Idosos",
  people_with_disabilities: "Pessoas com deficiência",
  health: "Saúde",
  education: "Educação",
  hunger_relief: "Combate à fome",
  homeless_people: "Pessoas em situação de rua",
  women: "Mulheres",
  animals: "Animais",
  environment: "Meio ambiente",
} as const;

export type Cause = keyof typeof causeLabels;

export const causes = Object.keys(causeLabels) as Cause[];
