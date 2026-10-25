import { useEffect, useState } from "react";
import { ApiError, apiFetch } from "../lib/api";

type Role = "learner" | "facilitator" | "supervisor" | "administrator";
type UserRecord = {
  id: number;
  name: string;
  email: string;
  role: Role;
  is_active: boolean;
};
type Group = {
  id: number;
  name: string;
  description: string;
  is_active: boolean;
  learner_count: number;
  facilitator_names: string[];
};
type Module = {
  id: number;
  week_number: number;
  title: string;
  is_published: boolean;
};
type GroupAssignment = {
  group_id: number;
  facilitator_ids: number[];
  learner_ids: number[];
};
type Dashboard = {
  users: UserRecord[];
  groups: Group[];
  modules: Module[];
};

const roles: Role[] = ["learner", "facilitator", "supervisor", "administrator"];

function errorMessage(error: unknown): string {
  if (error instanceof ApiError && error.status === 409) {
    return "That account or group change conflicts with programme rules.";
  }
  if (error instanceof ApiError && error.status === 403) {
    return "Administrator access is required for this action.";
  }
  return "The administration service is unavailable. Your change was not saved.";
}

function selectedIds(select: HTMLSelectElement): number[] {
  return Array.from(select.selectedOptions, (option) => Number(option.value));
}

export default function AdministratorDashboard() {
  const [data, setData] = useState<Dashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [retry, setRetry] = useState(0);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [groupName, setGroupName] = useState("");
  const [groupDescription, setGroupDescription] = useState("");
  const [selectedGroupId, setSelectedGroupId] = useState("");
  const [groupAssignments, setGroupAssignments] = useState<GroupAssignment | null>(null);
  const [facilitatorIds, setFacilitatorIds] = useState<number[]>([]);
  const [learnerIds, setLearnerIds] = useState<number[]>([]);
  const [sessionGroupId, setSessionGroupId] = useState("");
  const [sessionModuleId, setSessionModuleId] = useState("");
  const [sessionTitle, setSessionTitle] = useState("");
  const [sessionPlan, setSessionPlan] = useState("");
  const [sessionStart, setSessionStart] = useState("");
  const [sessionEnd, setSessionEnd] = useState("");
  const [roleDrafts, setRoleDrafts] = useState<Record<number, Role>>({});

  useEffect(() => {
    let active = true;
    setLoading(true);
    Promise.all([
      apiFetch("administrator/users").then((response) => response.json() as Promise<UserRecord[]>),
      apiFetch("administrator/groups").then((response) => response.json() as Promise<Group[]>),
      apiFetch("supervisor/modules").then((response) => response.json() as Promise<Module[]>),
    ])
      .then(([users, groups, modules]) => {
        if (!active) return;
        setData({ users, groups, modules });
        setRoleDrafts(Object.fromEntries(users.map((user) => [user.id, user.role])));
        setError("");
        if (!sessionModuleId && modules.length) setSessionModuleId(String(modules[0].id));
        if (!sessionGroupId && groups.length) setSessionGroupId(String(groups[0].id));
      })
      .catch((requestError: unknown) => {
        if (active) setError(errorMessage(requestError));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [retry]);

  useEffect(() => {
    let active = true;
    if (!selectedGroupId) {
      setGroupAssignments(null);
      return;
    }
    apiFetch(`administrator/groups/${selectedGroupId}/assignments`)
      .then((response) => response.json() as Promise<GroupAssignment>)
      .then((assignments) => {
        if (!active) return;
        setGroupAssignments(assignments);
        setFacilitatorIds(assignments.facilitator_ids);
        setLearnerIds(assignments.learner_ids);
      })
      .catch((requestError: unknown) => {
        if (active) setError(errorMessage(requestError));
      });
    return () => {
      active = false;
    };
  }, [selectedGroupId]);

  async function reload(message: string) {
    setNotice(message);
    setRetry((attempt) => attempt + 1);
  }

  async function createGroup() {
    setBusy(true);
    setError("");
    try {
      const response = await apiFetch("administrator/groups", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: groupName, description: groupDescription }),
      });
      const group = (await response.json()) as Group;
      setGroupName("");
      setGroupDescription("");
      setSelectedGroupId(String(group.id));
      await reload(`Group “${group.name}” was created.`);
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setBusy(false);
    }
  }

  async function saveAssignments() {
    if (!selectedGroupId || !groupAssignments) return;
    setBusy(true);
    setError("");
    try {
      await apiFetch(`administrator/groups/${selectedGroupId}/assignments`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          facilitator_ids: facilitatorIds,
          learner_ids: learnerIds,
        }),
      });
      await reload("Group membership and facilitator assignments were saved.");
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setBusy(false);
    }
  }

  async function createSession() {
    setBusy(true);
    setError("");
    try {
      await apiFetch("administrator/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          group_id: Number(sessionGroupId),
          module_id: Number(sessionModuleId),
          title: sessionTitle,
          facilitator_plan: sessionPlan,
          starts_at: new Date(sessionStart).toISOString(),
          ends_at: new Date(sessionEnd).toISOString(),
        }),
      });
      setSessionTitle("");
      setSessionPlan("");
      await reload("Session and facilitator-only plan were saved.");
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setBusy(false);
    }
  }

  async function updateUser(user: UserRecord) {
    const role = roleDrafts[user.id] ?? user.role;
    const isActive = (document.getElementById(`active-${user.id}`) as HTMLInputElement).checked;
    setBusy(true);
    setError("");
    try {
      await apiFetch(`administrator/users/${user.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role, is_active: isActive }),
      });
      await reload(`${user.name}’s account settings were saved.`);
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setBusy(false);
    }
  }

  async function setGroupActive(group: Group, isActive: boolean) {
    setBusy(true);
    setError("");
    try {
      await apiFetch(`administrator/groups/${group.id}`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ is_active: isActive }),
      });
      await reload(`Group ${isActive ? "activated" : "deactivated"}.`);
    } catch (requestError) {
      setError(errorMessage(requestError));
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <section className="workspace-intro">
        <span className="eyebrow">ALMASI administrator space</span>
        <h2>Manage accounts and programme setup.</h2>
        <p>Account administration does not grant access to private learner reflections.</p>
      </section>
      {error && <p className="workspace-alert" role="alert">{error}</p>}
      {notice && <p className="learner-completion" role="status">{notice}</p>}
      {loading ? (
        <p className="workspace-message" role="status">Loading accounts and groups…</p>
      ) : error && !data ? (
        <section className="workspace-message" role="alert">
          <h1>We couldn’t load administration tools.</h1>
          <p>{error}</p>
          <button className="button button--primary" onClick={() => setRetry((value) => value + 1)} type="button">Try again</button>
        </section>
      ) : data ? (
        <>
          <section className="workspace-card">
            <span className="workspace-kicker">ACCOUNT ADMINISTRATION</span>
            <h3>Accounts and roles</h3>
            <p>Public sign-up creates learner accounts. Assign staff roles only to verified accounts.</p>
            {data.users.map((user) => (
              <article className="supervisor-curriculum__module" key={user.id}>
                <h4>{user.name} · {user.email}</h4>
                <div className="workspace-header__actions">
                  <label className="learner-question">
                    <span>Role</span>
                    <select value={roleDrafts[user.id] ?? user.role} onChange={(event) => setRoleDrafts((current) => ({ ...current, [user.id]: event.target.value as Role }))}>
                      {roles.map((role) => <option key={role} value={role}>{role}</option>)}
                    </select>
                  </label>
                  <label>
                    <input defaultChecked={user.is_active} id={`active-${user.id}`} type="checkbox" /> Active
                  </label>
                  <button className="button button--primary" disabled={busy} onClick={() => void updateUser(user)} type="button">Save account</button>
                </div>
              </article>
            ))}
          </section>

          <section className="workspace-card">
            <span className="workspace-kicker">GROUPS</span>
            <h3>Create and assign mentorship groups</h3>
            <label className="learner-question">
              <span>Group name</span>
              <input maxLength={120} onChange={(event) => setGroupName(event.target.value)} value={groupName} />
            </label>
            <label className="learner-question">
              <span>Description</span>
              <textarea maxLength={2000} onChange={(event) => setGroupDescription(event.target.value)} rows={2} value={groupDescription} />
            </label>
            <button className="button button--primary" disabled={busy || !groupName.trim()} onClick={() => void createGroup()} type="button">Create group</button>
            <label className="learner-question">
              <span>Group</span>
              <select onChange={(event) => setSelectedGroupId(event.target.value)} value={selectedGroupId}>
                <option value="">Choose a group</option>
                {data.groups.map((group) => <option key={group.id} value={group.id}>{group.name} {group.is_active ? "" : "(inactive)"}</option>)}
              </select>
            </label>
            {selectedGroupId && groupAssignments && (
              <>
                <label className="learner-question">
                  <span>Assigned facilitators</span>
                  <select
                    multiple
                    onChange={(event) => setFacilitatorIds(selectedIds(event.currentTarget))}
                    value={facilitatorIds.map(String)}
                  >
                    {data.users.filter((person) => person.role === "facilitator" && person.is_active).map((person) => (
                      <option key={person.id} value={person.id}>{person.name}</option>
                    ))}
                  </select>
                </label>
                <label className="learner-question">
                  <span>Group learners</span>
                  <select
                    multiple
                    onChange={(event) => setLearnerIds(selectedIds(event.currentTarget))}
                    value={learnerIds.map(String)}
                  >
                    {data.users.filter((person) => person.role === "learner" && person.is_active).map((person) => (
                      <option key={person.id} value={person.id}>{person.name}</option>
                    ))}
                  </select>
                </label>
                <button className="button button--primary" disabled={busy} onClick={() => void saveAssignments()} type="button">Save group assignments</button>
              </>
            )}
            {data.groups.map((group) => (
              <p key={group.id}>
                {group.name} · {group.learner_count} learners · {group.facilitator_names.join(", ") || "No facilitators"} ·{" "}
                <button className="auth-text-button" disabled={busy} onClick={() => void setGroupActive(group, !group.is_active)} type="button">
                  {group.is_active ? "Deactivate" : "Activate"}
                </button>
              </p>
            ))}
          </section>

          <section className="workspace-card">
            <span className="workspace-kicker">SESSION SETUP</span>
            <h3>Schedule a session and author its facilitator plan</h3>
            <p>Plan content is visible to assigned facilitators, not to learners.</p>
            <label className="learner-question">
              <span>Group</span>
              <select onChange={(event) => setSessionGroupId(event.target.value)} value={sessionGroupId}>
                {data.groups.filter((group) => group.is_active).map((group) => <option key={group.id} value={group.id}>{group.name}</option>)}
              </select>
            </label>
            <label className="learner-question">
              <span>Curriculum module</span>
              <select onChange={(event) => setSessionModuleId(event.target.value)} value={sessionModuleId}>
                {data.modules.map((module) => <option key={module.id} value={module.id}>Week {module.week_number}: {module.title}</option>)}
              </select>
            </label>
            <label className="learner-question">
              <span>Session title</span>
              <input maxLength={200} onChange={(event) => setSessionTitle(event.target.value)} value={sessionTitle} />
            </label>
            <label className="learner-question">
              <span>Facilitator-only plan</span>
              <textarea maxLength={20_000} onChange={(event) => setSessionPlan(event.target.value)} rows={4} value={sessionPlan} />
            </label>
            <div className="workspace-header__actions">
              <label className="learner-question"><span>Starts</span><input onChange={(event) => setSessionStart(event.target.value)} type="datetime-local" value={sessionStart} /></label>
              <label className="learner-question"><span>Ends</span><input onChange={(event) => setSessionEnd(event.target.value)} type="datetime-local" value={sessionEnd} /></label>
            </div>
            <button className="button button--primary" disabled={busy || !sessionGroupId || !sessionModuleId || !sessionTitle.trim() || !sessionStart || !sessionEnd} onClick={() => void createSession()} type="button">Schedule session</button>
          </section>

          <section className="workspace-card">
            <span className="workspace-kicker">CURRICULUM</span>
            <h3>Review and publish learner modules</h3>
            <p>Administrators can also use supervisor curriculum review controls.</p>
          </section>
        </>
      ) : null}
    </>
  );
}
