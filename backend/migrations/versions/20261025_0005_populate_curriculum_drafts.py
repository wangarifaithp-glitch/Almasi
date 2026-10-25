"""Populate learner-ready curriculum drafts from the supplied manual.

Revision ID: 20261025_0005
Revises: 20261025_0004
Create Date: 2026-10-25
"""

from alembic import op
import sqlalchemy as sa

revision = "20261025_0005"
down_revision = "20261025_0004"
branch_labels = None
depends_on = None

REFLECTION_PROMPTS = [
    "What is one idea from this lesson that you understand more clearly now?",
    "What is one realistic action a girl your age could try this week?",
    "What could make that action difficult, and who or what could help?",
    "What is one important point you would want a friend to understand about this topic?",
]

MODULE_CONTENT = (
    {
        "week": 1,
        "reference": "Psalm 139:14",
        "focus": "Identity, confidence and self-worth",
        "objectives": [
            "Explain the difference between personal worth and performance, popularity or appearance.",
            "Identify strengths, values and areas for growth without putting others down.",
            "Practise replacing cruel self-talk with truthful, balanced self-talk.",
            "Describe how to respond to teasing or exclusion and where to seek support.",
        ],
        "lesson": (
            "Psalm 139:14 invites reflection on being known by God. A person deserves "
            "dignity, safety and respectful treatment; worth is not a prize earned by "
            "appearance, marks, popularity, money or perfection. Achievement matters "
            "for learning, but it does not decide whether someone deserves respect. "
            "A poor mark can show what needs practice; it does not make a learner a failure.\n\n"
            "Identity is wider than one label. Values, interests, culture, faith, "
            "relationships, skills, hopes and choices all help describe a person. "
            "Confidence does not mean being loud or never feeling afraid. It can mean "
            "trying, asking for help, learning and recovering after a mistake.\n\n"
            "Self-talk is how we explain events to ourselves. Notice a harsh thought, "
            "check whether it is completely true and fair, then replace it with a "
            "truthful statement that leaves room for a next step. Other people’s "
            "mocking or exclusion can hurt, but an insult is not proof that it is true. "
            "Faith does not require feeling happy about every part of life or erase "
            "difficulty; a trusted adult can help when teasing or exclusion continues."
        ),
        "questions": [
            "How might a girl respond if classmates call her slow because she needs more time to understand a lesson?",
            "What could you say to a girl who believes she is less valuable because she cannot afford the clothes her friends wear?",
            "If a learner receives a poor mark, how can she acknowledge the result without defining herself as a failure?",
            "What could a quiet girl do if others assume that her silence means she has nothing useful to contribute?",
            "How should a group respond when one girl makes a joke about another girl’s appearance and everyone laughs?",
        ],
        "assignment": (
            "For seven days, privately record one strength or helpful action each day. "
            "Also record one mistake and the lesson it offered. Submit a general lesson "
            "you noticed without names or identifying details."
        ),
    },
    {
        "week": 2,
        "reference": "Galatians 6:4",
        "focus": "Recognising comparison, appreciating differences and turning envy into growth",
        "objectives": [
            "Recognise upward, downward and appearance-based comparison.",
            "Explain how social media and selective information can distort comparison.",
            "Turn envy into information about a personal goal without resentment.",
            "Practise celebrating others while tracking personal progress.",
        ],
        "lesson": (
            "Comparison measures us against another person. It may be useful to learn "
            "a study method from a classmate, but it becomes harmful when another "
            "person’s strengths are treated as proof that we are inferior, or another’s "
            "difficulty as proof that we are superior. Comparison can create envy, "
            "shame, arrogance or pressure to pretend.\n\n"
            "We rarely know another person’s whole life. A photograph, good mark or "
            "new possession may not show the effort, support, difficulties or editing "
            "behind it. Social media often shows selected moments rather than an "
            "entire life. Comparing siblings or classmates can also make people feel "
            "that they are not enough.\n\n"
            "Envy can point to something we want, such as a skill, friendship, "
            "opportunity or recognition. The feeling does not make someone bad; what "
            "matters is the next choice. Turn it into a realistic learning goal, track "
            "your own effort and values, and celebrate another person without shrinking "
            "your own hopes. A friend’s success does not use up the success available "
            "to you."
        ),
        "questions": [
            "What could you do if your best friend receives an award you hoped to win, and you feel both happy for her and disappointed for yourself?",
            "How might you respond when social media makes it look as though everyone else has a better life than yours?",
            "What could a learner say when a relative repeatedly compares her marks with her sibling’s marks?",
            "If you envy another girl’s confidence when speaking in public, how can you turn that feeling into a learning plan?",
            "What would you say to a friend who spreads rumours about a successful girl because she feels jealous?",
        ],
        "assignment": (
            "When comparison appears, privately record what triggered it, what you "
            "think you want, what is and is not in your control, and one constructive "
            "next step. Submit only a general next step, without names or private details."
        ),
    },
    {
        "week": 3,
        "reference": "Psalm 34:18",
        "focus": "Emotional awareness, regulation and respectful expression",
        "objectives": [
            "Name a range of emotions and identify how they show up in body and thoughts.",
            "Distinguish feelings from actions and facts.",
            "Practise safe ways to express anger, sadness, fear, shame and joy.",
            "Know when to seek support from a trusted adult or professional.",
        ],
        "lesson": (
            "Emotions are signals that help us notice what matters. Fear may alert us "
            "to danger, anger may signal an unfairness or crossed boundary, sadness "
            "may follow loss, and joy may come with connection or achievement. "
            "Emotions are not automatically right or wrong, and they do not always "
            "tell the whole story. Feeling rejected does not prove that everyone "
            "rejects you. The goal is to notice feelings and choose a safe, useful response.\n\n"
            "Emotions can appear in the body as a tight chest, fast heartbeat, "
            "stomach discomfort, hot face, tears or restlessness. Thoughts can also "
            "become quick and absolute. A feeling deserves attention, but it is not a "
            "command: someone can feel angry without hurting another person, or afraid "
            "and still ask for help.\n\n"
            "More precise words can help identify what is needed. An “I” statement "
            "can describe an experience and request without attacking someone: “I felt "
            "embarrassed when my answer was laughed at. I would like us to listen "
            "without mocking.” Persistent sadness, hopelessness, major sleep or "
            "appetite changes, or difficulty functioning are reasons to seek a trusted "
            "adult or professional’s support."
        ),
        "questions": [
            "What could you do if you feel so angry after an argument that you want to send a cruel message immediately?",
            "How might you check your assumptions if you feel anxious because two classmates are whispering and looking your way?",
            "What could you say to a trusted adult if you have felt sad and withdrawn for several weeks?",
            "How can you tell a friend you are hurt by her words without insulting her back?",
            "If a friend says “I’m fine,” but seems distressed, how could you show care without pressuring her to explain?",
        ],
        "assignment": (
            "Once a day, use this private check-in: “I feel…; I notice it in my body "
            "as…; I may need…; one safe action is…”. Sharing the record is optional. "
            "Submit a general description of the check-in, not your private feelings."
        ),
    },
    {
        "week": 4,
        "reference": "Matthew 11:28",
        "focus": "Coping with stress, calming skills, resilience and asking for help",
        "objectives": [
            "Recognise common stressors and early signs of overwhelm.",
            "Practise grounding, breathing, problem-solving and support-seeking.",
            "Distinguish what can be changed from what needs help or acceptance.",
            "Build a personal coping plan that includes faith, practical action and trusted people.",
        ],
        "lesson": (
            "Stress is the mind and body responding to a demand, uncertainty or "
            "perceived threat. A manageable level can help us prepare; too much stress "
            "for too long can make concentration, sleep, memory, patience and decisions "
            "harder. Stress may show up as tense muscles, racing thoughts, irritability, "
            "crying, avoiding tasks or losing focus. These signs are not proof of weakness.\n\n"
            "When it feels safe and comfortable, slow breathing with a gentle longer "
            "exhale, feeling your feet on the floor, or naming things you can see can "
            "help settle the body. Then separate a problem into parts: What is the "
            "problem? What is urgent? What can I control? Who can help with what I "
            "cannot manage alone?\n\n"
            "Rest is part of functioning, not a reward only after everything is done. "
            "Prayer, scripture, worship and trusted people may support hope; faith "
            "should not be used to shame someone for feeling stress or needing help. "
            "If an adult is hurting or threatening a young person, seek help from a "
            "trusted adult or appropriate support person."
        ),
        "questions": [
            "What could you do if you have two assignments due, a family responsibility and feel too overwhelmed to begin?",
            "How might you help a friend who is crying after a difficult family situation without trying to solve everything for her?",
            "What should a learner do if the source of her stress is an adult who is hurting or threatening her?",
            "Which coping strategy might help if you are angry before an exam, and how could you tell whether it is helping?",
            "What could you change in your evening routine if scrolling on your phone keeps delaying your sleep?",
        ],
        "assignment": (
            "Try one coping strategy on three different days and privately note "
            "whether it helped, did not help or needs adapting. Identify a trusted "
            "adult before a crisis occurs. Do not include private causes or names in "
            "your submitted summary."
        ),
    },
    {
        "week": 5,
        "reference": "1 Corinthians 15:33",
        "focus": "Influence, belonging, critical thinking and decision-making",
        "objectives": [
            "Identify direct, indirect, spoken and online peer pressure.",
            "Explain why belonging can make pressure difficult to resist.",
            "Use a decision-making process to assess risks and values.",
            "Practise responses and exit plans for unsafe or unwanted situations.",
        ],
        "lesson": (
            "Peer pressure is influence from people in a similar age group that pushes "
            "someone toward a choice. It may be direct or indirect, spoken or online. "
            "Wanting friendship and belonging can make pressure difficult to resist, "
            "but a popular choice is not automatically safe or right.\n\n"
            "Pause and ask: What exactly am I being asked to do? Is it safe and lawful? "
            "Does it fit my values? Who could be harmed? What might happen next? "
            "Preparing a short refusal or exit plan can help when there is pressure. "
            "Friends can also influence one another positively by studying together, "
            "practising a skill or speaking up against bullying.\n\n"
            "If you have already made a harmful choice, shame can make it harder to "
            "ask for help. Stop the harmful action if possible, consider who may have "
            "been affected, seek support and take a responsible step to repair harm."
        ),
        "questions": [
            "What could you say if friends pressure you to skip class and threaten to call you boring if you refuse?",
            "How might you respond if a group chat asks everyone to share an embarrassing photo of another learner?",
            "What could you do if a friend says you must lend her money you cannot afford to lose to prove your loyalty?",
            "How can you tell the difference between a friend encouraging you to try something new and a friend pressuring you?",
            "If you already joined in bullying someone because your friends were doing it, what responsible steps could you take now?",
        ],
        "assignment": (
            "Write three personal values, two refusal phrases and identify two people "
            "you could contact if a situation becomes unsafe. Do not enter anyone’s "
            "name or contact details in your submission."
        ),
    },
    {
        "week": 6,
        "reference": "Proverbs 4:23",
        "focus": "Boundaries, assertive communication and safe refusal",
        "objectives": [
            "Define personal boundaries and explain why they matter.",
            "Distinguish passive, aggressive and assertive communication.",
            "Practise clear refusal phrases and exit strategies.",
            "Understand that consent and safety matter even when the other person is familiar or influential.",
        ],
        "lesson": (
            "A boundary is a limit about what you will accept, share, do or allow "
            "regarding your time, body, belongings, privacy, emotions and values. "
            "Saying no can feel difficult if someone fears disappointing an adult, "
            "losing a friendship or being called rude.\n\n"
            "A passive response hides a boundary; an aggressive response attacks; "
            "an assertive response states a limit clearly and respectfully. When "
            "someone keeps pushing, repeating a short phrase can help avoid being "
            "pulled into a long argument. A refusal may include an alternative for a "
            "harmless request, but when a situation is unsafe, leaving and seeking "
            "help can matter more than explaining.\n\n"
            "Consent and safety matter even when a person is familiar or influential. "
            "Christian kindness does not require tolerating harassment, coercion or "
            "unsafe behaviour. Proverbs 4:23 can frame boundaries as caring for one’s "
            "inner life."
        ),
        "questions": [
            "What could you say if a friend keeps borrowing your belongings without asking and laughs when you object?",
            "How might you respond if someone repeatedly asks for your phone password and says you have nothing to hide if you refuse?",
            "What could you do if saying no to an older person feels unsafe because that person has power over you?",
            "How can you set a boundary when a friend jokes about a private matter you asked her not to share?",
            "If a person ignores your refusal and continues pressuring you, what is your next safe step?",
        ],
        "assignment": (
            "Write one boundary you want to practise, the words you might use, and "
            "a backup action if the person does not respect it. Use a general or "
            "fictional example; do not include private details about an unsafe situation."
        ),
    },
    {
        "week": 7,
        "reference": "1 Corinthians 6:19",
        "focus": "Body dignity, privacy, consent, safe/unsafe touch and disclosure",
        "objectives": [
            "Explain that every person deserves bodily dignity, safety and respect.",
            "Identify personal boundaries, unsafe behaviour, coercion and unsafe secrets.",
            "Practise how to seek help and tell a trusted adult.",
            "Understand that harm is never the child’s fault and that adults are responsible for protecting children.",
        ],
        "lesson": (
            "Every young person deserves bodily dignity, safety and respect. People "
            "may feel differently about hugs, handshakes or hair being touched, and "
            "a boundary should be respected. A situation can feel safe, uncomfortable, "
            "confusing or dangerous. Unwanted touching, sexual comments, pressure to "
            "show private images, or requests to keep unsafe meetings secret are "
            "reasons to seek help.\n\n"
            "Consent is a freely given, informed and specific agreement, and it can "
            "be withdrawn. Silence, fear, threats or pressure are not freely given "
            "consent. A young person is never responsible for an adult’s harmful "
            "behaviour.\n\n"
            "If something feels wrong, move toward safety if possible and tell a "
            "trusted adult. If the first adult does not help and the unsafe behaviour "
            "continues, tell another trusted adult. Do not share private safety-plan "
            "details in answers or reflections."
        ),
        "questions": [
            "What could you do if a relative insists on hugging you even after you say you do not want a hug?",
            "How should a girl respond if an older person gives her gifts and asks her to keep their private meetings secret?",
            "What could you say to a friend who is being pressured to send an intimate image to prove that she loves someone?",
            "If a girl tells you that an adult touched her in a way that made her feel unsafe, what should you do and what should you avoid doing?",
            "What can a learner do if the first adult she tells dismisses her concern and the unsafe behaviour continues?",
        ],
        "assignment": (
            "Complete the private safety plan from the lesson: identify trusted "
            "adults, a safe place, and what to do if the first person does not help. "
            "Keep those details private. For this saved assignment, confirm only "
            "that you completed the plan or need help making it; do not enter names "
            "or locations."
        ),
    },
    {
        "week": 8,
        "reference": "Philippians 4:8",
        "focus": "Digital wellbeing, privacy, cyberbullying, misinformation and online exploitation",
        "objectives": [
            "Explain how online content can affect mood, identity, attention and relationships.",
            "Identify personal information and risky requests that should remain private.",
            "Practise steps for cyberbullying, suspicious contact and misinformation.",
            "Create realistic screen-time and digital-safety boundaries.",
        ],
        "lesson": (
            "Digital spaces can support learning, creativity, friendships, faith and "
            "opportunity. They can also expose people to bullying, scams, misinformation "
            "and unsafe requests. Online content can affect mood, identity, attention "
            "and relationships.\n\n"
            "Posts often show selected moments, filters and posed images, not a whole "
            "life. Protect passwords and private information. Requests for secrecy, "
            "private images or personal details from an unknown account are warning "
            "signs; tell a trusted adult. Cyberbullying can include repeated insults, "
            "threats, rumours, humiliating images or exclusion. Do not forward harmful "
            "material; get help and use platform safety tools with adult support.\n\n"
            "Before believing or sharing a claim, check its source, date and evidence. "
            "A realistic screen-time boundary can protect sleep, learning and "
            "wellbeing without requiring perfection."
        ),
        "questions": [
            "What could you do if a filtered photograph makes you feel that your own face or body is not good enough?",
            "How should you respond if an unknown account asks for your school, location and a private photograph?",
            "What steps could a learner take if a class group chat repeatedly mocks one girl and shares humiliating images?",
            "How can you check whether a dramatic online claim about health or safety is reliable before forwarding it?",
            "What realistic phone boundary could help if scrolling is delaying your homework or sleep?",
        ],
        "assignment": (
            "Review privacy settings with a trusted adult, identify one account or "
            "content type to mute if needed, and practise checking a claim before "
            "sharing it. Do not include usernames, passwords or account details in "
            "your submission."
        ),
    },
    {
        "week": 9,
        "reference": "Jeremiah 29:11",
        "focus": "Hope, strengths, goal-setting, pathways and overcoming barriers",
        "objectives": [
            "Identify interests, values, strengths and possible future directions.",
            "Turn a broad dream into a specific, realistic next step.",
            "Recognise barriers without treating them as proof that a dream is impossible.",
            "Practise seeking information, mentorship and support.",
        ],
        "lesson": (
            "A dream is a future a person hopes to work toward; it might be a career, "
            "skill, family contribution, creative project or community service. "
            "Curiosity, values and strengths can help someone discover possible paths. "
            "A broad hope becomes easier to act on when it is specific, observable "
            "and connected to a realistic next step.\n\n"
            "Barriers may include money, transport, school performance, caregiving "
            "duties, limited internet access, disability or unfair expectations. A "
            "barrier is real, but it is not proof that a dream is impossible. Seek "
            "information, mentors and support, and adjust plans when circumstances "
            "change.\n\n"
            "A setback is information, not a final verdict on the future. Review what "
            "was difficult, identify what can be practised or changed, and consider "
            "another route. Jeremiah 29:11 should be read in its historical context: "
            "it speaks to a community in exile encouraged to seek God and live "
            "faithfully while waiting; it is not a promise that every personal plan "
            "will happen exactly as imagined."
        ),
        "questions": [
            "What first step could you take if you dream of becoming a nurse but do not yet know the subjects or qualifications required?",
            "How could you keep working toward a goal if your family has limited money or internet access?",
            "What might you learn from failing an exam that matters to a future goal?",
            "How could you explore a career if you do not know anyone who works in that field?",
            "What would you say to a girl who believes that her current circumstances mean she has no future options?",
        ],
        "assignment": (
            "Complete one small step toward a goal and record what you learned. If "
            "the step proves difficult, adjust the plan and identify one kind of "
            "support that could help. Keep names and private circumstances out of "
            "your submission."
        ),
    },
    {
        "week": 10,
        "reference": "Proverbs 14:23",
        "focus": "Discipline, time management, accountability, balance and rest",
        "objectives": [
            "Explain responsibility as reliable action and accountability, not perfection.",
            "Break tasks into manageable steps and prioritise realistically.",
            "Practise time planning, reducing distractions and reviewing progress.",
            "Balance work, caregiving, relationships, faith, health and rest.",
        ],
        "lesson": (
            "Responsibility means recognising what is yours to do, making a reasonable "
            "effort, communicating when you cannot complete it, and taking steps to "
            "repair or continue. It does not mean being perfect. Discipline is more "
            "reliable when tasks are small, specific and connected to a routine; "
            "motivation changes from day to day.\n\n"
            "A list can help move tasks out of memory. Notice what is urgent, important, "
            "can wait or needs help. Distractions may come from notifications, noise, "
            "worry, boredom or tiredness; choose a strategy that fits the cause. If a "
            "task is missed, name what happened without denial or self-attack, "
            "communicate honestly and decide on a next step.\n\n"
            "Effort does not guarantee immediate reward, and people do not all have "
            "the same circumstances. Rest supports learning and health. A realistic "
            "plan should include school, responsibilities, relationships, faith, "
            "health and rest."
        ),
        "questions": [
            "What could you change if you regularly begin homework late because you scroll on your phone first?",
            "How might you plan if you have an exam, household chores and a younger sibling who needs help?",
            "What should you do if you realise a deadline will be missed because you do not understand the assignment?",
            "How can you respond responsibly after forgetting a commitment to a friend?",
            "What would a balanced timetable look like for a learner who has school, chores, study, rest and family responsibilities?",
        ],
        "assignment": (
            "Try a realistic plan for three days. Record what was realistic, what got "
            "in the way and one change for next week. Submit a general summary without "
            "sharing your private schedule or family details."
        ),
    },
    {
        "week": 11,
        "reference": "Proverbs 13:20",
        "focus": "Healthy relationships, trust, conflict, boundaries and warning signs",
        "objectives": [
            "Identify behaviours that build trust and those that damage it.",
            "Practise listening, apology, disagreement and repair.",
            "Recognise controlling, coercive or unsafe friendship patterns.",
            "Set boundaries and seek help when a relationship causes harm.",
        ],
        "lesson": (
            "A healthy friendship does not require constant agreement or being "
            "available every minute. It includes respect, honesty, kindness and room "
            "for different interests and other relationships. Trust grows when people "
            "keep reasonable promises, respect boundaries and handle private "
            "information carefully.\n\n"
            "Disagreement is normal; cruelty is not. A respectful repair can describe "
            "what happened without insults, explain its effect and make a request. "
            "Repeated humiliation, controlling who someone may talk to, demanding "
            "passwords, threats or pressure are warning signs that a friendship may "
            "be unsafe.\n\n"
            "Ordinary private information should be treated with care, but secrecy "
            "has limits when someone may be harmed. If a friend says she is being "
            "harmed, respond with care and seek help from a trusted adult rather "
            "than promising to keep danger secret."
        ),
        "questions": [
            "What could you do if a friend shares a private story you told her in confidence?",
            "How might you handle a disagreement with a friend without insulting her or involving the whole group?",
            "What should you do if a friend says you must stop talking to everyone else to prove that you care about her?",
            "How could you support a friend who is being excluded or mocked by a group?",
            "If a friend tells you she is being harmed and begs you not to tell anyone, how can you respond with care and safety?",
        ],
        "assignment": (
            "Choose one friendship-building action and one boundary you want to "
            "practise. Reflect on how you contribute to trust and what you need from "
            "others. Do not include another person’s name or private story."
        ),
    },
    {
        "week": 12,
        "reference": "Matthew 5:14",
        "focus": "Integration, leadership, service, personal commitments and continued growth",
        "objectives": [
            "Review and connect learning from the 12-week programme.",
            "Describe personal growth and identify skills still needing practice.",
            "Create a realistic plan for continuing growth and seeking support.",
            "Explain how to influence a community through safe, respectful actions.",
        ],
        "lesson": (
            "Growth is not a test of whether someone has become perfect. It may look "
            "like noticing an emotion earlier, asking for help, setting a boundary or "
            "trying again after a setback. Identity supports boundaries; emotional "
            "awareness can support safer decisions; goals can grow through "
            "responsibility and supportive friendships.\n\n"
            "Matthew 5:14–16 can invite reflection on contributing through kindness, "
            "honesty, courage, fairness, learning and service. Being a light does not "
            "mean hiding sadness, mistakes or a need for help. Leadership is not only "
            "a title or microphone: it can include listening, sharing tasks fairly "
            "and taking responsibility.\n\n"
            "A continuing growth plan can include a strength to build, a skill to "
            "practise, a habit to change, a relationship to nurture and a support "
            "person to contact. The end of a programme does not mean support must end; "
            "learning continues through practice, relationships and asking for help."
        ),
        "questions": [
            "What could you do if you notice a new girl sitting alone and you want to help her feel included without embarrassing her?",
            "How might you use what you learned about boundaries if a friend pressures you to keep an unsafe secret?",
            "What is one way to lead positively in your school or community without holding an official title?",
            "If you find that a goal you made during the programme is no longer realistic, how can you adapt it without giving up on growth?",
            "What would you say to a girl who thinks being an “Almasi girl” means she must never feel sad, make mistakes or ask for help?",
        ],
        "assignment": (
            "Review your growth plan after one month. Note what changed, what was "
            "difficult and what support is needed. For module completion now, submit "
            "a short plan for when you will review it; do not include private names "
            "or details."
        ),
    },
)


def upgrade() -> None:
    with op.batch_alter_table("learning_modules") as batch_op:
        batch_op.add_column(
            sa.Column("reflection_prompts", sa.JSON(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(
            sa.Column("reviewed_by_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_learning_modules_reviewed_by",
            "users",
            ["reviewed_by_id"],
            ["id"],
            ondelete="SET NULL",
        )
    op.create_index(
        "ix_learning_modules_reviewed_by_id",
        "learning_modules",
        ["reviewed_by_id"],
        unique=False,
    )
    with op.batch_alter_table("module_questions") as batch_op:
        batch_op.add_column(
            sa.Column(
                "kind",
                sa.String(length=20),
                nullable=False,
                server_default="case_study",
            )
        )
        batch_op.create_check_constraint(
            "ck_question_kind",
            "kind IN ('case_study', 'assignment', 'quiz')",
        )
        batch_op.create_check_constraint("ck_question_position", "position > 0")
    with op.batch_alter_table("learner_module_submissions") as batch_op:
        batch_op.alter_column(
            "submitted_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=True,
        )

    module_table = sa.table(
        "learning_modules",
        sa.column("week_number", sa.Integer()),
        sa.column("content_markdown", sa.Text()),
        sa.column("learning_objectives", sa.JSON()),
        sa.column("reflection_prompts", sa.JSON()),
    )
    question_table = sa.table(
        "module_questions",
        sa.column("module_id", sa.Integer()),
        sa.column("position", sa.Integer()),
        sa.column("kind", sa.String(20)),
        sa.column("prompt", sa.String(2000)),
    )
    bind = op.get_bind()
    for module in MODULE_CONTENT:
        module_id = bind.execute(
            sa.text(
                "SELECT id FROM learning_modules WHERE week_number = :week"
            ),
            {"week": module["week"]},
        ).scalar_one()
        bind.execute(
            module_table.update()
            .where(module_table.c.week_number == module["week"])
            .values(
                content_markdown=(
                    f"Bible reference: {module['reference']}\n"
                    f"Focus: {module['focus']}\n\n{module['lesson']}"
                ),
                learning_objectives=module["objectives"],
                reflection_prompts=REFLECTION_PROMPTS,
            )
        )
        questions = [
            {
                "module_id": module_id,
                "position": index,
                "kind": "case_study",
                "prompt": prompt,
            }
            for index, prompt in enumerate(module["questions"], start=1)
        ]
        questions.append(
            {
                "module_id": module_id,
                "position": len(questions) + 1,
                "kind": "assignment",
                "prompt": module["assignment"],
            }
        )
        op.bulk_insert(question_table, questions)
    with op.batch_alter_table("learning_modules") as batch_op:
        batch_op.alter_column(
            "reflection_prompts",
            existing_type=sa.JSON(),
            nullable=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    non_draft_modules = bind.execute(
        sa.text(
            "SELECT COUNT(*) FROM learning_modules "
            "WHERE is_published = 1 OR reviewed_at IS NOT NULL"
        )
    ).scalar_one()
    incomplete_submissions = bind.execute(
        sa.text(
            "SELECT COUNT(*) FROM learner_module_submissions "
            "WHERE submitted_at IS NULL"
        )
    ).scalar_one()
    if non_draft_modules or incomplete_submissions:
        raise RuntimeError(
            "Cannot downgrade populated curriculum after review, publication, or learner answer drafts."
        )
    for module in MODULE_CONTENT:
        module_id = bind.execute(
            sa.text(
                "SELECT id FROM learning_modules WHERE week_number = :week"
            ),
            {"week": module["week"]},
        ).scalar_one()
        for prompt in module["questions"] + [module["assignment"]]:
            bind.execute(
                sa.text(
                    "DELETE FROM module_questions "
                    "WHERE module_id = :module_id AND prompt = :prompt"
                ),
                {"module_id": module_id, "prompt": prompt},
            )
    op.execute(
        sa.text(
            "UPDATE learning_modules SET learning_objectives = '[]', "
            "content_markdown = '' WHERE week_number BETWEEN 1 AND 12"
        )
    )
    op.drop_index("ix_learning_modules_reviewed_by_id", table_name="learning_modules")
    with op.batch_alter_table("learning_modules") as batch_op:
        batch_op.drop_constraint(
            "fk_learning_modules_reviewed_by", type_="foreignkey"
        )
        batch_op.drop_column("reviewed_by_id")
        batch_op.drop_column("reviewed_at")
        batch_op.drop_column("reflection_prompts")
    with op.batch_alter_table("learner_module_submissions") as batch_op:
        batch_op.alter_column(
            "submitted_at",
            existing_type=sa.DateTime(timezone=True),
            nullable=False,
        )
    with op.batch_alter_table("module_questions") as batch_op:
        batch_op.drop_constraint("ck_question_position", type_="check")
        batch_op.drop_constraint("ck_question_kind", type_="check")
        batch_op.drop_column("kind")
