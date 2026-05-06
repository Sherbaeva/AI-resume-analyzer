/**
 * ATS API Client — v2 (with Auth + RBAC)
 *
 * Usage:
 *   const api = new AtsClient("http://localhost:8000");
 *   const { access_token } = await api.login("admin@ats-system.com", "admin1234");
 *   api.setToken(access_token);
 *   const me = await api.me();
 */
import type {
    LoginRequest, TokenResponse, UserMe,
    UserCreate, UserUpdate, UserOut,
    PermissionOut, PermissionsSetRequest,
    JobDescriptionCreate, JobDescriptionResponse,
    ResumeResponse,
    AnalysisCreate, AnalysisResponse,
    SkillCreate, SkillUpdate, SkillOut,
    AuditLogOut,
    HealthResponse,
} from "./types";

export class AtsApiError extends Error {
    constructor(public status: number, public detail: unknown) {
        super(`ATS API error ${status}: ${JSON.stringify(detail)}`);
        this.name = "AtsApiError";
    }
}

export class AtsClient {
    private baseUrl: string;
    private token: string | null = null;

    constructor(baseUrl: string = "http://localhost:8000", token?: string) {
        this.baseUrl = baseUrl.replace(/\/$/, "");
        if (token) this.token = token;
    }

    setToken(token: string | null) {
        this.token = token;
    }

    hasToken(): boolean {
        return this.token !== null;
    }

    private authHeader(): Record<string, string> {
        if (!this.token) throw new Error("Not authenticated. Call login() first.");
        return { Authorization: `Bearer ${this.token}` };
    }

    private async request<T>(
        method: string,
        path: string,
        opts: { body?: unknown; formData?: FormData; query?: Record<string, unknown>; auth?: boolean } = {}
    ): Promise<T> {
        const url = new URL(`${this.baseUrl}${path}`);
        if (opts.query) {
            Object.entries(opts.query).forEach(([k, v]) => {
                if (v !== undefined && v !== null) url.searchParams.set(k, String(v));
            });
        }

        const headers: Record<string, string> = opts.auth !== false ? this.authHeader() : {};
        let body: BodyInit | undefined;

        if (opts.formData) {
            body = opts.formData;
        } else if (opts.body !== undefined) {
            headers["Content-Type"] = "application/json";
            body = JSON.stringify(opts.body);
        }

        const res = await fetch(url.toString(), { method, headers, body });

        if (res.status === 204) return undefined as T;
        const json = await res.json();
        if (!res.ok) throw new AtsApiError(res.status, json.detail ?? json);
        return json as T;
    }

    // ─── Auth ───────────────────────────────────────────────────────────────

    async login(email: string, password: string): Promise<TokenResponse> {
        const data = await this.request<TokenResponse>("POST", "/auth/login", {
            body: { email, password } satisfies LoginRequest,
            auth: false,
        });
        this.token = data.access_token;
        return data;
    }

    async me(): Promise<UserMe> {
        return this.request<UserMe>("GET", "/auth/me");
    }

    async logout(): Promise<void> {
        await this.request<void>("POST", "/auth/logout");
        this.token = null;
    }

    // ─── Users (admin only) ─────────────────────────────────────────────────

    async createUser(data: UserCreate): Promise<UserOut> {
        return this.request<UserOut>("POST", "/users", { body: data });
    }

    async listUsers(skip = 0, limit = 100): Promise<UserOut[]> {
        return this.request<UserOut[]>("GET", "/users", { query: { skip, limit } });
    }

    async getUser(userId: number): Promise<UserOut> {
        return this.request<UserOut>("GET", `/users/${userId}`);
    }

    async updateUser(userId: number, data: UserUpdate): Promise<UserOut> {
        return this.request<UserOut>("PATCH", `/users/${userId}`, { body: data });
    }

    async deactivateUser(userId: number): Promise<void> {
        return this.request<void>("DELETE", `/users/${userId}`);
    }

    async getUserPermissions(userId: number): Promise<PermissionOut[]> {
        return this.request<PermissionOut[]>("GET", `/users/${userId}/permissions`);
    }

    async setUserPermissions(userId: number, codes: string[]): Promise<unknown> {
        return this.request("PUT", `/users/${userId}/permissions`, {
            body: { permission_codes: codes } satisfies PermissionsSetRequest,
        });
    }

    // ─── Job Descriptions ───────────────────────────────────────────────────

    async createJobDescription(data: JobDescriptionCreate): Promise<JobDescriptionResponse> {
        return this.request<JobDescriptionResponse>("POST", "/job-descriptions", { body: data });
    }

    async getJobDescription(jdId: number): Promise<JobDescriptionResponse> {
        return this.request<JobDescriptionResponse>("GET", `/job-descriptions/${jdId}`);
    }

    // ─── Resumes ────────────────────────────────────────────────────────────

    async uploadResume(file: File): Promise<ResumeResponse> {
        const fd = new FormData();
        fd.append("file", file);
        return this.request<ResumeResponse>("POST", "/resumes", { formData: fd });
    }

    async getResume(resumeId: number): Promise<ResumeResponse> {
        return this.request<ResumeResponse>("GET", `/resumes/${resumeId}`);
    }

    async deleteResume(resumeId: number): Promise<ResumeResponse> {
        return this.request<ResumeResponse>("DELETE", `/resumes/${resumeId}`);
    }

    // ─── Analyses ───────────────────────────────────────────────────────────

    async createAnalysis(data: AnalysisCreate): Promise<AnalysisResponse> {
        return this.request<AnalysisResponse>("POST", "/analyses", { body: data });
    }

    async getAnalysis(analysisId: number): Promise<AnalysisResponse> {
        return this.request<AnalysisResponse>("GET", `/analyses/${analysisId}`);
    }

    async getResults(jobDescriptionId: number): Promise<AnalysisResponse[]> {
        return this.request<AnalysisResponse[]>("GET", "/results", {
            query: { job_description_id: jobDescriptionId },
        });
    }

    // ─── Skill Taxonomy ─────────────────────────────────────────────────────

    async listSkills(opts?: {
        q?: string;
        category?: string;
        is_active?: boolean;
        skip?: number;
        limit?: number;
    }): Promise<SkillOut[]> {
        return this.request<SkillOut[]>("GET", "/taxonomy/skills", { query: opts });
    }

    async getSkill(skillId: number): Promise<SkillOut> {
        return this.request<SkillOut>("GET", `/taxonomy/skills/${skillId}`);
    }

    async createSkill(data: SkillCreate): Promise<SkillOut> {
        return this.request<SkillOut>("POST", "/taxonomy/skills", { body: data });
    }

    async updateSkill(skillId: number, data: SkillUpdate): Promise<SkillOut> {
        return this.request<SkillOut>("PATCH", `/taxonomy/skills/${skillId}`, { body: data });
    }

    async deleteSkill(skillId: number): Promise<void> {
        return this.request<void>("DELETE", `/taxonomy/skills/${skillId}`);
    }

    // ─── Audit Logs ─────────────────────────────────────────────────────────

    async getAuditLogs(opts?: {
        action?: string;
        entity_type?: string;
        actor_user_id?: number;
        date_from?: string;
        date_to?: string;
        limit?: number;
        offset?: number;
    }): Promise<AuditLogOut[]> {
        return this.request<AuditLogOut[]>("GET", "/logs/audit", { query: opts });
    }

    // ─── Health ─────────────────────────────────────────────────────────────

    async health(): Promise<HealthResponse> {
        return this.request<HealthResponse>("GET", "/health", { auth: false });
    }
}

// Singleton helper — stores token in localStorage
export function createClient(baseUrl?: string): AtsClient {
    const token = typeof window !== "undefined"
        ? localStorage.getItem("ats_token") ?? undefined
        : undefined;
    return new AtsClient(baseUrl, token);
}

export function persistToken(token: string) {
    if (typeof window !== "undefined") localStorage.setItem("ats_token", token);
}

export function clearToken() {
    if (typeof window !== "undefined") localStorage.removeItem("ats_token");
}
