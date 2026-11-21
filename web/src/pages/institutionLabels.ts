import type { InstitutionType, InstitutionVerdict } from "../api/institutions";

export const institutionTypeLabels: Record<InstitutionType, string> = {
  association: "Associação",
  foundation: "Fundação",
  religious_organization: "Organização religiosa",
};

export const institutionVerdictLabels: Record<InstitutionVerdict, string> = {
  likely_charity: "Provável instituição beneficente",
  nonprofit: "Organização sem fins lucrativos",
  inactive: "Cadastro inativo",
  unlikely: "Pouco provável que seja beneficente",
};
