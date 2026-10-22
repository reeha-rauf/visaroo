/**
 * Attorney Help — curated legal resources (spec REQ-5).
 *
 * Static, hand-verified links to legitimate third-party directories and official
 * government resources. Visaroo brokers no attorney relationships (REQ-7).
 */
export type ResourceCategory = "attorney" | "free_help" | "university" | "government";

export interface LegalResource {
  name: string;
  description: string;
  url: string;
  category: ResourceCategory;
  region?: string;
}

export const CATEGORY_TITLES: Record<ResourceCategory, string> = {
  attorney: "Find an immigration attorney",
  free_help: "Free and low-cost legal help",
  university: "University & campus resources",
  government: "Official government resources",
};

export const LEGAL_RESOURCES: LegalResource[] = [
  // Find an immigration attorney
  {
    name: "AILA — Find an Immigration Lawyer",
    description:
      "The American Immigration Lawyers Association's official directory of member attorneys.",
    url: "https://www.ailalawyer.com/",
    category: "attorney",
  },
  {
    name: "Immigrant Legal Resource Center (ILRC)",
    description: "Legal trainings, resources, and referrals on immigration law.",
    url: "https://www.ilrc.org/",
    category: "attorney",
  },
  {
    name: "National Immigration Law Center (NILC)",
    description: "Policy and legal resources focused on low-income immigrants.",
    url: "https://www.nilc.org/",
    category: "attorney",
  },

  // Free and low-cost legal help
  {
    name: "CLINIC — Catholic Legal Immigration Network",
    description: "Nationwide network of nonprofit immigration legal programs.",
    url: "https://www.cliniclegal.org/",
    category: "free_help",
  },
  {
    name: "Northwest Immigrant Rights Project",
    description: "Free and low-cost immigration legal services.",
    url: "https://www.nwirp.org/",
    category: "free_help",
    region: "Pacific Northwest",
  },
  {
    name: "Immigrant Legal Resource Center — Bay Area",
    description: "Legal help and referrals for the San Francisco Bay Area.",
    url: "https://www.ilrc.org/",
    category: "free_help",
    region: "Bay Area",
  },
  {
    name: "NYC — Immigrant Advocates Response Collaborative (NYIFUP / Legal Aid)",
    description: "Free immigration legal services across New York City.",
    url: "https://www.legalaidnyc.org/get-help/immigration-problems/",
    category: "free_help",
    region: "New York City",
  },
  {
    name: "ProBAR (South Texas Pro Bono Asylum Representation)",
    description: "Free legal services in Texas via the American Bar Association.",
    url: "https://www.americanbar.org/groups/public_interest/immigration/projects_initiatives/probar/",
    category: "free_help",
    region: "Texas",
  },
  {
    name: "National Immigrant Justice Center (Midwest)",
    description: "Legal services and advocacy based in the Midwest.",
    url: "https://immigrantjustice.org/",
    category: "free_help",
    region: "Midwest",
  },

  // University & campus resources
  {
    name: "Find your DSO / international student office",
    description:
      "Search \"[your university] international student office\" for your DSO's contact details.",
    url: "https://studyinthestates.dhs.gov/",
    category: "university",
  },
  {
    name: "Study in the States (SEVP)",
    description: "DHS resource hub for F/M students, with DSO and SEVP guidance.",
    url: "https://studyinthestates.dhs.gov/students",
    category: "university",
  },

  // Official government resources
  {
    name: "USCIS Contact Center",
    description: "Official USCIS help line and online tools.",
    url: "https://www.uscis.gov/contactcenter",
    category: "government",
  },
  {
    name: "SEVP Response Center",
    description: "Contact SEVP for SEVIS and F/M student program questions.",
    url: "https://www.ice.gov/sevis/contact",
    category: "government",
  },
  {
    name: "E-Verify Employer Help",
    description: "E-Verify support — useful for STEM OPT employers.",
    url: "https://www.e-verify.gov/contact-us",
    category: "government",
  },
];
