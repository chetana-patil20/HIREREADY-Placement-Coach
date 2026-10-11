"""
AI Service
==========
Single abstraction point for every AI-powered feature in HireReady
(placement coach chat, resume feedback, preparation-plan explanations,
interview question generation and answer evaluation).

Design:
- If AI_PROVIDER + AI_API_KEY are configured, `_call_llm()` routes to the
  appropriate provider SDK:
    • "gemini"    → Google Generative AI SDK  (primary)
    • "openai"    → OpenAI Python SDK         (optional)
    • "anthropic" → httpx direct call         (legacy support)
- If not configured, or if the API call fails, every public method
  transparently falls back to a deterministic, profile-aware mock
  implementation so the whole app keeps working with zero setup.
- The AI is NEVER used to decide eligibility, scores, deadlines or
  matching — those come from the engines. The AI is only used to
  *explain* facts that are handed to it, and it is explicitly told not
  to invent data it wasn't given.
- Every public method accepts already-computed facts (from the
  deterministic engines) as input, so the AI explains real data instead
  of guessing.
"""
import json
import logging
import random
import re
from typing import List, Dict, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

SYSTEM_GUARDRAIL = (
    "You are the HireReady Placement Coach, an AI assistant embedded in a college "
    "placement platform. Answer general questions across student placements, "
    "interview preparation, resumes, aptitude, coding, projects, communication, "
    "applications, and early careers. Use general knowledge for guidance, and "
    "use the supplied profile and computed facts for personalized advice. NEVER "
    "invent a student's CGPA, a company cutoff, deadline, CTC, eligibility "
    "outcome, or placement drive detail that was not provided. Say when current "
    "or institution-specific information is not available. Give clear steps and "
    "examples; connect recommendations to the student's actual gaps when possible."
)


class AIService:
    def __init__(self):
        self.enabled: bool = settings.ai_enabled
        self.provider: str = settings.AI_PROVIDER.lower() if settings.AI_PROVIDER else ""

        if self.enabled:
            logger.info(
                "AIService initialised — provider=%s  model=%s  api_key_set=%s",
                self.provider,
                settings.AI_MODEL,
                bool(settings.AI_API_KEY),
            )
        else:
            logger.info(
                "AIService initialised in FALLBACK mode "
                "(AI_PROVIDER=%r  AI_API_KEY configured=%s). "
                "All AI features will use the local smart mock.",
                settings.AI_PROVIDER,
                bool(settings.AI_API_KEY),
            )

    # ------------------------------------------------------------------
    # Low-level LLM dispatch
    # ------------------------------------------------------------------

    def _call_llm(self, system: str, user: str, max_tokens: int = 600) -> Optional[str]:
        """Route to the configured provider and return the text response.

        Returns None on any error so callers transparently fall back to the
        deterministic mock — the FastAPI endpoints never crash.
        """
        if not self.enabled:
            return None

        try:
            if self.provider == "gemini":
                return self._call_gemini(system, user, max_tokens)
            elif self.provider == "openai":
                return self._call_openai(system, user, max_tokens)
            elif self.provider == "anthropic":
                return self._call_anthropic(system, user, max_tokens)
            else:
                logger.warning(
                    "AIService: unknown provider %r — activating fallback.", self.provider
                )
                return None
        except Exception as exc:
            logger.error(
                "AIService: unexpected error dispatching to provider %r: %s — activating fallback.",
                self.provider,
                exc,
            )
            return None

    # ---- Gemini -------------------------------------------------------

    def _call_gemini(self, system: str, user: str, max_tokens: int) -> Optional[str]:
        try:
            import google.generativeai as genai  # imported lazily so missing SDK never breaks startup

            genai.configure(api_key=settings.AI_API_KEY)
            model_name = settings.AI_MODEL or "gemini-2.5-flash"
            model = genai.GenerativeModel(
                model_name=model_name,
                system_instruction=system,
            )
            generation_config = genai.types.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=0.4,
            )
            response = model.generate_content(
                user,
                generation_config=generation_config,
            )
            text = response.text.strip() if response.text else None
            logger.info("Gemini API call succeeded (model=%s, chars=%s).", model_name, len(text) if text else 0)
            return text or None
        except ImportError:
            logger.error(
                "AIService: google-generativeai SDK is not installed. "
                "Run: pip install google-generativeai==0.8.3 — falling back to local mock."
            )
            return None
        except Exception as exc:
            logger.error("AIService: Gemini API call failed: %s — activating fallback.", exc)
            return None

    # ---- OpenAI -------------------------------------------------------

    def _call_openai(self, system: str, user: str, max_tokens: int) -> Optional[str]:
        try:
            from openai import OpenAI  # imported lazily

            client = OpenAI(api_key=settings.AI_API_KEY)
            model_name = settings.AI_MODEL or "gpt-4o-mini"
            response = client.chat.completions.create(
                model=model_name,
                max_tokens=max_tokens,
                temperature=0.4,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
            )
            text = response.choices[0].message.content.strip()
            logger.info("OpenAI API call succeeded (model=%s, chars=%s).", model_name, len(text))
            return text or None
        except ImportError:
            logger.error(
                "AIService: openai SDK is not installed. "
                "Run: pip install openai==1.51.0 — falling back to local mock."
            )
            return None
        except Exception as exc:
            logger.error("AIService: OpenAI API call failed: %s — activating fallback.", exc)
            return None

    # ---- Anthropic (legacy httpx path — preserved unchanged) ----------

    def _call_anthropic(self, system: str, user: str, max_tokens: int) -> Optional[str]:
        try:
            resp = httpx.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.AI_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": settings.AI_MODEL,
                    "max_tokens": max_tokens,
                    "system": system,
                    "messages": [{"role": "user", "content": user}],
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()
            parts = [b["text"] for b in data.get("content", []) if b.get("type") == "text"]
            text = "\n".join(parts).strip()
            logger.info("Anthropic API call succeeded (chars=%s).", len(text))
            return text or None
        except Exception as exc:
            logger.error("AIService: Anthropic API call failed: %s — activating fallback.", exc)
            return None

    # ------------------------------------------------------------------
    # Placement coach chat
    # ------------------------------------------------------------------

    def answer_coach_question(self, student_context: Dict, message: str, facts: Dict) -> str:
        prompt = (
            f"STUDENT PROFILE:\n{json.dumps(student_context, indent=2)}\n\n"
            f"COMPUTED FACTS (from deterministic engines — treat as ground truth):\n"
            f"{json.dumps(facts, indent=2)}\n\n"
            f"RECENT CONVERSATION (use only to understand follow-up questions):\n"
            f"{json.dumps(facts.get('recent_conversation', []), indent=2)}\n\n"
            f"STUDENT QUESTION:\n{message}\n\n"
            "Answer directly and specifically, referencing the numbers/skills above. "
            "Do not invent any data that is not in STUDENT PROFILE or COMPUTED FACTS."
        )
        llm_answer = self._call_llm(SYSTEM_GUARDRAIL, prompt, max_tokens=500)
        if llm_answer:
            return llm_answer
        logger.info("answer_coach_question: using local smart fallback.")
        return self._mock_coach_answer(message, facts, student_context)

    def _mock_coach_answer(self, message: str, facts: Dict, student_context: Optional[Dict] = None) -> str:
        msg = message.lower()
        context = student_context or {}
        readiness = facts.get("readiness", {})
        gap = facts.get("skill_gap", {})
        best_match = facts.get("best_match")

        if "ready" in msg or "readiness" in msg:
            if not readiness:
                return "I don't have verified readiness data for you yet. Complete your profile (skills, projects, resume) first."
            return (
                f"Your overall placement readiness is {readiness.get('overall')}%. "
                f"Academic {readiness.get('academic')}%, Technical Skills {readiness.get('technical_skills')}%, "
                f"Projects {readiness.get('projects')}%, Resume {readiness.get('resume')}%, "
                f"Aptitude {readiness.get('aptitude')}%, Interview {readiness.get('interview')}%. "
                f"Your biggest weakness is {readiness.get('weakest_area')} — focus there next."
            )
        if "eligib" in msg or "which role" in msg or "which compan" in msg:
            all_matches = facts.get("matches") or []
            eligible_matches = [m for m in all_matches if m.get("eligible")]
            if any(term in msg for term in ("which", "list", "all", "company", "companies")) and all_matches:
                if eligible_matches:
                    names = ", ".join(f"{m.get('role_title')} at {m.get('company_name')}" for m in eligible_matches)
                    return f"Based on the profile data and listed drive criteria, you're currently eligible for: {names}. Check each drive's deadline and full requirements before applying."
                return "Your profile does not currently meet the listed eligibility rules for the available roles. Open Placements and review each role's specific failure reasons; this is different from the match percentage."
            if best_match is None:
                return "Add your CGPA, backlogs, graduation year and skills so I can check eligibility against real placement drives."
            if best_match.get("eligible"):
                return f"You're eligible for {best_match.get('role_title')} at {best_match.get('company_name')}."
            reasons = best_match.get("eligibility_reasons") or []
            return (
                "You're not eligible for that role. " + " ".join(reasons)
                if reasons
                else "You're not eligible for that role right now."
            )
        if "missing" in msg or "gap" in msg or any(term in msg for term in (
            "what skills", "which skills", "required skills", "skills needed", "skills should", "skill gap"
        )):
            if not gap:
                return "Set a target role on your profile so I can compare your skills against what it requires."
            missing = gap.get("top_skills_to_learn") or []
            if not missing:
                return f"You're covering the required skills well for {gap.get('role_name')}. Focus on projects and interview prep next."
            return f"For {gap.get('role_name')}, prioritize learning: {', '.join(missing)}."
        if "plan" in msg or "30" in msg or "preparation plan" in msg:
            return (
                "I can generate a personalized preparation plan from the Preparation Plan page — "
                "it's built from your actual skill gaps and weakest readiness areas, not a generic template. "
                "Go to 'Preparation Plan' and click 'Generate Plan'."
            )
        if "resume" in msg:
            resume = facts.get("resume")
            if resume:
                return (
                    f"Your last resume score was {resume.get('score')}/100. "
                    f"Top issue: {resume.get('top_issue', 'add more measurable outcomes to your project descriptions')}."
                )
            return "Paste your resume in the Resume Analyzer page and I'll score it and flag specific issues."
        if "interview" in msg or "mock" in msg:
            score = readiness.get("interview")
            prefix = f"Your interview readiness indicator is {score}%. " if score is not None else ""
            return prefix + "Practice in Mock Interview with HR, Technical, Aptitude, or Role-specific sessions. Structure answers by responding directly, explaining your reasoning, and adding a relevant example. Review the feedback after each question and practice the weak points before retrying."

        if any(k in msg for k in ("placement process", "placement drive", "campus placement", "placement season", "placement procedure")):
            return "A typical campus placement flow is: complete your profile and resume, check each drive's eligibility and deadline, apply through your placement cell, prepare for aptitude or coding rounds, then practice technical and HR interviews. Use the Placements page for drives listed by your college; I don't have access to unlisted company timelines."
        if any(k in msg for k in ("aptitude", "quantitative", "logical reasoning", "reasoning test")):
            return "For aptitude rounds, check the topics and time limit in the drive notice. Practice arithmetic, percentages, ratios, probability, logical reasoning, and data interpretation in timed sets. Track accuracy and time per question, then revise the topic causing the most errors. Use Aptitude practice and the Preparation Plan to keep a routine."
        if any(k in msg for k in ("resume", "cv", "curriculum vitae")):
            resume = facts.get("resume")
            prefix = f"Your latest resume analysis score is {resume.get('score')}/100. " if resume else "I don't have a recent resume analysis yet. "
            return prefix + "Use the Resume Analyzer to identify gaps. Keep the document concise and role-focused, and describe each project with the problem, your contribution, tools, and a truthful measurable result. Tailor keywords to each job description without adding skills or achievements you cannot discuss."
        if any(k in msg for k in ("project", "portfolio", "github")):
            projects = context.get("project_count", 0)
            return f"Your profile currently lists {projects} project(s). Choose one project you can explain end to end: problem, design choices, your contribution, trade-offs, tests, and results. A focused working project with a clear README and verifiable code is more useful than several unfinished demos."
        if any(k in msg for k in ("cgpa", "backlog", "academic", "marks", "percentage")):
            cgpa = context.get("cgpa", "not provided")
            backlogs = context.get("backlogs", "not provided")
            return f"Your profile lists CGPA {cgpa}/10 and {backlogs} active backlog(s). Eligibility is checked against each drive's published cutoffs; review the reason list for each role on Placements. If an academic cutoff is not met, focus on drives whose criteria you meet while strengthening skills and project evidence."
        if any(k in msg for k in ("group discussion", "communication", "soft skill", "teamwork")):
            return "For group discussions, make a concise point, support it with a reason or example, listen and build on others' ideas, and invite quieter participants in. Avoid interrupting or dominating. Practice explaining one idea in about 30–45 seconds and summarize the group's points respectfully."
        if any(k in msg for k in ("salary", "ctc", "package", "negotiate")):
            return "Compare the offer details, including fixed pay, variable pay, benefits, location, role, and any service or training conditions. Ask the recruiter or placement cell to clarify anything ambiguous. Treat the CTC shown on a listed drive as the platform's published figure; I cannot verify or negotiate an offer for you."
        if any(k in msg for k in ("coding", "data structure", "algorithm", "leetcode", "programming")):
            skills = ", ".join(s.get("name", "") for s in context.get("skills", [])[:5]) or "no skills listed yet"
            return f"Your profile lists these skills: {skills}. For coding rounds, practice arrays and strings, hash maps, stacks and queues, trees, sorting and searching, and complexity analysis. Explain your approach before coding, test edge cases, and state the time and space complexity. Prioritize topics named in your target role's missing skills."
        if any(k in msg for k in ("apply", "application", "eligibility", "eligible")):
            if best_match is None:
                return "Complete your CGPA, backlogs, graduation year, branch, and skills in Profile. Then open Placements to see eligibility criteria and required skills for each available drive. Eligibility from published criteria is separate from the match percentage, which estimates profile fit."
            reasons = best_match.get("eligibility_reasons") or []
            fit = f"For the closest listed opportunity ({best_match.get('role_title')} at {best_match.get('company_name')}), estimated profile match is {best_match.get('overall_match')}%. Eligibility: {'eligible' if best_match.get('eligible') else 'not eligible'}. "
            return fit + ("Reasons: " + "; ".join(reasons) if reasons else "See Placements for its exact requirements and deadline.")

        return (
            "I can answer placement questions about eligibility, campus drives, preparation plans, aptitude and coding rounds, interviews, resumes, projects, academics, communication, and offers. For your personal data, I use your saved profile and listed drives. Tell me the role or round you're preparing for and what you want to improve."
        )

    # ------------------------------------------------------------------
    # Resume feedback (qualitative suggestions only — score is deterministic)
    # ------------------------------------------------------------------

    def resume_suggestions(self, resume_text: str, target_role: str, deterministic_findings: Dict) -> List[str]:
        prompt = (
            f"TARGET ROLE: {target_role or 'not specified'}\n"
            f"DETERMINISTIC FINDINGS (already computed, do not contradict):\n"
            f"{json.dumps(deterministic_findings, indent=2)}\n\n"
            f"RESUME TEXT:\n{resume_text[:3000]}\n\n"
            "Give 3–5 specific, actionable rewrite suggestions for this exact resume. "
            "Do not invent achievements the student doesn't have. "
            "Return each suggestion on its own line prefixed with '- '."
        )
        llm = self._call_llm(SYSTEM_GUARDRAIL, prompt, max_tokens=400)
        if llm:
            return [line.strip("-• ").strip() for line in llm.split("\n") if line.strip()]
        logger.info("resume_suggestions: using local smart fallback.")
        return self._mock_resume_suggestions(deterministic_findings)

    def _mock_resume_suggestions(self, findings: Dict) -> List[str]:
        suggestions = []
        if findings.get("weak_project_descriptions"):
            suggestions.append("Rewrite project bullets to start with an action verb (Built, Designed, Automated) and state a measurable outcome.")
        if findings.get("missing_github"):
            suggestions.append("Add your GitHub profile link so recruiters can verify your project work.")
        if findings.get("missing_metrics"):
            suggestions.append("Add measurable impact to at least 2 bullet points, e.g. 'reduced load time by 30%' or 'processed 10k+ records'.")
        if findings.get("missing_keywords"):
            kws = ", ".join(findings["missing_keywords"][:5])
            suggestions.append(f"Add role-relevant keywords your resume is currently missing: {kws}.")
        if findings.get("short_resume"):
            suggestions.append("Your resume looks short — add at least one more project or certification section.")
        if not suggestions:
            suggestions.append("Your resume covers the basics well. Focus next on tailoring keywords to each specific role you apply for.")
        return suggestions

    # ------------------------------------------------------------------
    # Preparation plan explanation
    # ------------------------------------------------------------------

    def explain_plan(self, student_context: Dict, plan_summary: Dict) -> str:
        prompt = (
            f"STUDENT PROFILE:\n{json.dumps(student_context, indent=2)}\n\n"
            f"GENERATED PLAN SUMMARY:\n{json.dumps(plan_summary, indent=2)}\n\n"
            "In 3–4 sentences, explain why this plan is structured this way for THIS student "
            "(reference their actual weak areas and missing skills)."
        )
        llm = self._call_llm(SYSTEM_GUARDRAIL, prompt, max_tokens=250)
        if llm:
            return llm
        weakest = student_context.get("weakest_area", "your weakest area")
        role = plan_summary.get("role") or "your target role"
        top_skills = ", ".join(plan_summary.get("top_skills_to_learn", [])[:3]) or "your core skill gaps"
        return (
            f"This plan targets {role}. Week 1–2 focus on {top_skills} because those are your biggest "
            f"gaps against this role's requirements. Week 3 builds coding and aptitude speed, and week 4 "
            f"is dedicated to resume polish and mock interviews since {weakest} was flagged as your weakest area."
        )

    # ------------------------------------------------------------------
    # Mock interview
    # ------------------------------------------------------------------

    QUESTION_BANKS = {
        "HR": [
            "Tell me about yourself.",
            "What are your greatest strengths and weaknesses?",
            "Why should we hire you for this role?",
            "Describe a time you worked in a team to solve a problem.",
            "Where do you see yourself in three years?",
            "Why do you want to work at our company?",
            "Describe a challenge you faced and how you handled it.",
            "Tell me about a time you received critical feedback and how you responded.",
            "What is one achievement you are proud of, and what was your contribution?",
            "Describe a disagreement with a teammate and how you resolved it.",
            "How do you prioritize when several deadlines are close?",
            "What motivates you to do your best work?",
            "Tell me about a time you had to learn something quickly.",
            "What would you do if you realized you had made a mistake at work?",
            "Describe a situation where you showed initiative.",
            "How do you handle working under pressure?",
            "What kind of team helps you do your best work?",
            "What are you hoping to learn in your first role?",
            "Tell me about a goal you set and how you achieved it.",
            "How would you explain a technical idea to a non-technical person?",
            "What would you do if you disagreed with your manager's approach?",
            "Describe a time you adapted to a change in plans.",
            "How do you respond when you do not know the answer to a question?",
            "What makes you a good fit for this role?",
        ],
        "Aptitude": [
            "A train travels 60 km in 45 minutes. What is its speed in km/h?",
            "If the ratio of two numbers is 3:5 and their sum is 128, find the numbers.",
            "A shopkeeper marks an item 40% above cost price and gives a 10% discount. Find the profit percentage.",
            "In how many ways can the letters of the word 'TABLE' be arranged?",
            "If 5 workers can complete a task in 12 days, how many days will 3 workers take?",
            "A product costs 800 rupees and is sold for 920 rupees. What is the profit percentage?",
            "A car covers 150 km in 2.5 hours. Find its average speed.",
            "A number is increased by 20% and then reduced by 20%. What is the net percentage change?",
            "The average of five numbers is 18. If four are 12, 16, 20, and 22, find the fifth.",
            "A bag contains 4 red and 6 blue balls. What is the probability of drawing a red ball?",
            "A can finish a task in 10 days and B in 15 days. How long together?",
            "If 25% of a number is 45, what is the number?",
            "A two-digit number has digits summing to 9. Reversing the digits increases it by 27. Find it.",
            "Find the next number in the sequence: 2, 6, 12, 20, 30, ?",
            "A shop gives successive discounts of 10% and 20%. What is the equivalent discount?",
            "A student scores 72 out of 90. What percentage is that?",
            "If 8 machines make 240 items in 6 hours, how many items do 4 machines make in 3 hours?",
            "A person travels equal distances at 30 km/h and 60 km/h. What is the average speed?",
            "How many distinct arrangements can be made from the letters in LEVEL?",
            "A pipe fills a tank in 6 hours and a leak empties it in 12 hours. How long to fill with both open?",
        ],
        "Technical": {
            "python": [
                "What is the difference between a list and a tuple in Python?",
                "Explain Python's GIL and its impact on multithreading.",
                "What are Python decorators and when would you use one?",
                "How do Python dictionaries handle key lookups, and what is the average lookup complexity?",
                "What is a generator in Python, and when is it preferable to a list?",
                "How do exceptions and context managers help make Python code safer?",
                "What is the difference between shallow and deep copying in Python?",
                "How would you test a Python function that calls an external API?",
                "What is a virtual environment, and why use one for a project?",
                "Explain the difference between a class method, static method, and instance method.",
                "How would you profile and improve a slow Python function?",
                "What are mutable default arguments, and why can they cause bugs?",
            ],
            "sql": [
                "What is the difference between INNER JOIN and LEFT JOIN?",
                "What is normalization and why is it used?",
                "Write a query to find the second highest salary from an Employee table.",
                "What is the difference between WHERE and HAVING in SQL?",
                "How would you find duplicate email addresses in a Users table?",
                "Explain primary keys and foreign keys with an example.",
                "What is an index, and what trade-off does it introduce?",
                "How would you calculate a running total with SQL?",
                "What is the difference between UNION and UNION ALL?",
                "How do NULL values behave in SQL comparisons?",
                "What are transactions, and what does ACID mean?",
                "How can a window function help rank employees by salary?",
            ],
            "default": [
                "Explain the difference between a stack and a queue.",
                "What is Big-O notation and why does it matter?",
                "How would you detect a cycle in a linked list?",
                "What is the difference between REST and SOAP APIs?",
                "How would you explain time and space complexity for a hash map lookup?",
                "What is the difference between a process and a thread?",
                "How does an HTTP request travel from a browser to a server?",
                "What is a database transaction, and why do applications need one?",
                "How would you design pagination for an API that returns many records?",
                "What is the difference between authentication and authorization?",
                "How would you find the first non-repeating character in a string?",
                "What is a race condition, and how can you prevent one?",
                "How would you debug a service that suddenly became slow?",
                "What is caching, and what can make cached data stale?",
                "How do you use Git branches and pull requests in a team?",
                "What is input validation, and where should it happen?",
                "How would you test an API endpoint, including error cases?",
                "What happens when a database query uses an index?",
            ],
        },
        "Role-specific": [
            "Walk me through a project most relevant to this role and explain your personal contribution.",
            "How would you approach the first week of work in this role?",
            "Describe a technical decision you made in a project and the trade-offs you considered.",
            "Tell me how you would investigate a production bug reported by a user.",
            "How do you decide what to build first when requirements are unclear?",
            "Describe how you would collaborate with a teammate to deliver a feature.",
            "What role-related skill are you currently improving, and how are you practicing it?",
            "How would you explain one of your projects to a recruiter in two minutes?",
            "What would you monitor after deploying a new feature?",
            "Tell me about a time you improved reliability, performance, or usability.",
            "How would you break a large task into smaller deliverable steps?",
            "What questions would you ask before starting a new assignment in this role?",
            "How do you verify that your solution meets the user's actual need?",
            "Describe a project challenge and how you evaluated alternative solutions.",
            "What would you do if a deadline conflicted with a quality issue you discovered?",
        ],
    }

    def generate_interview_question(
        self,
        role: str,
        mode: str,
        question_number: int,
        student_skills: List[str],
        asked_already: List[str],
    ) -> str:
        if self.enabled:
            prompt = (
                f"Generate ONE {mode} interview question (question #{question_number}) for a candidate "
                f"applying for the role '{role or 'Software Developer'}'. "
                f"Their known skills: {', '.join(student_skills) or 'not specified'}. "
                f"Questions already asked in this session (do not repeat): {asked_already}. "
                "Return only the question text, no numbering, no preamble."
            )
            llm = self._call_llm(SYSTEM_GUARDRAIL, prompt, max_tokens=120)
            if llm and llm.strip().strip('"').casefold() not in {q.casefold() for q in asked_already}:
                return llm.strip().strip('"')
        return self._mock_question(role, mode, student_skills, asked_already)

    def _mock_question(
        self, role: str, mode: str, student_skills: List[str], asked_already: List[str]
    ) -> str:
        if mode == "HR":
            bank = self.QUESTION_BANKS["HR"]
        elif mode == "Aptitude":
            bank = self.QUESTION_BANKS["Aptitude"]
        elif mode == "Role-specific":
            bank = self.QUESTION_BANKS["Role-specific"]
        else:  # Technical or Role-specific
            tech = self.QUESTION_BANKS["Technical"]
            key = "default"
            for skill in student_skills:
                if skill.lower() in tech:
                    key = skill.lower()
                    break
            bank = tech.get(key, tech["default"]) + tech["default"]

        remaining = [q for q in bank if q not in asked_already]
        if not remaining:
            remaining = bank
        return random.choice(remaining)

    def evaluate_interview_answer(
        self, question: str, answer: str, role: str, mode: str
    ) -> Dict:
        if self.enabled:
            prompt = (
                f"Interview mode: {mode}. Role: {role or 'Software Developer'}.\n"
                f"Question: {question}\n"
                f"Candidate answer: {answer}\n\n"
                "Return ONLY a JSON object with exactly these keys:\n"
                "  score         — integer 0–100\n"
                "  strengths     — string describing what the candidate did well\n"
                "  weaknesses    — string describing what was missing or weak\n"
                "  improved_answer — string with a stronger version of their answer\n"
                "Score with this rubric: relevance to the question 40 points, factual/technical correctness 30, "
                "specific evidence or examples 15, clear structure 10, concise communication 5. A short correct "
                "answer can score well; a long vague or incorrect answer must score low. Make scores vary with the "
                "actual answer and do not default to a repeated score.\n"
                "Do not include any text outside the JSON object."
            )
            llm = self._call_llm(SYSTEM_GUARDRAIL, prompt, max_tokens=450)
            if llm:
                try:
                    cleaned = llm.strip()
                    # Strip markdown code fences if the model wrapped the JSON
                    if cleaned.startswith("```"):
                        cleaned = cleaned.strip("`")
                        if cleaned.lower().startswith("json"):
                            cleaned = cleaned[4:].strip()
                    parsed = json.loads(cleaned)
                    return {
                        "score": max(0, min(100, int(parsed.get("score", 50)))),
                        "strengths": str(parsed.get("strengths", "")),
                        "weaknesses": str(parsed.get("weaknesses", "")),
                        "improved_answer": str(parsed.get("improved_answer", "")),
                    }
                except Exception as exc:
                    logger.warning(
                        "evaluate_interview_answer: failed to parse LLM JSON (%s) — using fallback.", exc
                    )
        return self._mock_evaluate_answer(question, answer)

    def _mock_evaluate_answer(self, question: str, answer: str) -> Dict:
        """Deterministic evaluator used when no LLM key is configured."""
        words = answer.strip().split()
        length = len(words)
        if length == 0:
            return {
                "score": 0,
                "strengths": "No answer was given.",
                "weaknesses": "You didn't answer the question.",
                "improved_answer": "Give a direct answer first, then explain it with a short example.",
            }

        q = question.lower()
        a = answer.lower()

        factual_checks = [
            (
                ("stack", "queue"),
                ["stack", "lifo", "queue", "fifo"],
                "A strong answer should state that a stack is LIFO and a queue is FIFO.",
                "Stack = LIFO (Last In, First Out); Queue = FIFO (First In, First Out). Example: a stack is like a pile of plates, while a queue is like people waiting in line.",
            ),
            (
                ("list", "tuple"),
                ["list", "tuple", "mutable", "immutable"],
                "Mention mutability: lists are mutable, tuples are immutable.",
                "A list is mutable, so its elements can be changed after creation. A tuple is immutable, so its elements cannot be changed. Both are ordered collections.",
            ),
            (
                ("global interpreter lock", "gil"),
                ["gil", "thread", "bytecode", "cpu"],
                "Explain that CPython's GIL allows one thread at a time to execute Python bytecode, limiting CPU-bound threading.",
                "In CPython, the GIL prevents multiple threads from executing Python bytecode simultaneously. Threads can still help with I/O-bound work, while multiprocessing is often better for CPU-bound work.",
            ),
            (
                ("rest", "soap"),
                ["rest", "soap", "http", "xml"],
                "Compare REST as an architectural style using HTTP resources with SOAP as a protocol commonly using XML envelopes.",
                "REST is an architectural style commonly using HTTP methods and resource-oriented URLs. SOAP is a protocol built around structured XML messages and formal contracts.",
            ),
        ]
        for needles, expected, weakness, improved in factual_checks:
            if all(n in q for n in needles) or any(n in q for n in needles):
                normalized_answer = re.sub(r"[^a-z0-9 ]", " ", a)
                aliases = {
                    "lifo": ("lifo", "last in first out", "last item added is removed first"),
                    "fifo": ("fifo", "first in first out", "first item added is removed first"),
                    "bytecode": ("bytecode", "byte code"),
                    "cpu": ("cpu", "processor", "compute bound"),
                    "mutable": ("mutable", "can be changed", "can change"),
                    "immutable": ("immutable", "cannot be changed", "cannot change"),
                    "xml": ("xml", "extensible markup language"),
                }
                matched = sum(
                    1 for token in expected
                    if any(phrase in normalized_answer for phrase in aliases.get(token, (token,)))
                )
                score = 18 + matched * 14
                if length >= 12:
                    score += min(8, (length - 11) // 5)
                if any(x in a for x in ["example", "for instance", "such as", " like a ", " e.g."]):
                    score += 7
                if any(x in a for x in ["because", "therefore", "which means", "so that"]):
                    score += 6
                if matched == len(expected):
                    score += 8
                if any(x in a for x in ["however", "whereas", "while", "on the other hand"]):
                    score += 5
                score = min(100, score)
                if matched <= 1:
                    score = min(score, 40)
                strengths = f"You covered {matched} of {len(expected)} key points." if matched else "You attempted the question directly, but the answer needs more relevant detail."
                return {
                    "score": score,
                    "strengths": strengths,
                    "weaknesses": weakness,
                    "improved_answer": improved,
                }

        # Generic but answer-sensitive rubric: topic coverage, enough detail,
        # evidence, reasoning, and a clear sequence each contribute separately.
        lower_q = q
        cues = []
        if "yourself" in lower_q or "introduction" in lower_q:
            cues = [["student", "graduate", "education", "degree"], ["project", "internship", "experience", "skill"], ["role", "goal", "interest", "contribute"]]
        elif "team" in lower_q or "teammate" in lower_q:
            cues = [["team", "teammate", "colleague", "group"], ["problem", "challenge", "task", "goal"], ["result", "resolved", "delivered", "learned"]]
        elif "strength" in lower_q:
            cues = [["strength", "strong"], ["example", "project", "instance"], ["result", "impact", "improved", "helped"]]
        elif "challenge" in lower_q or "pressure" in lower_q:
            cues = [["challenge", "problem", "pressure", "obstacle"], ["action", "decided", "approach", "step"], ["result", "solved", "learned", "improved"]]
        elif "project" in lower_q or "role" in lower_q:
            cues = [["project", "role", "application", "system"], ["built", "designed", "implemented", "contributed"], ["result", "user", "performance", "impact"]]
        else:
            stop = {"what", "which", "when", "where", "why", "who", "how", "would", "could", "should", "does", "your", "you", "the", "and", "for", "with", "from", "that", "this", "have", "about", "into", "between", "explain", "describe", "tell", "difference", "used", "use", "one", "are", "is"}
            terms = [w for w in re.findall(r"[a-z0-9+#]+", q) if len(w) > 2 and w not in stop]
            cues = [[word] for word in dict.fromkeys(terms[:4])]
        cue_hits = sum(1 for group in cues if any(term in a for term in group))
        coverage = cue_hits / max(1, len(cues))
        length_score = min(15, round(length * 0.45))
        evidence = any(w in a for w in ["example", "for instance", "project", "built", "implemented", "measured", "result"])
        reasoning = any(w in a for w in ["because", "therefore", "so that", "which means", "as a result"])
        structure = any(w in a for w in ["first", "then", "finally", "situation", "task", "action", "result"])
        score = 18 + round(coverage * 42) + length_score + (12 if evidence else 0) + (8 if reasoning else 0) + (5 if structure else 0)
        score = min(100, score)
        if coverage == 0:
            score = min(score, 45)
        strengths = f"Your answer covered {cue_hits} of {len(cues)} question-specific points" + (" and included an example." if evidence else ".")
        missing_note = " Address the question's key points more directly." if coverage < 0.67 else ""
        evidence_note = " Add a concrete example with your own actions and result." if not evidence else ""
        reasoning_note = " Explain why you chose that approach." if not reasoning else ""
        weaknesses = (missing_note + evidence_note + reasoning_note).strip() or "Good coverage. Tighten the answer and make your result or impact explicit."
        improved = answer.strip() + " Tip: structure it as Definition → Explanation → Example → Impact."
        return {
            "score": score,
            "strengths": strengths,
            "weaknesses": weaknesses,
            "improved_answer": improved,
        }


ai_service = AIService()
