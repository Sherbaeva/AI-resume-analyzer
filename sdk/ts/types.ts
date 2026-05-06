// ─── Auth ──────────────────────────────────────────────────────────────────
export interface LoginRequest {
    email: string;
    password: string;
}

export interface TokenResponse {
    access_token: string;
    token_type: string;
    expires_in: number; // seconds
}

export interface UserMe {
    id: number;
    email: string;
    role: "admin" | "hr";
    is_active: boolean;
    permissions: string[];
}

// ─── Users (admin only) ────────────────────────────────────────────────────
export interface UserCreate {
    email: string;
    password: string;
    role?: "admin" | "hr";
}

export interface UserUpdate {
    role?: "admin" | "hr";
    is_active?: boolean;
    password?: string;
}

export interface UserOut {
    id: number;
    email: string;
    role: "admin" | "hr";
    is_active: boolean;
    created_at: string;
    updated_at: string;
    last_login_at: string | null;
    permissions: string[];
}

export interface PermissionOut {
    id: number;
    code: string;
    description: string;
}

export interface PermissionsSetRequest {
    permission_codes: string[];
}

// ─── Job Descriptions ──────────────────────────────────────────────────────
export interface JobDescriptionCreate {
    title: string;
    raw_text: string;
}

export interface JobDescriptionResponse {
    id: number;
    title: string;
    raw_text: string;
    created_at: string;
}

// ─── Resumes ───────────────────────────────────────────────────────────────
export interface ResumeResponse {
    id: number;
    filename: string;
    file_path: string;
    file_hash: string;
    file_size: number;
    content_type: string;
    uploaded_at: string;
    deleted_at: string | null;
}

// ─── Analyses ──────────────────────────────────────────────────────────────
export interface AnalysisCreate {
    resume_id: number;
    job_description_id: number;
}

export interface AnalysisResponse {
    id: number;
    resume_id: number;
    job_description_id: number;
    status: "queued" | "running" | "done" | "failed";
    score: number | null;
    matched_skills_json: string | null;
    missing_skills_json: string | null;
    explanations_json: string | null;
    error_message: string | null;
    scoring_version: string;
    parser_version: string;
    created_at: string;
    started_at: string | null;
    finished_at: string | null;
}

// ─── Taxonomy ──────────────────────────────────────────────────────────────
export interface SkillCreate {
    name: string;
    category?: string;
    aliases?: string[];
    is_active?: boolean;
}

export interface SkillUpdate {
    name?: string;
    category?: string;
    aliases?: string[];
    is_active?: boolean;
}

export interface SkillOut {
    id: number;
    name: string;
    category: string | null;
    aliases: string[];
    is_active: boolean;
    created_by_id: number | null;
    updated_by_id: number | null;
    created_at: string;
    updated_at: string;
}

// ─── Audit Logs ────────────────────────────────────────────────────────────
export interface AuditLogOut {
    id: number;
    actor_user_id: number | null;
    action: string;
    entity_type: string;
    entity_id: number | null;
    meta_json: Record<string, unknown> | null;
    ip: string | null;
    user_agent: string | null;
    created_at: string;
}

// ─── Misc ──────────────────────────────────────────────────────────────────
export interface HealthResponse {
    status: string;
    service: string;
}

export interface ApiError {
    detail: string | { loc: string[]; msg: string; type: string }[];
}

/** Known RBAC permission codes */
export type PermissionCode =
    | "users.manage"
    | "resumes.read"
    | "resumes.write"
    | "resumes.delete"
    | "taxonomy.manage"
    | "taxonomy.read"
    | "logs.view"
    | "jd.write"
    | "jd.read"
    | "analysis.write"
    | "results.read";
