/**
 * Attorney Help — deterministic suggested questions (spec REQ-3 / TASK-2).
 *
 * Rule-based, NO LLM. Returns 3–5 questions tailored to the user's profile and
 * deadlines, always including the "most important things" fallback.
 */
import type { Profile } from "../api/profile";
import type { ComputedDeadline } from "./computeDeadlines";

const FALLBACK =
  "What are the most important things I should do to protect my status right now?";

export function generateSuggestedQuestions(
  profile: Profile,
  deadlines: ComputedDeadline[],
): string[] {
  const questions: string[] = [];

  if (
    profile.visaType === "OPT" &&
    (profile.unemploymentDaysUsed ?? 0) > 60
  ) {
    questions.push(
      "What happens if I exceed 90 unemployment days before finding a job?",
    );
  }
  if (profile.stemOptStatus === "pending") {
    questions.push(
      "What is my status if my STEM OPT extension is not approved before my OPT EAD expires?",
    );
  }
  if (profile.h1bTransferInProgress) {
    questions.push(
      "Am I authorized to continue working during an H-1B transfer?",
    );
  }
  if ((profile.upcomingTravel?.length ?? 0) > 0) {
    questions.push(
      "What documents do I need to re-enter the US after traveling abroad?",
    );
  }
  if (deadlines.some((d) => d.tier === "critical")) {
    questions.push(
      "I have a deadline within 7 days — what should I do immediately?",
    );
  }

  questions.push(FALLBACK); // always included
  return questions.slice(0, 5);
}
