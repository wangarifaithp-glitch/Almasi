"""Add server-scored module quizzes and staff-only facilitator guides.

Revision ID: 20261027_0001
Revises: 016c1f4bac9a
Create Date: 2026-10-27
"""

from datetime import UTC, datetime

from alembic import op
import sqlalchemy as sa

revision = "20261027_0001"
down_revision = "016c1f4bac9a"
branch_labels = None
depends_on = None

REVIEW_NOTE = (
    "Draft supplementary material. Requires human curriculum, safeguarding, "
    "and biblical review before use."
)

MODULE_SUPPLEMENTS = (
    {
        "week": 1,
        "focus": "identity, confidence, and self-worth",
        "guide_notes": [
            "Separate a learner's inherent dignity from grades, appearance, possessions, or popularity.",
            "Model balanced self-talk that acknowledges a difficulty and identifies a next step.",
            "Do not ask learners to disclose painful experiences; use fictional examples and allow passing.",
        ],
        "discussion": [
            "How can effort be recognised without making achievement a measure of a person's worth?",
            "What is a kind and truthful response to a mistake?",
            "When should a trusted adult help address teasing or exclusion?",
        ],
        "activity": "Strengths shield: learners privately choose strengths, values, and one growth goal; sharing is optional.",
        "quiz": [
            ("What determines a person's dignity?", ["Grades and awards", "Appearance", "Their inherent worth; it is not earned", "Popularity"], 2, "A result or appearance does not determine whether someone deserves dignity and respect."),
            ("A learner receives a low mark. Which response is most balanced?", ["I am a failure.", "The mark shows what I can practise next; it does not define me.", "I should stop trying.", "Other learners are the problem."], 1, "A mark can guide learning without defining a person's worth."),
            ("What can confidence include?", ["Never feeling nervous", "Being louder than everyone", "Trying, learning, and asking for help", "Always being right"], 2, "Confidence can include taking a step while nervous and seeking support."),
            ("What is a helpful response to repeated teasing?", ["Keep it secret forever", "Blame yourself", "Tell a trusted adult and seek support", "Tease someone else"], 2, "Ongoing teasing should be addressed with support from a trusted adult."),
            ("Which is balanced self-talk after a mistake?", ["I can notice what happened and choose one thing to practise.", "I never do anything right.", "It does not matter what I do.", "Everyone is against me."], 0, "Balanced self-talk is truthful and leaves room for learning and a next step."),
        ],
    },
    {
        "week": 2,
        "focus": "comparison, envy, and personal growth",
        "guide_notes": [
            "Normalize comparison feelings without shaming learners for envy or disappointment.",
            "Discuss how selected social-media posts omit context; avoid demonising technology or peers.",
            "Help learners turn a comparison into a self-directed, realistic goal.",
        ],
        "discussion": [
            "What parts of another person's life might not be visible in a photograph or post?",
            "How can someone celebrate a friend's success while caring for their own disappointment?",
            "What is one useful next step when comparison points to a skill you want to build?",
        ],
        "activity": "Comparison-to-goal cards: use fictional scenarios to identify the feeling, the underlying wish, and a controllable next step.",
        "quiz": [
            ("Why can comparing your whole life to a social-media post be misleading?", ["Posts always show every detail", "Posts may show selected moments without context", "Everyone has identical circumstances", "Online images cannot affect feelings"], 1, "A post is a selected moment and may omit effort, difficulties, or context."),
            ("You feel disappointed that a friend won an award. What is a constructive response?", ["Spread rumours", "Celebrate your friend and identify a goal for yourself", "Pretend you do not care", "Give up on your interests"], 1, "You can celebrate another person and still make a constructive plan for yourself."),
            ("What can envy sometimes help you notice?", ["That someone else must lose", "A skill or opportunity you hope to pursue", "That you are a bad person", "That effort is pointless"], 1, "A feeling can offer information about something you value or hope to develop."),
            ("Which goal is most helpful after comparing public-speaking skills?", ["Become perfect tomorrow", "Practise one short introduction with support", "Avoid speaking forever", "Copy another learner exactly"], 1, "A small, realistic practice goal supports growth without demanding perfection."),
            ("Does another person's success reduce your worth?", ["Yes, success is limited to one person", "Only if you are disappointed", "No, their success does not determine your worth", "Only online"], 2, "Another person's achievement does not decide your value or future possibilities."),
        ],
    },
    {
        "week": 3,
        "focus": "emotional awareness and respectful expression",
        "guide_notes": [
            "Teach that feelings are signals, not commands, diagnoses, or proof that a feared thought is true.",
            "Offer several regulation choices; breathing is optional and should never be forced.",
            "If a learner indicates immediate danger or persistent distress, follow local safeguarding procedures and involve the designated trusted adult.",
        ],
        "discussion": [
            "How can the body signal that an emotion is becoming strong?",
            "How can someone express anger without harming themselves or another person?",
            "Who could a young person approach when distress does not ease?",
        ],
        "activity": "Feelings-to-needs map: fictional characters identify a feeling, body signal, safe response, and possible support person.",
        "quiz": [
            ("What is a useful way to understand emotions?", ["They are commands", "They are signals that deserve attention", "They prove every thought is true", "They should always be hidden"], 1, "Emotions can signal that something matters, while still needing thoughtful interpretation."),
            ("Feeling angry means a person must hurt someone.", ["True", "False", "It depends on popularity", "Only at school"], 1, "A feeling is not a command; a person can choose a safe response."),
            ("What can an 'I' statement do?", ["Blame and insult", "Describe an experience and make a respectful request", "Guarantee agreement", "End every conflict immediately"], 1, "An 'I' statement can explain an experience and request without attacking."),
            ("Which may be a body signal of emotion?", ["Tight chest or fast heartbeat", "A final diagnosis", "Proof that a thought is true", "A guarantee of danger"], 0, "Body changes can accompany emotions but do not by themselves prove what is happening."),
            ("When should someone seek extra support?", ["Only after every other person agrees", "When distress persists or safety is a concern", "Never; faith means coping alone", "Only when they can explain everything"], 1, "Persistent distress or safety concerns are reasons to contact a trusted adult or professional."),
        ],
    },
    {
        "week": 4,
        "focus": "coping with stress and seeking support",
        "guide_notes": [
            "Present coping strategies as options, not cures or substitutes for adult support.",
            "Distinguish ordinary stress from unsafe situations that require immediate help.",
            "Do not imply that prayer or faith requires someone to tolerate harm or avoid professional care.",
        ],
        "discussion": [
            "Which small actions can make a stressful task feel more manageable?",
            "How can a learner ask for help before feeling overwhelmed?",
            "What is the difference between a hard task and an unsafe situation?",
        ],
        "activity": "Pause-plan-practise: groups use a fictional school-stress scenario to pause, identify choices, and rehearse asking for help.",
        "quiz": [
            ("What is a helpful first response when stress feels overwhelming?", ["Ignore every warning sign", "Pause, notice what is happening, and consider a safe next step", "Make a major decision immediately", "Blame yourself"], 1, "A pause can help someone identify a manageable, safe next step."),
            ("Breaking a large task into smaller steps can:", ["Make every problem disappear", "Make the task easier to approach", "Remove the need for rest", "Guarantee a perfect result"], 1, "Smaller steps can make a task more manageable, though they do not solve every difficulty."),
            ("When a situation is unsafe, a learner should:", ["Keep it private", "Seek help from a trusted adult or emergency support", "Wait until the next lesson", "Use a calming exercise instead of getting help"], 1, "Safety concerns call for appropriate adult or emergency help, not coping techniques alone."),
            ("Asking for help is:", ["A sign of failure", "A responsible option when support is needed", "Only allowed after trying everything", "A way to avoid learning"], 1, "Seeking support is a responsible coping choice."),
            ("Faith and coping support are best understood as:", ["Faith means never feeling stress", "Prayer can accompany, not replace, practical and professional help", "Only one coping method is acceptable", "People must handle distress alone"], 1, "Faith practices may accompany practical help and professional care when needed."),
        ],
    },
    {
        "week": 5,
        "focus": "recognizing and responding to peer pressure",
        "guide_notes": [
            "Use realistic, non-graphic peer-pressure scenarios and let learners pass on role-play.",
            "Teach a pause-and-check routine that includes safety, values, and trusted advice.",
            "Avoid framing a learner as responsible for another person's coercive or harmful behavior.",
        ],
        "discussion": [
            "What signs can show that a request is becoming pressure?",
            "What options are available when saying no directly feels unsafe?",
            "How can friends support a decision without controlling one another?",
        ],
        "activity": "Choice-map role-play: in fictional scenarios, practise pausing, naming pressure, selecting a response, and identifying support.",
        "quiz": [
            ("Which may be a sign of peer pressure?", ["A friend accepts your choice", "Someone threatens exclusion unless you comply", "You consider advice calmly", "You choose after reflecting"], 1, "Threats or conditional acceptance can signal coercive pressure."),
            ("What can help before making a pressured decision?", ["Pause and consider safety, values, and options", "Agree immediately", "Assume the group is always right", "Keep danger secret"], 0, "Pausing creates room to assess the request and choose safely."),
            ("If refusing directly might be unsafe, what can a learner do?", ["Prioritize getting safe and contact a trusted adult", "Stay to prove courage", "Challenge the person alone", "Promise secrecy"], 0, "Safety comes first; getting away and seeking trusted help are valid."),
            ("A respectful friend should:", ["Threaten you into agreeing", "Allow you to make a thoughtful choice", "Demand private information", "Make your decision for you"], 1, "Supportive friends respect boundaries and independent choices."),
            ("Who is a good person to consult about confusing or unsafe pressure?", ["A trusted adult", "Only the person applying pressure", "An unknown online contact", "Nobody"], 0, "A trusted adult can help assess safety and options."),
        ],
    },
    {
        "week": 6,
        "focus": "assertive communication and personal boundaries",
        "guide_notes": [
            "Explain that boundaries may be spoken, physical, emotional, or digital and can differ between people.",
            "Do not teach that a refusal must be polite, explained, or repeated when safety is at risk.",
            "If a boundary is ignored, help-seeking is appropriate; the person whose boundary was crossed is not to blame.",
        ],
        "discussion": [
            "What are some everyday examples of a boundary?",
            "How can someone respect another person's no?",
            "What can a learner do if a boundary is ignored or they feel unsafe?",
        ],
        "activity": "Boundary phrase practice: choose or adapt short phrases for fictional school, friendship, and online situations; passing is welcome.",
        "quiz": [
            ("A boundary is:", ["A way to describe what feels acceptable or safe", "A rule that controls everyone", "A promise to explain everything", "A punishment"], 0, "Boundaries communicate personal limits and needs."),
            ("Does someone need a long explanation before saying no?", ["Yes, always", "No; a brief no can be enough", "Only to a friend", "Only online"], 1, "A person is not required to provide a lengthy explanation for a boundary."),
            ("What should you do when another person states a boundary?", ["Respect it", "Ask repeatedly until they change it", "Share it publicly", "Treat it as a joke"], 0, "Respecting other people's boundaries is part of safe relationships."),
            ("If a person ignores your boundary and you feel unsafe, what is a good next step?", ["Handle it alone", "Move toward safety and tell a trusted adult", "Keep the secret", "Blame yourself"], 1, "Safety and trusted support matter when a boundary is ignored."),
            ("Is a person responsible for someone else's choice to violate a boundary?", ["Yes, the person who said no", "No, the person choosing to cross it is responsible", "Only if they did not explain enough", "It depends on popularity"], 1, "The person who chooses to cross a boundary is responsible for that choice."),
        ],
    },
    {
        "week": 7,
        "focus": "bodily dignity, personal safety, and help-seeking",
        "guide_notes": [
            "Use age-appropriate, non-graphic language about bodily autonomy, privacy, and consent.",
            "Make clear that a learner can seek help even if they froze, felt confused, or could not say no.",
            "Follow local child-protection rules immediately for a disclosure or current safety concern; do not promise secrecy or investigate in the group.",
        ],
        "discussion": [
            "What does it mean to treat every person's body with dignity?",
            "Which trusted adults or services could help if a young person feels unsafe?",
            "How can a peer listen supportively without asking for details?",
        ],
        "activity": "Trusted-support map: privately identify safe adults and practice a simple help-seeking phrase using a fictional example.",
        "quiz": [
            ("Which statement reflects bodily dignity?", ["People deserve respect and safety", "A person must accept unwanted contact", "Boundaries do not matter with friends", "A young person is responsible for another's harm"], 0, "Every person deserves dignity, respect, and safety."),
            ("If a young person feels unsafe, what should they do?", ["Tell a trusted adult or appropriate local support", "Keep quiet to avoid trouble", "Investigate alone", "Post identifying details online"], 0, "A trusted adult or appropriate service can help address safety."),
            ("A young person who freezes during a frightening situation is:", ["To blame", "Still deserving of support; freezing does not mean consent", "Required to handle it alone", "Responsible for another person's actions"], 1, "Freezing is not consent and does not make the young person responsible for harm."),
            ("How should a facilitator respond to a safety disclosure?", ["Promise absolute secrecy", "Listen calmly and follow safeguarding procedures", "Ask the group to investigate", "Demand every detail"], 1, "Facilitators should listen, avoid promises of secrecy, and use safeguarding procedures."),
            ("What is a supportive response to a peer who hints they feel unsafe?", ["Ask for graphic details", "Listen without pressure and help them reach a trusted adult", "Tell them to forget it", "Share their story with friends"], 1, "Support without pressure and connect them with appropriate trusted help."),
        ],
    },
    {
        "week": 8,
        "focus": "digital privacy, online safety, and evaluating content",
        "guide_notes": [
            "Focus on privacy, consent, trusted-adult help, and reporting; avoid victim-blaming.",
            "Do not ask learners to reveal accounts, passwords, private messages, or personal online experiences.",
            "Encourage pausing before sharing and using platform reporting/blocking tools with adult support.",
        ],
        "discussion": [
            "What information should remain private online?",
            "How can a learner check whether a post is reliable or designed to provoke?",
            "What steps can help when an online interaction feels unsafe?",
        ],
        "activity": "Digital decision cards: sort fictional posts into pause, verify, protect privacy, or seek trusted help.",
        "quiz": [
            ("Which information should generally be kept private online?", ["Home address and passwords", "A public library's opening hours", "A fictional story", "A public weather report"], 0, "Addresses and passwords can expose someone to risk and should not be shared."),
            ("A surprising online claim should be:", ["Shared immediately", "Checked with reliable sources before sharing", "Believed because it is popular", "Sent with personal details"], 1, "Pause and verify claims with reliable sources before spreading them."),
            ("If an online contact pressures a learner for private images or details, they should:", ["Send them to keep the contact", "Stop responding and get help from a trusted adult", "Move to a more secret channel", "Share the contact's details publicly"], 1, "Pressure for private material is a reason to stop and involve a trusted adult."),
            ("Before sharing another person's photo, it is important to:", ["Get their permission", "Assume permission", "Add their location", "Ask strangers"], 0, "Respect privacy and obtain permission before sharing someone's image."),
            ("Blocking or reporting an unsafe account can be combined with:", ["Telling a trusted adult", "Keeping all risk secret", "Meeting the person alone", "Sharing passwords"], 0, "Platform tools and trusted adult support can be used together."),
        ],
    },
    {
        "week": 9,
        "focus": "aspirations, goal setting, and future pathways",
        "guide_notes": [
            "Help learners see several possible pathways; avoid promising that every goal will happen.",
            "Separate an aspiration from the first practical step and any support or resources needed.",
            "Value rest, flexibility, and changing a goal when circumstances change.",
        ],
        "discussion": [
            "What makes a goal meaningful to the learner rather than chosen only to please others?",
            "How can a large hope be divided into achievable steps?",
            "What can someone do when a plan needs to change?",
        ],
        "activity": "Future pathways map: learners choose a fictional or personal low-risk goal, map steps, supports, and a flexible alternative.",
        "quiz": [
            ("A helpful first step toward a large goal is to:", ["Break it into manageable actions", "Expect instant success", "Avoid asking questions", "Give up if the first plan changes"], 0, "Smaller actions make a larger goal easier to begin and review."),
            ("A realistic goal should consider:", ["Available time and support", "Only what peers are doing", "A guarantee of success", "A fixed path with no changes"], 0, "Planning should account for current circumstances and available support."),
            ("If a goal becomes unsuitable, a learner can:", ["Never change it", "Review the goal and choose another path", "Conclude they have no future", "Hide the difficulty"], 1, "Changing a plan can be a thoughtful response to new information."),
            ("Who can help a young person explore education or career pathways?", ["A trusted adult, teacher, or mentor", "An unknown person requesting private details", "Only social-media influencers", "No one"], 0, "Trusted adults and educators can help identify realistic options and resources."),
            ("A person's worth depends on achieving every goal.", ["True", "False", "Only when others approve", "Only when the goal is difficult"], 1, "A goal is a direction for growth; it does not determine a person's worth."),
        ],
    },
    {
        "week": 10,
        "focus": "responsibility, effort, planning, and rest",
        "guide_notes": [
            "Discuss responsibility as a learnable practice, not a measure of a learner's value.",
            "Include household, school, and community responsibilities without assuming all learners have the same resources.",
            "Balance planning and effort with sleep, rest, safety, and asking for help.",
        ],
        "discussion": [
            "Which routines make a busy week more manageable?",
            "How can someone respond constructively after missing a responsibility?",
            "Why are rest and help part of responsible planning?",
        ],
        "activity": "Weekly plan challenge: use a fictional learner's schedule to prioritize tasks, include rest, and adapt for an unexpected change.",
        "quiz": [
            ("What can a simple weekly plan help with?", ["Remembering priorities and making time", "Guaranteeing nothing changes", "Removing the need for sleep", "Comparing learners"], 0, "A plan can help organize priorities, though unexpected changes still happen."),
            ("If you miss a responsibility, a constructive response is to:", ["Hide it and blame someone", "Acknowledge it, repair what you can, and plan a next step", "Decide you are worthless", "Give up every other task"], 1, "Taking responsibility includes acknowledging, repairing, and learning where possible."),
            ("Rest is:", ["Always laziness", "Part of a healthy and sustainable routine", "Only for adults", "Unnecessary when goals matter"], 1, "Rest supports wellbeing and sustainable effort."),
            ("When a schedule changes unexpectedly, it can help to:", ["Reprioritize and ask for help if needed", "Assume all goals are ruined", "Skip meals and sleep", "Blame yourself"], 0, "Flexible planning helps people respond to changes without self-blame."),
            ("Responsibility makes a person's worth:", ["Higher if perfect", "Lower after mistakes", "Not dependent on perfect performance", "Dependent on never needing help"], 2, "Responsibility is a practice; it does not decide personal worth."),
        ],
    },
    {
        "week": 11,
        "focus": "healthy friendship, trust, and boundaries",
        "guide_notes": [
            "Explore friendship through respect, trust, reciprocity, and room for boundaries.",
            "Avoid labeling learners or peers as wholly good or bad based on one conflict.",
            "For bullying, threats, or unsafe control, recommend trusted adult help rather than handling it alone.",
        ],
        "discussion": [
            "What does mutual respect look like in a friendship?",
            "How can friends disagree while maintaining boundaries?",
            "What signs suggest a trusted adult should help?",
        ],
        "activity": "Friendship traffic lights: fictional behaviors are sorted into supportive, needs a conversation, or seek adult help.",
        "quiz": [
            ("A healthy friendship generally includes:", ["Respect and room for boundaries", "Pressure to share every secret", "One person controlling all choices", "Fear of saying no"], 0, "Respect and boundaries help relationships remain safe and mutual."),
            ("A friend says no to an invitation. A respectful response is to:", ["Accept their answer", "Threaten to end the friendship", "Keep asking until they agree", "Share their private reason"], 0, "Respecting a no supports trust and personal choice."),
            ("What should someone do about repeated bullying or threats?", ["Handle it alone", "Tell a trusted adult and seek support", "Retaliate", "Keep it secret"], 1, "Repeated bullying or threats warrant trusted adult support."),
            ("Conflict in a friendship always means the friendship is unsafe.", ["True", "False", "Only if it happens in public", "Only if both people agree"], 1, "Disagreement can happen; patterns of control, harm, or ignored boundaries require attention."),
            ("A supportive friend should:", ["Make every decision for you", "Encourage safe choices and respect limits", "Demand passwords", "Discourage trusted adult help"], 1, "Support includes respect, safety, and room to seek help."),
        ],
    },
    {
        "week": 12,
        "focus": "growth, everyday leadership, and a personal plan",
        "guide_notes": [
            "Invite reflection on growth without requiring learners to describe private or painful experiences.",
            "Celebrate process, support-seeking, kindness, and learning, not only visible achievements.",
            "Close with a practical support plan and reinforce where safeguarding help is available.",
        ],
        "discussion": [
            "What is one idea or skill you may carry forward?",
            "Who can support your next step after this programme?",
            "How can leadership make a group safer and more welcoming?",
        ],
        "activity": "Growth portfolio: learners select a skill, a next step, and a support person; sharing remains optional.",
        "quiz": [
            ("What is a useful way to reflect on progress?", ["Notice learning and choose a next step", "Compare yourself only with the highest achiever", "Require perfection", "Ignore support received"], 0, "Reflection can recognize learning and inform a manageable next step."),
            ("Everyday leadership can include:", ["Listening and helping a group act respectfully", "Controlling every decision", "Being the loudest person", "Never asking for help"], 0, "Leadership can be expressed through respectful, practical actions."),
            ("If a learner needs support after the programme, they should:", ["Use a trusted adult or appropriate service", "Assume the programme is the only help", "Keep safety concerns secret", "Rely on an unknown online contact"], 0, "Support remains available through trusted adults and appropriate local services."),
            ("A personal growth plan should be:", ["Flexible and realistic", "A promise never to make mistakes", "Based only on another person's goals", "Kept even when unsafe"], 0, "A useful plan can adapt to needs and circumstances."),
            ("A person's value depends on how much visible leadership they show.", ["True", "False", "Only in a group", "Only when they volunteer"], 1, "People have dignity regardless of visibility, achievement, or leadership role."),
        ],
    },
)


def _guide(module: dict[str, object]) -> dict[str, object]:
    focus = str(module["focus"])
    activity = str(module["activity"])
    return {
        "review_status": REVIEW_NOTE,
        "session_length_minutes": 210,
        "facilitator_objective": f"Help learners explore {focus} using safe, age-appropriate discussion and practical rehearsal.",
        "preparation": [
            "Review the learner lesson, quiz, and local safeguarding/contact procedures before the session.",
            "Prepare paper, pens, and fictional scenario cards; do not require personal disclosures.",
            "Arrange a private, accessible way for a learner to ask for support after the session.",
        ],
        "teaching_notes": module["guide_notes"],
        "discussion_questions": module["discussion"],
        "practical_activities": [activity],
        "session_structure": [
            {"minutes": 20, "segment": "Welcome and group agreements", "facilitator_notes": "Set expectations for respect, privacy, passing, and seeking help."},
            {"minutes": 20, "segment": "Opening reflection and Bible reference", "facilitator_notes": "Introduce the module's reference and invite observation; avoid pressuring anyone to share beliefs or personal experiences."},
            {"minutes": 35, "segment": "Teach and model", "facilitator_notes": "Teach the key ideas with fictional, age-appropriate examples and check understanding."},
            {"minutes": 10, "segment": "Break", "facilitator_notes": "Offer water and a quiet option."},
            {"minutes": 40, "segment": "Practical activity", "facilitator_notes": activity},
            {"minutes": 30, "segment": "Guided discussion", "facilitator_notes": "Use the prompts; allow learners to pass and do not request identifying details."},
            {"minutes": 10, "segment": "Break", "facilitator_notes": "Offer a calm transition and private check-in option."},
            {"minutes": 30, "segment": "Skills practice and quiz", "facilitator_notes": "Practise a safe next step, then allow learners to complete the separate module quiz."},
            {"minutes": 15, "segment": "Reflection and close", "facilitator_notes": "Invite a private takeaway and identify trusted support; sharing is optional."},
        ],
        "safeguarding": [
            "Use fictional examples and never require a learner to disclose trauma, abuse, or private safety information.",
            "Do not promise confidentiality when a learner's safety may be at risk; follow local child-protection procedures.",
            "Listen calmly, avoid investigating a disclosure in the group, and promptly contact the designated safeguarding lead.",
            "The facilitator guide is staff-only and must not be presented as clinical or legal advice.",
        ],
    }


def upgrade() -> None:
    op.add_column(
        "learning_modules",
        sa.Column("facilitator_guide", sa.JSON(), nullable=True),
    )
    op.create_table(
        "module_quiz_questions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("module_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("prompt", sa.String(length=2000), nullable=False),
        sa.Column("options", sa.JSON(), nullable=False),
        sa.Column("correct_option", sa.Integer(), nullable=False),
        sa.Column("explanation", sa.String(length=2000), nullable=False),
        sa.ForeignKeyConstraint(["module_id"], ["learning_modules.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("module_id", "position", name="uq_quiz_module_position"),
        sa.CheckConstraint("position BETWEEN 1 AND 7", name="ck_quiz_question_position"),
        sa.CheckConstraint("correct_option BETWEEN 0 AND 3", name="ck_quiz_correct_option"),
    )
    op.create_index("ix_module_quiz_questions_module_id", "module_quiz_questions", ["module_id"])
    op.create_table(
        "learner_quiz_attempts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("learner_id", sa.Integer(), nullable=False),
        sa.Column("module_id", sa.Integer(), nullable=False),
        sa.Column("answers", sa.JSON(), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("total_questions", sa.Integer(), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["learner_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["module_id"], ["learning_modules.id"], ondelete="CASCADE"),
        sa.CheckConstraint("score BETWEEN 0 AND total_questions", name="ck_quiz_attempt_score"),
        sa.CheckConstraint("total_questions BETWEEN 5 AND 7", name="ck_quiz_attempt_total"),
    )
    op.create_index("ix_learner_quiz_attempts_learner_id", "learner_quiz_attempts", ["learner_id"])
    op.create_index("ix_learner_quiz_attempts_module_id", "learner_quiz_attempts", ["module_id"])

    bind = op.get_bind()
    now = datetime.now(UTC).replace(tzinfo=None)
    modules = sa.table(
        "learning_modules",
        sa.column("id", sa.Integer()),
        sa.column("week_number", sa.Integer()),
        sa.column("facilitator_guide", sa.JSON()),
        sa.column("is_published", sa.Boolean()),
        sa.column("reviewed_at", sa.DateTime(timezone=True)),
        sa.column("reviewed_by_id", sa.Integer()),
        sa.column("updated_at", sa.DateTime(timezone=True)),
    )
    questions = sa.table(
        "module_quiz_questions",
        sa.column("module_id", sa.Integer()),
        sa.column("position", sa.Integer()),
        sa.column("prompt", sa.String(2000)),
        sa.column("options", sa.JSON()),
        sa.column("correct_option", sa.Integer()),
        sa.column("explanation", sa.String(2000)),
    )
    for supplement in MODULE_SUPPLEMENTS:
        module = bind.execute(
            sa.select(modules.c.id, modules.c.week_number).where(
                modules.c.week_number == supplement["week"]
            )
        ).one_or_none()
        if module is None:
            continue
        bind.execute(
            modules.update()
            .where(modules.c.id == module.id)
            .values(
                facilitator_guide=_guide(supplement),
                is_published=False,
                reviewed_at=None,
                reviewed_by_id=None,
                updated_at=now,
            )
        )
        bind.execute(
            sa.text(
                "DELETE FROM module_quiz_questions WHERE module_id = :module_id"
            ),
            {"module_id": module.id},
        )
        op.bulk_insert(
            questions,
            [
                {
                    "module_id": module.id,
                    "position": position,
                    "prompt": prompt,
                    "options": list(options),
                    "correct_option": correct_option,
                    "explanation": explanation,
                }
                for position, (prompt, options, correct_option, explanation)
                in enumerate(supplement["quiz"], start=1)
            ],
        )
    with op.batch_alter_table("learning_modules") as batch_op:
        batch_op.alter_column(
            "facilitator_guide",
            existing_type=sa.JSON(),
            nullable=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    attempts = bind.execute(sa.text("SELECT COUNT(*) FROM learner_quiz_attempts")).scalar_one()
    if attempts:
        raise RuntimeError(
            "Cannot downgrade after learner quiz attempts have been recorded."
        )
    op.drop_index("ix_learner_quiz_attempts_module_id", table_name="learner_quiz_attempts")
    op.drop_index("ix_learner_quiz_attempts_learner_id", table_name="learner_quiz_attempts")
    op.drop_table("learner_quiz_attempts")
    op.drop_index("ix_module_quiz_questions_module_id", table_name="module_quiz_questions")
    op.drop_table("module_quiz_questions")
    op.drop_column("learning_modules", "facilitator_guide")
